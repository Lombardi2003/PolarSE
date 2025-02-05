import psycopg2
from postgres_creation import connect_to_db

DB_NAME = "movies_series_db"

def parse_query(query):
    """Analizza la query e separa la parte full-text dalle condizioni specifiche, gestendo AND, OR e operatori di confronto su release_year."""
    parsed_query = []
    conditions = []
    full_text_field = None

    terms = query.split(" ")
    current_operator = "&"  # AND di default
    temp_query = []

    for term in terms:
        term = term.strip()
        if term.upper() == "OR":
            current_operator = "|"
        elif term.upper() == "AND":
            current_operator = "&"
        else:
            # Controlla se la query contiene un operatore per release_year
            if ":" in term:
                field, value = term.split(":", 1)
                field, value = field.strip(), value.strip()

                if field in ["title", "genres", "description", "type"]:
                    full_text_field = field
                    temp_query.append(value)

            else:
                temp_query.append(term)

        if temp_query:
            parsed_query.append(f" {current_operator} ".join(temp_query))
            temp_query = []

    full_text_query = " | ".join(parsed_query) if parsed_query else ''
    return full_text_query, conditions, full_text_field


def search_with_ranking(user_query):
    """Esegue una ricerca full-text con ranking in PostgreSQL, supportando sia AND che OR e operatori di confronto su release_year."""
    conn = connect_to_db(DB_NAME)
    if not conn:
        print("Errore di connessione al database.")
        return
    
    try:
        with conn.cursor() as cursor:
            full_text_query, conditions, full_text_field = parse_query(user_query)

            if full_text_field:
                tsvector_query = f"setweight(to_tsvector('english', coalesce({full_text_field}, '')), 'A')"
            else:
                tsvector_query = """
                setweight(to_tsvector('english', coalesce(title, '')), 'A') || 
                setweight(to_tsvector('english', coalesce(description, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(genres, ' ')), 'C')
                """

            sql_query = f"""
            SELECT id, title, release_year, genres, description, type, 
                   ts_rank_cd(
                       {tsvector_query},
                       to_tsquery('english', %s)
                   ) AS rank
            FROM dataset
            WHERE {tsvector_query} @@ to_tsquery('english', %s)
            """

            if conditions:
                sql_query += " AND " + " AND ".join(conditions)
            
            sql_query += " ORDER BY rank DESC LIMIT 10;"

            cursor.execute(sql_query, (full_text_query, full_text_query))
            results = cursor.fetchall()
            
            print("\n🔍 Risultati della ricerca per:", user_query)
            for row in results:
                rank_value = row[6] if row[6] is not None else 0.0
                print(f"\n🎬 {row[1]} ({row[2]})\n   {row[4]}\n   Genere: {row[3]} - Type: {row[5]}")
    
    except Exception as e:
        print(f"❌ Errore nella ricerca: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    search_query = input("Inserisci la query di ricerca: ")
    search_with_ranking(search_query)