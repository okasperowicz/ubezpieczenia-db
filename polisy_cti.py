# -*- coding: utf-8 -*-

import sqlite3

from datetime import date
from datetime import timedelta

#
# Ścieżka połączenia z bazą danych
#
db_path = 'ubezpieczenia.db'

#
# Wyjątek używany w repozytorium
#
class UbezpieczeniaDbException(Exception):
    def __init__(self, message, *errors):
        Exception.__init__(self, message)
        self.errors = errors


#
# Klasy odpowiadajce danym z tabel
#

# Model polisy
class Polisa():

    def __init__(self, id, klient, dataPoczatku, terytorium, osobodni, ryzyka=[], dataZawarcia=date.today(), okres=365):
        self.id = id
        self.numer = "CTI/" + str(self.id) + "/" + str(dataZawarcia.year)
        self.klient = klient
        self.dataZawarcia = dataZawarcia
        self.dataPoczatku = dataPoczatku
        if okres > 0 :
            d = timedelta(days=okres)
            self.dataKonca = dataPoczatku + d
        self.terytorium = terytorium
        self.osobodni = osobodni
        self.ryzyka = ryzyka
        self.skladka = sum([osobodni * ryzyko.skladkaOsDz for ryzyko in ryzyka])

    def __repr__(self):
        return """<Polisa(id='%s', numer='%s', klient='%s', dataZawarcia='%s', dataPoczatku='%s', dataKonca='%s',
        terytorium='%s', osobodni='%s', skladka='%s', ryzyka='%s')>""" % (
                str(self.id), self.numer, self.klient, str(self.dataZawarcia), str(self.dataPoczatku), str(self.dataKonca),
                self.terytorium, str(self.osobodni), str(self.skladka), str(self.ryzyka)
                )

#Model ryzyka na polisie
class Ryzyko():

    def __init__(self, nazwa, skladkaOsDz):
        self.nazwa = nazwa
        self.skladkaOsDz = skladkaOsDz

    def __repr__(self):
        return "<Ryzyko(nazwa='%s', skladkaOsDz='%s')>" % (
                    self.nazwa, str(self.skladkaOsDz)
                )


#
# Klasa bazowa repozytorium
#
class Repozytorium():
    def __init__(self):
        try:
            self.conn = self.get_connection()
        except Exception as e:
            raise UbezpieczeniaDbException('GET CONNECTION:', *e.args)
        self._complete = False

    # wejście do with ... as ...
    def __enter__(self):
        return self

    # wyjście z with ... as ...
    def __exit__(self, type_, value, traceback):
        self.close()

    def complete(self):
        self._complete = True

    def get_connection(self):
        return sqlite3.connect(db_path)

    def close(self):
        if self.conn:
            try:
                if self._complete:
                    self.conn.commit()
                else:
                    self.conn.rollback()
            except Exception as e:
                raise UbezpieczeniaDbException(*e.args)
            finally:
                try:
                    self.conn.close()
                except Exception as e:
                    raise UbezpieczeniaDbException(*e.args)

