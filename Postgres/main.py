import re
from database_config import DatabaseConfig
from db_setup import create_db, create_table, popolate_table, table_exists, control_popolate, index_exists
from indexing import create_indexes
from search_engine import SearchEngine  # Import the SearchEngine class from search_engine.py
# Python library to visualize in a correct way html characters in the console
from html import unescape

import psycopg2
import time
import os
from re import sub

# DB connection
def db_connection(config):
    for i in range(config.RECONNECT_ATTEMPTS):
        print(f"Tentativo di connessione al database {i+1}/{config.RECONNECT_ATTEMPTS}...")
        try:
            conn = psycopg2.connect(
                dbname=config.DB_NAME,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                host=config.IP_ADDRESS,
                port=config.PORT_NUMBER
            )
            print("Connessione al database stabilita con successo.\n")
            time.sleep(3)  # Attendi 1 secondo
            os.system('cls' if os.name == 'nt' else 'clear')  # Pulisce la console
            print("Connessione al database stabilita con successo.\n")
            return conn  # Connessione riuscita, restituisce connessione
        except Exception as e:
            print(f"Errore di connessione: {e}")
            time.sleep(config.RECONNECT_INTERVAL)  # Attendi 1 secondo prima di ritentare

    print("Connessione non riuscita dopo 7 tentativi.\n")
    return None  # Restituisce None se non riesce a connettersi

# DB close connection
def close_connection(conn):
    if conn:
        conn.close()
        print("Connessione chiusa con successo.")

def main():
    os.system('cls' if os.name == 'nt' else 'clear')  # Pulisce la console
    database = DatabaseConfig()    # Create a new database configuration
    conn = db_connection(database) # Connect to the database
    if conn is None:  
        time.sleep(3)  # Attendi 3 secondi
        os.system('cls' if os.name == 'nt' else 'clear')  # Pulisce la console
        print("Creazione del database in corso...\n")
        create_db(database) # Avvia lo script di creazione del DB
        conn = db_connection(database)  # Riprova a connettersi dopo la creazione
        print("Database creato e connesso con successo.\n")

    if not table_exists(conn):
        create_table(conn)  # Creazione della tabella
    
    if control_popolate(conn) is True:
        popolate_table(conn) # Popolamento della tabella

    if index_exists(conn) is True:
        create_indexes(conn) # Creazione degli indici
    
    # Prompt per la scelta del ranking
    ricerca = SearchEngine(database, conn)  # Create an instance of the SearchEngine class
    print("Benvenuto nel motore di ricerca!\n")
    while True:
        print("\nScegli il ranking da utilizzare per la ricerca:")
        scelta=input("1: TF-IDF (basato su ts_rank, metodo di default per Postgres); \n2: BM25 (basato su ts_rank_cd);\n3: EXIT\nSCELTA: ")
        if scelta == '1':
            result = ricerca.tfidf_search()
        elif scelta == '2':
            result = ricerca.bm25_search()
        elif scelta == '3':
            break
        else:
            print("Scelta non valida.")
            continue
        if result == 0:
            continue
        os.system('cls' if os.name == 'nt' else 'clear')
        for r in result:
            print(f"\n🎬 {r[0]} (\033[1;32m{r[1] if r[1]!=-1 else 'Year not available'}\033[0m) - Type: \033[1;35m{r[4]}\033[0m) - ⭐ Average Rating:  \033[38;5;208m{r[5]}\033[0m)\n   {r[3]}")
            if r[2] == "":
                print("   Genere: N/A")
            else:
                print(f"   Genere: {r[2]}")
            # Campi headline: partono da r[6] in poi
            for i in range(6, len(r)):
                snippet = r[i]
                if not snippet or not isinstance(snippet, str):
                    continue
                if "<b>" not in snippet:
                    continue
                testo_html = unescape(snippet)
                testo_html = sub(r'<b>(.*?)</b>', '\033[1;34m\\1\033[0m', testo_html, flags=re.DOTALL)
                print(f" 🔍 You can find the searched word here: {testo_html}...")

            print("--------------------------------------------------")

    # Close the connection
    print("Arrivederci!!!")
    close_connection(conn)

if __name__ == '__main__':
    main()