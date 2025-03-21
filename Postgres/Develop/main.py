from database_config import DatabaseConfig
from db_creation import create_db 
import psycopg2
import time

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
            print("Connection established successfully")
            return conn  # Connessione riuscita, restituisce connessione
        except Exception as e:
            print(f"Errore di connessione: {e}")
            time.sleep(config.RECONNECT_INTERVAL)  # Attendi 1 secondo prima di ritentare

    print("Connessione non riuscita dopo 7 tentativi.")
    return None  # Restituisce None se non riesce a connettersi

def main():
    database = DatabaseConfig()    # Create a new database configuration
    conn = db_connection(database) # Connect to the database
    if conn is None:  
        print("Creazione del database in corso...")
        create_db(database) # Avvia lo script di creazione del DB
        conn = db_connection(database)  # Riprova a connettersi dopo la creazione
        print("Database creato e connesso con successo.")
    
    #  Close the connection
    if conn:
        conn.close()

if __name__ == '__main__':
    main()
