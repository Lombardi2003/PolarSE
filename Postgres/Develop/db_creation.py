import psycopg2
import os
import json

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

def popolate_table(conn):
    data_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Dataset")
    if conn:
        try:
            with conn.cursor() as cursor:
                a = 0
                for file_name in os.listdir(data_folder):
                    a+=1; print(a)
                    if file_name.endswith(".json"):
                        with open(f"{data_folder}/{file_name}", "r", encoding="utf-8") as file:
                            data = json.load(file)
                            id, title, release_year, genres_list, average_rating, description, type = data.values()
                            # Convert genres list to string
                            genres = ', '.join(genres_list)
                            # Modify date if it's empty
                            if release_year == "":
                                release_year = -1
                            insert_query = """
                            INSERT INTO dataset (id, title, release_year, genres, average_rating, description, type)
                            VALUES (%s, %s, %s, %s, %s, %s, %s);
                            """
                            cursor.execute(insert_query, (id, title, int(release_year), genres, average_rating, description, type))
                            conn.commit()
                print("Dati inseriti con successo.")
        except Exception as e:
            print(f"Errore durante l'inserimento dei dati: {e}")