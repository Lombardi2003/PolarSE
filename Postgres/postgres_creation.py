import os
import json
import psycopg2
from psycopg2 import sql

# Configurazione del database
DB_NAME = "movies_series_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

# Funzione per connettersi al database
def connect_to_db(dbname=None):
    try:
        conn = psycopg2.connect(
            dbname=dbname or "postgres",
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Errore nella connessione al database: {e}")
        return None

# Creazione del database
def create_database():
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE {DB_NAME};")
                print(f"Database '{DB_NAME}' creato con successo.")
        except psycopg2.errors.DuplicateDatabase:
            print(f"Il database '{DB_NAME}' esiste già.")
        finally:
            conn.close()

# Creazione della tabella
def create_table():
    conn = connect_to_db(DB_NAME)
    if conn:
        try:
            with conn.cursor() as cursor:
                create_table_query = """
                CREATE TABLE IF NOT EXISTS movies (
                    id SERIAL PRIMARY KEY,
                    title TEXT,
                    release_date DATE,
                    genres TEXT [],
                    average_rating REAL,
                    description TEXT,
                    type TEXT
                );
                """
                cursor.execute(create_table_query)
                print("Tabella 'movies' creata con successo.")
        except Exception as e:
            print(f"Errore nella creazione della tabella: {e}")
        finally:
            conn.close()

# Popolazione della tabella
def populate_table(data_folder):
    conn = connect_to_db(DB_NAME)
    if conn:
        try:
            with conn.cursor() as cursor:
                for file_name in os.listdir(data_folder):
                    if file_name.endswith(".json"):
                        file_path = os.path.join(data_folder, file_name)
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            id = data.get("id")
                            title = data.get("title")
                            release_date = data.get("release_date")
                            genres = data.get("genres", [])  #Recupero la lista dei generi, se non presente metto una lista vuota
                            average_rating = data.get("average_rating")
                            description = data.get("description")
                            type = data.get("type")

                            insert_query = """
                            INSERT INTO movies (id, title, release_date, genres, average_rating, description, type)
                            VALUES (%s, %s, %s, %s, %s, %s, %s);
                            """
                            #Usa genres come array di stringhe
                            cursor.execute(insert_query, (id, title, release_date, genres, average_rating, description, type))
                print("Popolazione della tabella completata.")
        except Exception as e:
            print(f"Errore nella popolazione della tabella: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    # Percorso alla cartella contenente i file JSON
    data_folder = "movies_dataset_gestione"

    # Creazione del database e della tabella, poi popolazione
    create_database()
    create_table()
    populate_table(data_folder)
