import psycopg2
from postgres_creation import connect_to_db
import re
import math

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

def calculate_idf(cursor, term, total_documents):
    """Calcola l'IDF per un dato termine."""
    query = f"""
    SELECT COUNT(*) 
    FROM dataset 
    WHERE to_tsvector('english', coalesce(title, '')) @@ to_tsquery('english', %s) OR
          to_tsvector('english', coalesce(release_year, '')) @@ to_tsquery('english', %s) OR
          to_tsvector('english', array_to_string(genres, ' ')) @@ to_tsquery('english', %s) OR
          to_tsvector('english', coalesce(description, '')) @@ to_tsquery('english', %s);
    """
    cursor.execute(query, (term, term, term, term))
    doc_count = cursor.fetchone()[0]
    idf = math.log(total_documents / (doc_count + 1))  # +1 per evitare la divisione per zero
    return idf

def search_with_tfidf(query):
    """Esegue una ricerca full-text con TF-IDF su tutti i campi e supporto per query binarie."""
    conn = connect_to_db(DB_NAME)
    if conn:
        try:
            with conn.cursor() as cursor:
                # Elabora la query dell'utente
                full_text_query, numeric_conditions = parse_query(query)

                # Controlla se ci sono condizioni numeriche vuote
                if any(not condition for condition in numeric_conditions):
                    raise ValueError("Le condizioni numeriche contengono valori vuoti o non validi!")

                # Conta il numero totale di documenti nel database
                cursor.execute("SELECT COUNT(*) FROM dataset")
                total_documents = cursor.fetchone()[0]

                # Calcola il TF per ogni documento e il punteggio IDF per ciascun termine
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

                cursor.execute(sql_query, (full_text_query, full_text_query))
                results = cursor.fetchall()

                print("\n🔍 Risultati TF-IDF per la ricerca:", query)
                for row in results:
                    rank = row[6]  # Il rank calcolato dal TS-Rank
                    # Calcola il TF e l'IDF per ogni documento e applica il TF-IDF
                    terms = full_text_query.split(" & ")
                    tfidf_score = 0
                    for term in terms:
                        term = term.strip()
                        idf = calculate_idf(cursor, term, total_documents)
                        tf = rank  # Questo può essere adattato a seconda del TF calcolato per il termine
                        tfidf_score += tf * idf

                    print(f"\n🎬 {row[1]} ({row[2]}) - TF-IDF Rank: {tfidf_score:.4f}  -  Type: {row[5]}\n   {row[4]}\n   Genere: {', '.join(row[3])}")

        except Exception as e:
            print(f"Errore nella ricerca TF-IDF: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    search_query = input("Inserisci il termine di ricerca (usa AND, OR, NOT se necessario): ")
    search_with_tfidf(search_query)
