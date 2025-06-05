import re
from Postgres.database_config import DatabaseConfig
from Postgres.db_setup import create_db, create_table, popolate_table, table_exists, control_popolate, index_exists
from Postgres.indexing import create_indexes
from Postgres.search_engine import SearchEngine  # Import the SearchEngine class from search_engine.py
# Python library to visualize in a correct way html characters in the console
from html import unescape
import shutil

import psycopg2
import time
import os
from re import sub

# DB connection
def db_connection(config, retry=True):
    for i in range(config.RECONNECT_ATTEMPTS):
        if retry:
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

def setup_postgres():
    os.system('cls' if os.name == 'nt' else 'clear')  # Pulisce la console
    database = DatabaseConfig()    # Create a new database configuration
    conn = db_connection(database) # Connect to the database
    if conn is None:  
        time.sleep(1)  # Attendi 3 secondi
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
        
    close_connection(conn)

def main_postgres():
    
    database = DatabaseConfig()    # Create a new database configuration
    conn = db_connection(database, False) # Connect to the database

    # Prompt per la scelta del ranking
    ricerca = SearchEngine(database, conn)  # Create an instance of the SearchEngine class
    print("Benvenuto nel motore di ricerca!\n")
    while True:
        print("\nScegli il ranking da utilizzare per la ricerca:")
        scelta=input("1: TF-IDF (basato su ts_rank, metodo di default per Postgres); \n2: BM25 (basato su ts_rank_cd); \n3: Torna al menù scelta del Search Engine; \nSCELTA: ")
        try:
            if scelta == '1':
                result = ricerca.tfidf_search()
            elif scelta == '2':
                result = ricerca.bm25_search()
            elif scelta == '3':
                # Close the connection
                close_connection(conn)
                return 0
        except Exception:
            print("Scelta non valida.")
            continue

        if result == 0:
            print("❌Nessun risultato trovato.")
        os.system('cls' if os.name == 'nt' else 'clear')
        terminal_width = shutil.get_terminal_size().columns
        titolo = "📌 \033[1mSearch Results:\033[0m"
        print(titolo.center(terminal_width))
        for r in result:
            print(f"🎬 \033[1m{r[0]}\033[0m (\033[1;32m{r[1] if r[1] != -1 else 'Year not available'}\033[0m)")
            print(f"📽️  \033[1mType:\033[0m \033[1;35m{r[4]}\033[0m")
            print(f"⭐ \033[1mAverage Rating:\033[0m \033[1;38;5;229m{r[5]}\033[0m")
            print(f"🎭 \033[1mGenre:\033[0m \033[38;5;208m{r[2] if r[2] else 'N/A'}\033[0m")
            print(f"\n📝 \033[1mDescription:\033[0m\n   {r[3]}")

            # Campi headline: partono da r[6] in poi
            found_snippet = False
            for i in range(6, len(r)):
                snippet = r[i]
                if not snippet or not isinstance(snippet, str):
                    continue
                if "<b>" not in snippet:
                    continue
                if not found_snippet:
                    print("\n🔍 \033[1mSearch Highlights:\033[0m")
                    found_snippet = True
                testo_html = unescape(snippet)
                testo_html = sub(r'<b>(.*?)</b>', '\033[1;34m\\1\033[0m', testo_html, flags=re.DOTALL)
                print(f"   - {testo_html}...")
            print()
            print("-" * terminal_width)
            print()

if __name__ == '__main__':
    main_postgres()