#
# repozytorium ubezpieczen CTI
#
class RepozytoriumUbezpieczen(Repozytorium):

    # Metoda dodaje pojedynczą polisę do bazy danych, wraz z zawartymi na niej ryzykami.
    def add(self, polisa):

        try:
            c = self.conn.cursor()
            # zapisz polisę
            c.execute('''INSERT INTO Polisy (id, numer, nazwa_klienta, data_zawarcia, data_poczatku, data_konca,
                zakres_terytorialny, ilosc_osobodni, kwota_skladki) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (polisa.id, polisa.numer, polisa.klient, str(polisa.dataZawarcia), str(polisa.dataPoczatku), str(polisa.dataKonca),
                 polisa.terytorium, polisa.osobodni, polisa.skladka)
                    )

            # zapisz ryzyka z polisy
            if polisa.ryzyka:
                for ryzyko in polisa.ryzyka:
                    try:
                        c.execute('INSERT INTO Ryzyka (nazwa, skladka_osobodzien, id_polisy) VALUES(?,?,?)',
                                        (ryzyko.nazwa, ryzyko.skladkaOsDz, polisa.id)
                                )
                    except Exception as e:
                        # błąd dodawania ryzyka - wypisz ryzyko które się nie dodało i błąd jaki wystąpił
                        raise UbezpieczeniaDbException('Błąd dodawania do bazy ryzyka: %s, z polisy: %s' %
                                                        (str(ryzyko), str(polisa.id))
                                                    )
        except Exception as e:
            # bład dodawania polisy - wypisz polisę dla jakiej błąd wystąpił
            raise UbezpieczeniaDbException('Błąd dodawania do bazy polisy: %s' % str(polisa))


    # Metoda usuwa pojedynczą polisę z bazy danych, wraz z zawartymi na niej ryzykami.
    def delete(self, idPolisy):
        try:
            c = self.conn.cursor()
            # usuń ryzyka zawarte na polisie
            c.execute('DELETE FROM Ryzyka WHERE id_polisy=?', (idPolisy,))
            # usuń polisę
            c.execute('DELETE FROM Polisy WHERE id=?', (idPolisy,))

        except Exception as e:
            # Bład usuwania polisy - wypisz id
            raise UbezpieczeniaDbException('Błąd usuwania z bazy polisy o id %s' % str(idPolisy))


    def utworzPolisyZWiersza(self, polisy_rows):
        try:
            if polisy_rows == None:
                return None

            polisy_list = []
            for polisa_row in polisy_rows:
                polisa = Polisa(polisa_row[0], polisa_row[2], polisa_row[4], polisa_row[6], polisa_row[7], okres=0)
                polisa.numer = polisa_row[1]
                polisa.dataZawarcia = polisa_row[3]
                polisa.dataKonca = polisa_row[5]
                polisa.skladka = polisa_row[8]

                c = self.conn.cursor()
                c.execute("SELECT * FROM Ryzyka WHERE id_polisy=? order by nazwa", (polisa_row[0],))
                ryzyka_rows = c.fetchall()
                ryzyka_list = []
                for ryzyko_row in ryzyka_rows:
                    ryzyko = Ryzyko(nazwa=ryzyko_row[0], skladkaOsDz=ryzyko_row[1])
                    ryzyka_list.append(ryzyko)
                polisa.ryzyka=ryzyka_list
                polisy_list.append(polisa)
        except Exception as e:
            raise UbezpieczeniaDbException('Błąd tworzenia polisy z wiersza  - id polisy: %s' % str(polisa_row[0]))
        return polisy_list

    # Metoda pobiera polisę o określonym id
    def getById(self, idPolisy):

        try:
            c = self.conn.cursor()
            c.execute("SELECT * FROM Polisy WHERE id=?", (idPolisy,))
            polisy_rows = c.fetchall()
            polisy_list = self.utworzPolisyZWiersza(polisy_rows)

        except Exception as e:
            # Błąd pobierania polisy - wypisz dla jakiego id wystąpił
            raise UbezpieczeniaDbException('Błąd pobierania polisy po id  - id polisy: %s' % str(idPolisy))
        return polisy_list

    # Metoda pobiera wszystkie polisy danego klienta
    def getByKlient(self, nazwaKlienta):

        try:
            c = self.conn.cursor()
            c.execute("SELECT * FROM Polisy WHERE nazwa_klienta=?", (nazwaKlienta,))
            polisy_rows = c.fetchall()
            polisy_list = self.utworzPolisyZWiersza(polisy_rows)

        except Exception as e:
            # Błąd pobierania polisy - wypisz dla jakiego klienta wystąpił
            raise UbezpieczeniaDbException('Błąd pobierania polisy po nazwie klienta  - klient: %s' % str(nazwaKlienta))
        return polisy_list

    # Metoda pobiera wszystkie polisy danego klienta
    def getByTerytorium(self, terytorium):

        try:
            c = self.conn.cursor()
            c.execute("SELECT * FROM Polisy WHERE zakres_terytorialny=?", (terytorium,))
            polisy_rows = c.fetchall()
            polisy_list = self.utworzPolisyZWiersza(polisy_rows)

        except Exception as e:
            # Błąd pobierania polisy - wypisz dla jakiego terytorium wystąpił
            raise UbezpieczeniaDbException('Błąd pobierania polis wg zakresu terytorialnego  - terytorium: %s' % str(terytorium))
        return polisy_list



    # Metoda uaktualnia pojedynczą polisę w bazie danych, wraz z zawartymi na niej ryzykami.
    def update(self, polisa):

        try:
            # pobierz polisę z bazy
            polisa_oryg = self.getById(polisa.id)
            if polisa_oryg != None:
                # polisa jest w bazie: usuń ją
                self.delete(polisa.id)
            self.add(polisa)

        except Exception as e:
            # błąd uaktualnienia polisy - wypisz polisę
            print(e)
            raise UbezpieczeniaDbException('Błąd uaktualnienia polisy: %s' % str(polisa))



if __name__ == '__main__':
    try:
        # Definicja danych do wypelnienia
        ryzykaKross = [ Ryzyko("Koszty leczenia", 3.50), Ryzyko("NNW", 0.70), Ryzyko("OC", 1.30), Ryzyko("Assistance", 1.50) ]
        ryzykaTuttu = [ Ryzyko("Koszty leczenia", 3.75), Ryzyko("NNW", 1.05), Ryzyko("OC", 1.35), Ryzyko("Assistance", 1.85) ]
        ryzykaPolsat = [ Ryzyko("Koszty leczenia", 2.75), Ryzyko("NNW", 0.55), Ryzyko("OC", 1.00) ]
        ryzykaOstaszewski = [ Ryzyko("Koszty leczenia", 2.50), Ryzyko("NNW", 0.45), Ryzyko("OC", 1.15), Ryzyko("Assistance", 1.25) ]
        ryzykaDnv = [ Ryzyko("Koszty leczenia", 2.60), Ryzyko("NNW", 0.50), Ryzyko("OC", 1.00), Ryzyko("Assistance", 1.30) ]

        nowe_polisy = [
            Polisa(1, "Kross", date(2017, 02, 15), "Swiat", 200, ryzykaKross),
            Polisa(2, "Tuttu", date(2017, 02, 18), "Swiat", 300, ryzykaTuttu),
            Polisa(3, "Polsat", date(2017, 02, 20), "Europa", 100, ryzykaPolsat),
            Polisa(4, "Ostaszewski Spedycja", date(2017, 02, 22), "Europa", 500, ryzykaOstaszewski),
            Polisa(5, "DNV", date(2017, 02, 23), "Europa", 250, ryzykaDnv),
        ]

        ryzykaKross16 = [ Ryzyko("Koszty leczenia", 3.70), Ryzyko("NNW", 0.80), Ryzyko("OC", 1.30), Ryzyko("Assistance", 1.60) ]
        ryzykaPolsat16 = [ Ryzyko("Koszty leczenia", 2.75), Ryzyko("NNW", 0.55), Ryzyko("OC", 1.00) ]
        ryzykaOstaszewski16 = [ Ryzyko("Koszty leczenia", 2.50), Ryzyko("NNW", 0.45), Ryzyko("OC", 1.15), Ryzyko("Assistance", 1.25) ]
        ryzykaStateStreet16 = [ Ryzyko("Koszty leczenia", 2.40), Ryzyko("NNW", 0.40), Ryzyko("OC", 0.90), Ryzyko("Assistance", 1.15) ]

        poprzednie_polisy = [
            Polisa(6, "Kross", date(2016, 02, 10), "Swiat", 200, ryzykaKross16, date(2016, 02, 07)),
            Polisa(7, "Polsat", date(2016, 02, 12), "Europa", 100, ryzykaPolsat16, date(2016, 02, 05)),
            Polisa(8, "Ostaszewski Spedycja", date(2016, 02, 17), "Europa", 500, ryzykaOstaszewski16, date(2016, 02, 10)),
            Polisa(9, "State Street", date(2016, 02, 19), "Europa", 250, ryzykaStateStreet16, date(2016, 02, 10)),
        ]


        with RepozytoriumUbezpieczen() as repozytorium_ubezpieczen:
            for polisa in nowe_polisy:
                repozytorium_ubezpieczen.add(polisa)
            for polisa in poprzednie_polisy:
                repozytorium_ubezpieczen.add(polisa)

            repozytorium_ubezpieczen.complete()
    except UbezpieczeniaDbException as e:
        print(e)

    print RepozytoriumUbezpieczen().getById(1)

    try:
        with RepozytoriumUbezpieczen() as repozytorium_ubezpieczen:
            repozytorium_ubezpieczen.update( Polisa(1, u"Kross", date(2017, 02, 15), u"Swiat", 400, ryzykaKross))
            repozytorium_ubezpieczen.complete()
    except UbezpieczeniaDbException as e:
        print(e)

    print RepozytoriumUbezpieczen().getById(1)

    #wypisz wszystkie polisy klienta "Ostaszewski spedycja"
    print RepozytoriumUbezpieczen().getByKlient("Ostaszewski Spedycja")

    #wypisz wszystkie polisy na Europę
    print RepozytoriumUbezpieczen().getByTerytorium("Europa")
