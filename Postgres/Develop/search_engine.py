import os
import psycopg2

class SearchEngine:
    def __init__(self, db, conn, limit=10):
        self.db = db
        self.conn = conn
        self.limit = limit

    """ Per implementare la ricerca full text, deve esserci una funzione per creare un tsvector da un documento e un tsquery da una query utente. 
        Inoltre, occorre restituire i risultati in un ordine utile, quindi c'è bisogno di una funzione che confronti i documenti rispetto alla 
        loro pertinenza alla query. È anche importante essere in grado di visualizzare i risultati in modo gradevole. 
        PostgreSQL fornisce supporto per tutte queste funzioni """

    # Implementazione della ricerca TF-IDF
    def tfidf_search(self):
        text = input("Scegli il campo su cui effettuare la ricerca ([title, description, genres, type]:[valore]): ") 
        field, search_value = text.split(":")
        results = self.execute_ts_rank(field, search_value)
        return results
    
    # Implementazione della ricerca BM25
    def bm25_search(self):
        pass
    
    #Restituisce la stringa SQL per generare il ts_vector su un campo specifico.
    @staticmethod
    def generate_ts_vector(field):
        return f"to_tsvector('english', {field})"

    #Converte il valore cercato in una query compatibile con ts_query.
    @staticmethod
    def generate_ts_query(search_value):
        return search_value.replace(" ", " & ")  # PostgreSQL usa '&' per AND
    
    #Costruisce la query SQL utilizzando ts_vector, ts_query e ts_rank.
    @staticmethod
    def generate_query(field, search_value):
        ts_vector = SearchEngine.generate_ts_vector(field)
        ts_query = "to_tsquery('english', %s)"
        query = f"""
        SELECT title, release_year, genres, description, type, average_rating,
            ts_rank({ts_vector}, {ts_query}) AS rank
        FROM dataset
        WHERE {ts_vector} @@ {ts_query}
        ORDER BY rank DESC
        LIMIT 10;
        """
        return query
    
    # Esegue la query e restituisce i risultati ordinati per ranking.
    def execute_ts_rank(self, field, search_value):
        cur = self.conn.cursor()
        sql_query = SearchEngine.generate_query(field, search_value)
        ts_query_value = SearchEngine.generate_ts_query(search_value)
        cur.execute(sql_query, (ts_query_value, ts_query_value))
        results = cur.fetchall()
        cur.close()        
        return results   