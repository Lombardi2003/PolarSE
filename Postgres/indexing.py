import psycopg2

# Script per la creazione degli indici per il database
def create_indexes(conn):
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
                # Indice per ricerca veloce su type
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON dataset (type);")
                # Commit delle modifiche al db
                conn.commit()
                print("Indici creati con successo.")
        except Exception as e:
            print(f"Errore nella creazione degli indici: gli indici che vuoi creare potrebbero già esistere.")
