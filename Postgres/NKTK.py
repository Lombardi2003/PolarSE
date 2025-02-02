import psycopg2
from postgres_creation import connect_to_db
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Scarica le risorse necessarie di NLTK
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Configurazione del database
DB_NAME = "movies_series_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"
DB_HOST = "localhost"
DB_PORT = "5432"

def preprocess_query(query):
    """Tokenizza, rimuove stopwords e lemmatizza la query dell'utente."""
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    
    tokens = word_tokenize(query.lower())  # Tokenizzazione e conversione in minuscolo
    filtered_tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words and word.isalnum()]
    
    return " & ".join(filtered_tokens)  # Unisce i termini con AND logico per la ricerca full-text

def parse_query(query):
    """Analizza la query dell'utente e restituisce la parte full-text e le condizioni numeriche separate."""
    parsed_query = []
    numeric_conditions = []
    terms = query.split(" AND ")

    for term in terms:
        term = term.strip()
        if ":" in term:
            field, value = term.split(":", 1)
            field, value = field.strip(), value.strip()
            
            if field in ["release_year", "average_rating"] and re.match(r"^[<>]=?\d+$", value):
                numeric_conditions.append(f"{field} {value}")
            else:
                parsed_query.append(preprocess_query(value))
        else:
            parsed_query.append(preprocess_query(term))
    
    return " & ".join(parsed_query), numeric_conditions

def search_with_bm25(query):
    """Esegue una ricerca full-text con BM25 e supporto per query avanzate."""
    conn = connect_to_db(DB_NAME)
    if conn:
        try:
            with conn.cursor() as cursor:
                full_text_query, numeric_conditions = parse_query(query)
                
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
                
                if numeric_conditions:
                    sql_query += " AND " + " AND ".join(numeric_conditions)
                sql_query += " ORDER BY rank DESC LIMIT 10;"
                
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
