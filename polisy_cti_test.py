# -*- coding: utf-8 -*-

import polisy_cti
import sqlite3
import unittest
from datetime import date

db_path = 'ubezpieczenia.db'

class RepositoryTest(unittest.TestCase):

    def setUp(self):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('DELETE FROM Ryzyka')
        c.execute('DELETE FROM Polisy')
        c.execute('''INSERT INTO Polisy (id, numer, nazwa_klienta, data_zawarcia, data_poczatku, data_konca,
            zakres_terytorialny, ilosc_osobodni, kwota_skladki) VALUES(1, "CTI/1/17", "UG", "2016-01-01", "2016-02-02", "2016-03-03", "Europa", 100, 400)''')
        c.execute('''INSERT INTO Ryzyka (nazwa, skladka_osobodzien, id_polisy) VALUES("KL", 3.00, 1)''')
        c.execute('''INSERT INTO Ryzyka (nazwa, skladka_osobodzien, id_polisy) VALUES("NNW", 1.00, 1)''')
        c.execute('''INSERT INTO Polisy (id, numer, nazwa_klienta, data_zawarcia, data_poczatku, data_konca,
            zakres_terytorialny, ilosc_osobodni, kwota_skladki) VALUES(2, "CTI/2/17", "PG", "2016-01-01", "2016-02-02", "2016-03-03", "Europa", 100, 300)''')
        c.execute('''INSERT INTO Ryzyka (nazwa, skladka_osobodzien, id_polisy) VALUES("KL", 3.00, 2)''')
        conn.commit()
        conn.close()

    def tearDown(self):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('DELETE FROM Ryzyka')
        c.execute('DELETE FROM Polisy')
        conn.commit()
        conn.close()

    def testGetByIdInstance(self):
        polisy_list = polisy_cti.RepozytoriumUbezpieczen().getById(1)
        self.assertEqual(len(polisy_list), 1, "Powinna być jedna polisa")
        polisa = polisy_list[0]
        self.assertIsInstance(polisa, polisy_cti.Polisa, "Objekt nie jest klasy Polisa")

    def testGetByTerytoriumNotFound(self):
        polisy_list = polisy_cti.RepozytoriumUbezpieczen().getByTerytorium("Swiat")
        self.assertEqual(len(polisy_list), 0, "Powinno być zero polis")

    def testGetByIdRyzykaCount(self):
        polisy_list = polisy_cti.RepozytoriumUbezpieczen().getById(1)
        self.assertEqual(len(polisy_list[0].ryzyka), 2, "Powinno wyjść 2")

    def testAddandGetByKlient(self):
        with polisy_cti.RepozytoriumUbezpieczen() as repozytorium_ubezpieczen:
            repozytorium_ubezpieczen.add(polisy_cti.Polisa(3, "UG", date(2017, 02, 18), "Swiat", 300, [polisy_cti.Ryzyko("KL", 4.00)]))
            repozytorium_ubezpieczen.complete()

        polisy_list = polisy_cti.RepozytoriumUbezpieczen().getByKlient("UG")
        self.assertEqual(len(polisy_list), 2, "Powinny być dwie polisy")

if __name__ == "__main__":
    unittest.main()
