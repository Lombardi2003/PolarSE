import psycopg2
from postgres_creation import connect_to_db

# Configurazione del database
DB_NAME = "movies_series_db"

# Creazione degli indici
def create_indexes():
    conn = connect_to_db(DB_NAME)
    if conn:
        try:
            with conn.cursor() as cursor:       
                # Indice per ricerca veloce su id
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_id ON dataset (id);")

                # Indice per ricerca veloce su title
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_title ON dataset (title);")

                # Indice per ricerca per anno di uscita
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_release_year ON dataset (release_year);")

                # Indice per ricerca rapida nei generi (usa pattern matching su TEXT)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_genres ON dataset (genres);")

                # Indice per ordinamenti basati su rating
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_average_rating ON dataset (average_rating);")

                # Indice Full-Text Search su description
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_description ON dataset USING GIN(to_tsvector('english', description));")

                print("Indici creati con successo!")
        except Exception as e:
            print(f"Errore nella creazione degli indici: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    create_indexes()