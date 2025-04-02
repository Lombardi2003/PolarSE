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

    # Create tsvector from document
    def create_tsvector(self):
        tsvector = self.db.execute("SELECT to_tsvector('english', description) FROM dataset")
        print(tsvector)
        return tsvector
    
    # Create tsquery from user query
    def create_tsquery(self):
        query = input("Inserisci la tua query di ricerca: ")
        pass
    
    def tfidf_search(self):
        
        sql = """
        SELECT title, release_year, description, genres, type, 
            ts_rank(to_tsvector('english', title || ' ' || description), plainto_tsquery(%s)) AS rank
        FROM dataset
        WHERE to_tsvector('english', title || ' ' || description) @@ plainto_tsquery(%s)
        ORDER BY rank DESC
        LIMIT %s;
        """
        conn = self.conn
        cursor = conn.cursor()
        cursor.execute(sql, (query, query, limit))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return results

    def bm25_search(self):
        # Implementazione della ricerca BM25
        pass