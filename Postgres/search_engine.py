import psycopg2

columns = ["title", "description", "genres", "type", "release_year", "average_rating"]

class SearchEngine:
    def __init__(self, db, conn, limit=10):
        self.db = db
        self.conn = conn
        self.limit = limit

    @staticmethod
    def parse_query_input():
        operator = None
        text = input("Inserisci la query ([campo:valore] oppure più campi separati da un operatore booleano): ")
        if 'AND' in text:
            pairs = text.split(' AND ')
            operator = 'AND' 
        elif 'OR' in text:
            pairs = text.split(' OR ')
            operator = 'OR'
        else:
            pairs = list()
            pairs.append(text.strip())
            #pairs = text.strip().split()
        criteria = {}
        print(f"Query inserita e processata: {pairs}")
        for pair in pairs:
            if ':' in pair:
                key, value = pair.split(':') # questa riga fa in modo che se ci sono più ":" prenda solo il primo
                print(f"Campo: {key}, Valore: {value}")
                if key in columns or "NOT" in key:
                    if "NOT" in key:
                        operator += ' NOT'
                    key = key.replace("NOT", "").strip()
                    criteria[key] = value
                else:
                    print(f"Campo non valido: {key}")
            else:
                # fallback: se scrive solo una parola senza campo, assume sia il titolo
                criteria["title"] = pair
                criteria["description"] = pair
                operator = 'OR'

        return criteria, operator

    def search_auto(self, ranking_method='tfidf'):
        criteria, operator = SearchEngine.parse_query_input()
        if not criteria:
            print("Nessuna query valida inserita.")
            return []
        if len(criteria) == 1:
            field, value = next(iter(criteria.items())) # Prende il primo elemento del dizionario
            if field in ["release_year", "average_rating"]:
                return self.execute_simple_query(field, value)
            else:
                if ranking_method == 'bm25':
                    return self.execute_bm25_rank(field, value)
                else:
                    return self.execute_ts_rank(field, value)
        else:
            if ranking_method == 'bm25':
                return self.execute_complex_query(operator, criteria, 'bm25')
            else:
                return self.execute_complex_query(operator, criteria)

    def execute_simple_query(self, field, value):
        cur = self.conn.cursor()
        sql_query = SearchEngine.generate_query(field, value)
        if field == "release_year":
            value = int(value)
        elif field == "average_rating":
            value = float(value)
        cur.execute(sql_query, (value,))
        results = cur.fetchall()
        cur.close()
        return results

    @staticmethod
    def generate_query(field, search_value, ranking_method='tfidf'):
        if field == "release_year":
            query = f"""
            SELECT title, release_year, genres, description, type, average_rating
            FROM dataset
            WHERE {field} = %s
            ORDER BY {field} DESC
            LIMIT 10;
            """
        elif field == "average_rating":
            query = f"""
            SELECT title, release_year, genres, description, type, average_rating
            FROM dataset
            WHERE ROUND({field}::numeric,1) = %s
            ORDER BY {field} DESC
            LIMIT 10;
            """
        else:
            ts_vector = SearchEngine.generate_ts_vector(field)
            ts_query = "plainto_tsquery('english', %s)"  # Cambia to_tsquery con plainto_tsquery
            if ranking_method == 'bm25':
                query = f"""
                SELECT title, release_year, genres, description, type, average_rating,
                       ts_rank_cd({ts_vector}, {ts_query}) AS rank
                FROM dataset
                WHERE {ts_vector} @@ {ts_query}
                ORDER BY rank DESC
                LIMIT 10;
                """
            else:
                query = f"""
                SELECT title, release_year, genres, description, type, average_rating,
                       ts_rank({ts_vector}, {ts_query}) AS rank
                FROM dataset
                WHERE {ts_vector} @@ {ts_query}
                ORDER BY rank DESC
                LIMIT 10;
                """
        print(query)
        return query

    def tfidf_search(self):
        return self.search_auto(ranking_method='tfidf')

    def bm25_search(self):
        return self.search_auto(ranking_method='bm25')

    @staticmethod
    def generate_ts_vector(field):
        return f"to_tsvector('english', {field})"

    @staticmethod
    def generate_ts_query(search_value):
        # Mantieni la funzione come prima, convertendo gli spazi in ' & ' per to_tsquery, ma usa plainto_tsquery.
        search_value = search_value.replace(" ", " & ")
        return search_value

    def execute_ts_rank(self, field, search_value):
        cur = self.conn.cursor()
        sql_query = SearchEngine.generate_query(field, search_value)
        ts_query_value = SearchEngine.generate_ts_query(search_value)  # Restiamo con la stessa logica per convertire la query
        # Usiamo plainto_tsquery invece di to_tsquery per semplificare la sintassi
        cur.execute(sql_query, (ts_query_value, ts_query_value))  
        results = cur.fetchall()
        cur.close()
        return results

    def execute_bm25_rank(self, field, search_value):
        cur = self.conn.cursor()
        sql_query = SearchEngine.generate_query(field, search_value, ranking_method='bm25')
        ts_query_value = SearchEngine.generate_ts_query(search_value)
        # Usiamo plainto_tsquery invece di to_tsquery per semplificare la sintassi
        cur.execute(sql_query, (ts_query_value, ts_query_value))  
        results = cur.fetchall()
        cur.close()
        return results

    def execute_complex_query(self, operator, criteria, ranking_method='tfidf'):
        query, values = SearchEngine.generate_complex_query(operator, criteria, ranking_method)
        cur = self.conn.cursor()
        cur.execute(query, values)
        results = cur.fetchall()
        cur.close()
        return results
    
    @staticmethod
    def generate_complex_query(operator, criteria, ranking_method='tfidf'):
        values = []
        ts_query = "plainto_tsquery('english', %s)"  # Cambiato to_tsquery con plainto_tsquery
        if ranking_method == 'bm25':
            app = list()
            query = f"""
            SELECT title, release_year, genres, description, type, average_rating,"""

            ts_vector = ""
            for field, value in criteria.items():
                ts_vector = SearchEngine.generate_ts_vector(field)
                values.append(value)
                app.append(f"""
                     ts_rank_cd({ts_vector}, {ts_query})
                """)
            query += " + ".join(app)
            app = list()
            query +=""" AS rank
            FROM dataset
            WHERE """
            for field, value in criteria.items():
                ts_vector = SearchEngine.generate_ts_vector(field)
                values.append(value)
                app.append(f"""
                     {ts_vector} @@ {ts_query}
                """)
            query += f" {operator} ".join(app)
            query +=f"""
            ORDER BY rank DESC
            LIMIT 10;
            """
        else:
            app = list()
            query = f"""
            SELECT title, release_year, genres, description, type, average_rating,"""

            ts_vector = ""
            for field, value in criteria.items():
                ts_vector = SearchEngine.generate_ts_vector(field)
                values.append(value)
                app.append(f"""
                     ts_rank({ts_vector}, {ts_query})
                """)
            query += " + ".join(app)
            app = list()
            query +=""" AS rank
            FROM dataset
            WHERE """
            for field, value in criteria.items():
                ts_vector = SearchEngine.generate_ts_vector(field)
                values.append(value)
                app.append(f"""
                     {ts_vector} @@ {ts_query}
                """)
            query += f" {operator} ".join(app)
            query +=f"""
            ORDER BY rank DESC
            LIMIT 10;
            """
        print(query)
        print(f"Valori: {values}")
        return query, values
