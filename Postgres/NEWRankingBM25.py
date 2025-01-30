import psycopg2
from postgres_creation import connect_to_db

# Configurazione del database
DB_NAME = "movies_series_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

def search_with_bm25(query):
    """Esegue una ricerca full-text con BM25 su tutti i campi e supporto per query binarie."""
    conn = connect_to_db(DB_NAME)
    if conn:
        try:
            with conn.cursor() as cursor:
                sql_query = """
                SELECT id, title, release_year, genres, description, type, 
                       ts_rank_cd(
                           setweight(to_tsvector('english', coalesce(title, '')), 'A') || 
                           setweight(to_tsvector('english', coalesce(release_year, '')), 'B') || 
                           setweight(to_tsvector('english', array_to_string(genres, ' ')), 'C') ||
                           setweight(to_tsvector('english', coalesce(description, '')), 'D'),
                           to_tsquery('english', %s)
                       ) AS rank
                FROM dataset
                WHERE (
                    setweight(to_tsvector('english', coalesce(title, '')), 'A') || 
                    setweight(to_tsvector('english', coalesce(release_year, '')), 'B') || 
                    setweight(to_tsvector('english', array_to_string(genres, ' ')), 'C') ||
                    setweight(to_tsvector('english', coalesce(description, '')), 'D')
                ) @@ to_tsquery('english', %s)
                ORDER BY rank DESC
                LIMIT 10;
                """
                cursor.execute(sql_query, (query, query))
                results = cursor.fetchall()

                print("\n🔍 Risultati BM25 per la ricerca:", query)
                for row in results:
                    print(f"\n🎬 {row[1]} ({row[2]}) - Rank: {row[6]:.4f}  -  Type: {row[5]}\n   {row[4]}\n   Genere: {', '.join(row[3])}")

        except Exception as e:
            print(f"Errore nella ricerca BM25: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    search_query = input("Inserisci il termine di ricerca (usa AND, OR, NOT se necessario): ")
    search_with_bm25(search_query)
