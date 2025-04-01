import psycopg2
import os
import json
from tqdm import tqdm  # This library is used to show progress bars
from postgres_nltk import processing  # Import the processing function from postgres_nltk.py

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
                    type TEXT,
                    processed_description TEXT,
                    processed_title TEXT
                );
                """
                cursor.execute(create_table_query)
                conn.commit()  # Ensure changes are committed to the database
                print("Tabella 'dataset' caricata con successo.")
        except Exception as e:
            print(f"Errore nella creazione della tabella: {e}")

def popolate_table(conn):
    data_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Dataset")
    if conn:
        try:
            with conn.cursor() as cursor:
                # Get all JSON files in the data folder
                json_files = [f for f in os.listdir(data_folder) if f.endswith(".json")]
                total_files = len(json_files)
                if total_files == 0:
                    print("Nessun file JSON trovato nella cartella.")
                    return
                
                # Show progress bar
                for file_name in tqdm(json_files, desc="Inserimento dati", unit="file"):
                    file_path = os.path.join(data_folder, file_name)
                    # Open the JSON file
                    with open(file_path, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        id, title, release_year, genres_list, average_rating, description, type = data.values()

                        processed_title = processing(title)
                        processed_description = processing(description)

                        # Convert genres list to string
                        genres = ', '.join(genres_list)
                        # Modify date if it's empty
                        if release_year == "":
                            release_year = -1
                        insert_query = """
                        INSERT INTO dataset (id, title, release_year, genres, average_rating, description, type, processed_description, processed_title)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                        """     # %s is a placeholder for the values (to prevent SQL injection). The DB driver automaticcaly converts the values to the correct SQL format.
                        cursor.execute(insert_query, (id, title, int(release_year), genres, average_rating, description, type, processed_description, processed_title))
                        # Copy the description and title to the processed columns
                        #cursor.execute("UPDATE dataset SET processed_description = description, processed_title = title WHERE id = %s;", (id,))
                        # Commit the changes to the database
                        conn.commit()
                print("\nDati inseriti con successo.")
        except Exception as e:
            print(f"\nErrore durante l'inserimento dei dati: la Tabella è già popolata")