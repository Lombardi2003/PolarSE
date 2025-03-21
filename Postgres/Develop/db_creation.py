import psycopg2

def create_db(database):
    try:   
        conn = psycopg2.connect(
            dbname="postgres",
            user=database.DB_USER,
            password=database.DB_PASSWORD,
            host=database.IP_ADDRESS,
            port=database.PORT_NUMBER
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE {database.DB_NAME};")
        cur.close()
        conn.close()
        print(f"Database {database.DB_NAME} creato con successo.")
    except Exception as e:
        print(f"Errore durante la creazione del database: {e}")

def create_table(conn):
    pass