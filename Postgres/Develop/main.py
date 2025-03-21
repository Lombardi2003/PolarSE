from database_config import DatabaseConfig
import psycopg2

# DB connection
def db_connection(config):
    """Crea una connessione al database usando i parametri forniti"""
    try:
        conn = psycopg2.connect(
            dbname=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            host=config.IP_ADDRESS,
            port=config.PORT_NUMBER
        )
        print("Connection established successfully")
        return conn
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def main():
    database = DatabaseConfig()    # Create a new database configuration
    conn = db_connection(database) # Connect to the database

    #  Close the connection
    if conn:
        conn.close()

if __name__ == '__main__':
    main()
