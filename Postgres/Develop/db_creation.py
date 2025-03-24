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
        create_table(conn)  # Call create_table function after creating the database
        conn.close()
        print(f"Database {database.DB_NAME} creato con successo.")
    except Exception as e:
        print(f"Errore durante la creazione del database: {e}")

def create_table(conn):
    if conn:
        try:
            with conn.cursor() as cursor:
                create_table_query = """
                CREATE TABLE IF NOT EXISTS dataset (
                    id SERIAL PRIMARY KEY,
                    title TEXT,
                    release_year INTEGER,      
                    genres TEXT,
                    average_rating REAL,
                    description TEXT,
                    type TEXT
                );
                """
                cursor.execute(create_table_query)
                conn.commit()  # Ensure changes are committed to the database
                print("Tabella 'dataset' creata con successo.")
        except Exception as e:
            print(f"Errore nella creazione della tabella: {e}")
