import psycopg2
from postgres_creation import connect_to_db
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Scarica i dati necessari da NLTK
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

# Parametri per la connessione al database
DB_NAME = "movies_series_db"

# Parametri BM25
K1 = 1.5  
B = 0.75  

def preprocess_query(query):
    """ Prepara la query per il full-text search """
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()

    query = re.sub(r'[^a-zA-Z0-9\s]', '', query)  # Rimuove caratteri speciali
    tokens = word_tokenize(query.lower())
    filtered_tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words and word.isalnum()]
    
    return " & ".join(filtered_tokens)

def parse_query(query):
    """ Analizza la query e genera condizioni SQL con gestione di AND e OR """
    conditions = []
    query_params = []

    # Tokenizza in base a " AND " e " OR " preservando gli operatori
    tokens = re.split(r"( AND | OR )", query)
    current_clause = []
    last_operator = "AND"  # Operatore di default

    for token in tokens:
        token = token.strip()
        
        if token in {"AND", "OR"}:
            # Se è un operatore, salviamo la condizione accumulata e impostiamo l'operatore
            if current_clause:
                conditions.append(f" ({' AND '.join(current_clause)}) ")
                current_clause = []
            last_operator = token
        else:
            # Analizza il termine della query
            if ":" in token:
                field, value = token.split(":", 1)
                field, value = field.strip(), value.strip()

                if field in {"release_year", "average_rating"}:
                    match = re.match(r"([<>]=?)\s*(\d+(\.\d+)?)", value)
                    if match:
                        operator, num_value, _ = match.groups()
                        current_clause.append(f"{field} {operator} %s")
                        query_params.append(float(num_value) if field == "average_rating" else int(num_value))
                    else:
                        try:
                            num_value = float(value) if field == "average_rating" else int(value)
                            current_clause.append(f"{field} = %s")
                            query_params.append(num_value)
                        except ValueError:
                            print(f"❌ Errore: valore '{value}' non valido per '{field}'")
                elif field == "title":
                    current_clause.append("LOWER(title) ILIKE LOWER(%s)")
                    query_params.append(f"%{value}%")
                else:
                    current_clause.append(f"to_tsvector('english', coalesce({field}, '')) @@ to_tsquery('english', %s)")
                    query_params.append(preprocess_query(value))
            else:
                term_processed = preprocess_query(token)
                current_clause.append(f"(to_tsvector('english', coalesce(title, '')) @@ to_tsquery('english', %s) OR "
                                      f"to_tsvector('english', coalesce(description, '')) @@ to_tsquery('english', %s))")
                query_params.extend([term_processed] * 2)

    # Aggiunge l'ultima clausola
    if current_clause:
        conditions.append(f" ({' AND '.join(current_clause)}) ")

    # Combina tutte le condizioni rispettando gli operatori AND/OR
    final_conditions = f" {last_operator} ".join(conditions)

    return final_conditions, query_params

def search_with_bm25(query):
    """ Esegue la ricerca nel database con BM25 """
    conn = connect_to_db(DB_NAME)
    if conn:
        try:
            with conn.cursor() as cursor:
                conditions, query_params = parse_query(query)
                
                # Stampa per il debug: verifica la query e i parametri
                print("Condizioni della query:", conditions)
                print("Parametri della query:", query_params)
                
                # Genera la query SQL
                sql_query = f"""
                WITH doc_lengths AS (
                    SELECT id, 
                           length(coalesce(title, '')) + 
                           length(coalesce(description, '')) + 
                           length(coalesce(genres, '')) AS doc_length
                    FROM dataset
                ), avg_length AS (
                    SELECT AVG(doc_length) AS avg_doc_length 
                    FROM doc_lengths
                )
                SELECT d.id, 
                       d.title, 
                       d.release_year, 
                       d.genres, 
                       d.description, 
                       d.type,
                       d.average_rating,
                       ts_rank_cd(
                           setweight(to_tsvector('english', coalesce(d.title, '')), 'A') ||
                           setweight(to_tsvector('english', coalesce(d.description, '')), 'B'),
                           to_tsquery('english', %s)
                       ) / (1 + {K1} * ((doc_lengths.doc_length::float / avg_length.avg_doc_length) * {B})) AS bm25_rank
                FROM dataset d
                JOIN doc_lengths ON d.id = doc_lengths.id
                CROSS JOIN avg_length
                WHERE {conditions}
                ORDER BY bm25_rank DESC NULLS LAST, d.id
                LIMIT 10;
                """
                
                # Parametri finali della query
                final_query_params = [preprocess_query(query)] + query_params
                
                # Stampa per il debug: mostra la query finale
                print("\n🔍 Query SQL Generata:\n", sql_query)
                print("\n📝 Parametri:\n", final_query_params)

                cursor.execute(sql_query, tuple(final_query_params))
                results = cursor.fetchall()
                
                if not results:
                    print("❌ Nessun risultato trovato!")
                else:
                    print("\n🔍 Risultati BM25 per la ricerca:", query)
                    for row in results:
                        print(f"\n🎬 {row[1]} ({row[2]}) - Type: {row[5]} - ⭐ Average Rating:  {row[6]}\n   {row[4]}\n   Genere: {row[3]}")
        
        except Exception as e:
            print(f"❌ Errore nella ricerca BM25: {e}")
        finally:
            conn.close()
            
if __name__ == "__main__":
    search_query = input("Inserisci il termine di ricerca (usa AND, OR, NOT se necessario): ")
    search_with_bm25(search_query)
