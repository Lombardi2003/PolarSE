import psycopg2
from postgres_creation import connect_to_db

def search_with_bm25(query):
    """Esegue una ricerca full-text con BM25 e ordina i risultati per pertinenza."""
    conn = connect_to_db()
    if conn:
        try:
            with conn.cursor() as cursor:
                sql_query = """
                SELECT id, title, description,
                       ts_rank_cd(to_tsvector('english', description), to_tsquery('english', %s)) AS rank
                FROM dataset
                WHERE to_tsvector('english', description) @@ to_tsquery('english', %s)
                ORDER BY rank DESC
                LIMIT 10;
                """
                cursor.execute(sql_query, (query, query))
                results = cursor.fetchall()

                print("\n🔍 Risultati BM25 per la ricerca:", query)
                for row in results:
                    print(f"\n🎬 {row[1]} - Rank: {row[3]:.4f}\n   {row[2]}\n")

        except Exception as e:
            print(f"Errore nella ricerca BM25: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    search_query = input("Inserisci il termine di ricerca: ")
    search_with_bm25(search_query)
