import os
import json
import psycopg2

# Configurazione del database
DB_NAME = "movies_series_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

class Postgres:
    def __init__(self):
        """ Inizializza una connessione unica al database """
        self.conn = None

    def connect_to_db(self, dbname="postgres"):
        """ Connessione unica al database """
        try:
            if self.conn is None or self.conn.closed:
                self.conn = psycopg2.connect(
                    dbname=dbname,
                    user=DB_USER,
                    password=DB_PASSWORD,
                    host=DB_HOST,
                    port=DB_PORT,
                )
                self.conn.autocommit = True
            return self.conn
        except Exception as e:
            print(f"Errore nella connessione al database: {e}")
            return None

    def create_database(self):
        """ Creazione del database se non esiste """
        conn = self.connect_to_db("postgres")  # Connettersi al database di default
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}';")
                    exists = cursor.fetchone()
                    if not exists:
                        cursor.execute(f"CREATE DATABASE {DB_NAME};")
                        print(f"Database '{DB_NAME}' creato con successo.")
                    else:
                        print(f"Il database '{DB_NAME}' esiste già.")
            except Exception as e:
                print(f"Errore nella creazione del database: {e}")
            finally:
                conn.close()

    def create_table(self):
        """ Creazione della tabella se non esiste """
        conn = self.connect_to_db(DB_NAME)
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
                    print("Tabella 'dataset' creata con successo.")
            except Exception as e:
                print(f"Errore nella creazione della tabella: {e}")
            finally:
                conn.close()

    def populate_table(self, data_folder):
        """ Popolazione della tabella dal dataset JSON """
        conn = self.connect_to_db(DB_NAME)
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
                                release_year = data.get("release_year")

                                # Gestione del valore mancante per release_year
                                try:
                                    release_year = int(release_year) if release_year else None
                                except ValueError:
                                    release_year = None

                                genres_list = data.get("genres", [])
                                genres = ", ".join(genres_list)
                                average_rating = data.get("average_rating")
                                description = data.get("description")
                                type = data.get("type")

                                insert_query = """
                                INSERT INTO dataset (id, title, release_year, genres, average_rating, description, type)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (id) DO NOTHING;
                                """
                                cursor.execute(insert_query, (id, title, release_year, genres, average_rating, description, type))
                    print("Popolazione della tabella completata.")
            except Exception as e:
                print(f"Errore nella popolazione della tabella: {e}")
            finally:
                conn.close()

if __name__ == "__main__":
    data_folder = "Dataset"
    
    db = Postgres()
    db.create_database()
    db.create_table()
    db.populate_table(data_folder)
