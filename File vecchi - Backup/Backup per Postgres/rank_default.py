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
    """ Analizza la query e genera condizioni SQL """
    parsed_query = []
    numeric_conditions = []
    query_params = []
    terms = re.split(r" AND | OR ", query)

    for term in terms:
        term = term.strip()
        if ":" in term:
            field, value = term.split(":", 1)
            field, value = field.strip(), value.strip()

            if field == "release_year" or field == "average_rating":
                # Gestione del confronto numerico
                match = re.match(r"([<>]=?)\s*(\d+(\.\d+)?)", value)
                if match:
                    operator, num_value, _ = match.groups()
                    numeric_conditions.append(f"{field} {operator} %s")
                    query_params.append(float(num_value) if field == "average_rating" else int(num_value))
                else:
                    # Gestione dell'uguaglianza
                    try:
                        num_value = float(value) if field == "average_rating" else int(value)
                        numeric_conditions.append(f"{field} = %s")
                        query_params.append(num_value)
                    except ValueError:
                        print(f"❌ Errore: il valore '{value}' per '{field}' non è valido.")

            elif field == "title":
                parsed_query.append("LOWER(title) ILIKE LOWER(%s)")
                query_params.append(f"%{value}%")
            else:
                parsed_query.append(f"to_tsvector('english', coalesce({field}, '')) @@ to_tsquery('english', %s)")
                query_params.append(preprocess_query(value))
        else:
            term_processed = preprocess_query(term)
            parsed_query.append(f"(to_tsvector('english', coalesce(title, '')) @@ to_tsquery('english', %s) OR "
                                f"to_tsvector('english', coalesce(description, '')) @@ to_tsquery('english', %s))")
            query_params.extend([term_processed] * 2)

    conditions = " AND ".join(parsed_query)
    if numeric_conditions:
        conditions += " AND " + " AND ".join(numeric_conditions)

    return conditions, query_params


def search_with_ranking(query):
    """ Esegue la ricerca nel database con il modello di ranking di default di PostgreSQL """
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
                       ts_rank(
                           setweight(to_tsvector('english', coalesce(d.title, '')), 'A') ||
                           setweight(to_tsvector('english', coalesce(d.description, '')), 'B'),
                           to_tsquery('english', %s)
                       ) AS default_rank
                FROM dataset d
                JOIN doc_lengths ON d.id = doc_lengths.id
                CROSS JOIN avg_length
                WHERE {conditions}
                ORDER BY default_rank DESC NULLS LAST
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
                    print("\n🔍 Risultati con il ranking di default per la ricerca:", query)
                    for row in results:
                        print(f"\n🎬 {row[1]} ({row[2]}) - Type: {row[5]} - ⭐ {row[6]}\n   {row[4]}\n   Genere: {row[3]}")
        
        except Exception as e:
            print(f"❌ Errore nella ricerca con il ranking di default: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    search_query = input("Inserisci la query di ricerca: ")
    search_with_ranking(search_query)