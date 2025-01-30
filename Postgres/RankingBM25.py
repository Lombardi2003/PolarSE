import psycopg2
from postgres_creation import connect_to_db
import re

# Configurazione del database
DB_NAME = "movies_series_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

def parse_query(query):
    """Analizza la query dell'utente e restituisce la parte full-text e le condizioni numeriche separate."""
    parsed_query = []
    numeric_conditions = []
    query_params = []

    terms = query.split(" AND ")

    for term in terms:
        term = term.strip()
        if ":" in term:  # Query con campo specifico
            field, value = term.split(":", 1)
            field = field.strip()
            value = value.strip()

            # Gestione dei campi numerici con operatori
            if field == "release_year" or field == "average_rating":  # esempio numerico
                # Controlla se il valore è vuoto o non valido
                if value and re.match(r"^[<>]=?\d+$", value):  # Verifica se è un valore numerico valido
                    if value.startswith(">="):
                        numeric_conditions.append(f"{field} >= '{value[2:].strip()}'")
                    elif value.startswith(">"):
                        numeric_conditions.append(f"{field} > '{value[1:].strip()}'")
                    elif value.startswith("<="):
                        numeric_conditions.append(f"{field} <= '{value[2:].strip()}'")
                    elif value.startswith("<"):
                        numeric_conditions.append(f"{field} < '{value[1:].strip()}'")
                    elif value.startswith("[") and value.endswith("]"):  # range
                        start, end = value[1:].split(' TO ')
                        numeric_conditions.append(f"{field} BETWEEN '{start}' AND '{end}'")
                    else:
                        numeric_conditions.append(f"{field} = '{value}'")
                else:
                    print(f"Valore non valido per {field}: {value}. Verrà ignorato.")
            else:  # Campo testuale
                parsed_query.append(f"({value})")
        else:  # Termini generali (senza specificare il campo)
            parsed_query.append(f"({term})")

    # Crea la parte della query full-text
    full_text_query = " & ".join(parsed_query)

    # Restituisci sia la parte della query full-text che le condizioni numeriche
    return full_text_query, numeric_conditions

def search_with_bm25(query):
    """Esegue una ricerca full-text con BM25 su tutti i campi e supporto per query binarie."""
    conn = connect_to_db(DB_NAME)
    if conn:
        try:
            with conn.cursor() as cursor:
                # Elabora la query dell'utente
                full_text_query, numeric_conditions = parse_query(query)

                # Controlla se ci sono condizioni numeriche vuote
                if any(not condition for condition in numeric_conditions):
                    raise ValueError("Le condizioni numeriche contengono valori vuoti o non validi!")

                # Costruisci la query SQL
                sql_query = f"""
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
                """

                # Aggiungi le condizioni numeriche (non facendole diventare parte del full-text)
                if numeric_conditions:
                    sql_query += " AND " + " AND ".join(numeric_conditions)

                sql_query += " ORDER BY rank DESC LIMIT 10;"

                # Esegui la query
                cursor.execute(sql_query, (full_text_query, full_text_query))
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
