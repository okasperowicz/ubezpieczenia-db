import sqlite3


db_path = 'ubezpieczenia.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

#
# Wyczyszczenie starej bazy
#
c.execute("DROP TABLE IF EXISTS Polisy")
c.execute("DROP TABLE IF EXISTS Ryzyka")

#
# Tabele
#
c.execute('''
          CREATE TABLE Polisy
          ( id INTEGER PRIMARY KEY,
            numer VARCHAR(30) NOT NULL,
            nazwa_klienta VARCHAR(100) NOT NULL,
            data_zawarcia DATE NOT NULL,
            data_poczatku DATE NOT NULL,
            data_konca DATE NOT NULL,
            zakres_terytorialny  VARCHAR(10) NOT NULL,
            ilosc_osobodni INTEGER NOT NULL,
            kwota_skladki MONEY NOT NULL
          )
          ''')
c.execute('''
          CREATE TABLE Ryzyka
          ( nazwa VARCHAR(50),
            skladka_osobodzien MONEY NOT NULL,
            id_polisy INTEGER,
           FOREIGN KEY(id_polisy) REFERENCES Polisy(id),
           PRIMARY KEY (nazwa, id_polisy))
          ''')
