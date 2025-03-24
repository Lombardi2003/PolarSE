from database_config import DatabaseConfig
from db_setup import create_db, create_table, popolate_table
from indexing import create_indexes

import psycopg2
import time
import os

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
            time.sleep(3)  # Attendi 1 secondo
            os.system('cls' if os.name == 'nt' else 'clear')  # Pulisce la console
            print("Connessione al database stabilita con successo.\n")
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
    
    # Creazione della tabella
    create_table(conn)
    
    # Popolamento della tabella
    popolate_table(conn)

    # Creazione degli indici
    create_indexes(conn)

    # Close the connection
    close_connection(conn)

if __name__ == '__main__':
    main()
