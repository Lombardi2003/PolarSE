import psycopg2

from postgres_creation import connect_to_db

# Configurazione del database
DB_NAME = "movies_series_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

def search(query):
    conn = connect_to_db(DB_NAME)
    cur = conn.cursor()

    sql = """
        SELECT *, ts_rank(to_tsvector('english', title || ' ' || description), to_tsquery('english', %s)) AS rank
        FROM dataset
        WHERE to_tsvector('english', title || ' ' || description) @@ to_tsquery('english', %s)
        ORDER BY rank DESC;
        """
    
    cur.execute(sql, (query, query))
    results = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return results

if __name__ == "__main__":
    query = input("Inserisci la ricerca: ")
    risultati = search(query)

    if risultati:
        print("\nRisultati della ricerca:")
        for r in risultati:
            print(f"[{r[0]}] {r[1]} - Rank: {float(r[2]):.4f}")
    else:
        print("Nessun risultato trovato.")
