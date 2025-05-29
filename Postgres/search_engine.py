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
        if 'AND' in text or 'OR' in text:
            pairs, operator = SearchEngine.get_pairs(text)
        else:
            pairs = list()
            pairs.append(text.strip())
            #pairs = text.strip().split()
        criteria = []
        print(f"Query inserita e processata: {pairs}")
        for pair in pairs:
            # Query con uguale
            if ':' in pair:
                

                if ':<' in pair:
                    key, value = pair.split(':<') # questa riga fa in modo che se ci sono più ":" prenda solo il primo
                    print(f"Campo: {key}, Valore: {value}")
                    if key == "release_year" or key == "average_rating":
                        criteria.append((key, value, "<"))
                    else:
                        print(f"Query non valida: {key}, reinserire la query.")
                        return [], []
                # Query con maggiore
                elif ':>' in pair:
                    key, value = pair.split(':>') # questa riga fa in modo che se ci sono più ":" prenda solo il primo
                    print(f"Campo: {key}, Valore: {value}")
                    if key == "release_year" or key == "average_rating":
                        criteria.append((key, value, ">"))
                    else:
                        print(f"Query non valida: {key}, reinserire la query.")
                        return [], []
                else:
                    key, value = pair.split(':') # questa riga fa in modo che se ci sono più ":" prenda solo il primo
                    print(f"Campo: {key}, Valore: {value}")
                    if key in columns:
                        criteria.append((key, value, "="))
                    else:
                        print(f"Campo non valido: {key}, reinserire la query.")
                        return [], []
            # Query con una parola
            else:
                # fallback: se scrive solo una parola senza campo, assume sia il titolo
                criteria.append(("title", pair, "="))
                criteria.append(("description", pair, "="))
                operator = list()
                operator.append("OR")
        return criteria, operator

    def search_auto(self, ranking_method='tfidf'):
        criteria, operator = SearchEngine.parse_query_input()
        if not criteria:
            print("Nessuna query valida inserita.")
            return []
        if len(criteria) == 1:
            field, value, o = criteria.pop() # Prende il primo elemento del dizionario
            if field in ["release_year", "average_rating"]:
                return self.execute_simple_query(field, value, o)
            else:
                if ranking_method == 'bm25':
                    return self.execute_bm25_rank(field, value, o)
                else:
                    return self.execute_ts_rank(field, value, o)
        else:
            if ranking_method == 'bm25':
                return self.execute_complex_query(operator, criteria, 'bm25')
            else:
                return self.execute_complex_query(operator, criteria)

    def execute_simple_query(self, field, value, operation):
        cur = self.conn.cursor()
        sql_query = SearchEngine.generate_query(field, value, operation)
        if field == "release_year":
            if 'TO' not in value:
                value = int(value)
        elif field == "average_rating":
            if 'TO' not in value:
                value = float(value)
        cur.execute(sql_query, (value,))
        results = cur.fetchall()
        cur.close()
        return results

    @staticmethod
    def generate_query(field, search_value, operation, ranking_method='tfidf'):
        if field == "release_year":
            if 'TO' in search_value:
                val = search_value.split(" TO ")
                query = f"""
                SELECT title, release_year, genres, description, type, average_rating
                FROM dataset
                WHERE {field} BETWEEN {int(val[0][1:])} AND {int(val[1][:-1])}
                ORDER BY {field} DESC
                LIMIT 10;
                """
            else:
                query = f"""
                SELECT title, release_year, genres, description, type, average_rating
                FROM dataset
                WHERE {field} {operation} %s
                ORDER BY {field} DESC
                LIMIT 10;
                """
        elif field == "average_rating":
            if 'TO' in search_value:
                val = search_value.split(" TO ")
                query = f"""
                SELECT title, release_year, genres, description, type, average_rating
                FROM dataset
                WHERE ROUND({field}::numeric,1) BETWEEN {float(val[0][1:])} AND {float(val[1][:-1])}
                ORDER BY {field} DESC
                LIMIT 10;
                """
            else:        
                query = f"""
                SELECT title, release_year, genres, description, type, average_rating
                FROM dataset
                WHERE ROUND({field}::numeric,1) {operation} %s
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
                       ts_headline('english', {field}, {ts_query}) AS headline
                FROM dataset
                WHERE {ts_vector} @@ {ts_query}
                ORDER BY rank DESC
                LIMIT 10;
                """
            else:
                query = f"""
                SELECT title, release_year, genres, description, type, average_rating,
                       ts_rank({ts_vector}, {ts_query}) AS rank,
                       ts_headline('english', {field}, {ts_query}) AS headline
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

    def execute_ts_rank(self, field, search_value, operation):
        cur = self.conn.cursor()
        sql_query = SearchEngine.generate_query(field, search_value, operation)
        ts_query_value = SearchEngine.generate_ts_query(search_value)  # Restiamo con la stessa logica per convertire la query
        # Usiamo plainto_tsquery invece di to_tsquery per semplificare la sintassi
        cur.execute(sql_query, (ts_query_value, ts_query_value, ts_query_value))
        # Aggiungiamo ts_headline per evidenziare i risultati
        results = cur.fetchall()
        cur.close()
        return results

    def execute_bm25_rank(self, field, search_value, operation):
        cur = self.conn.cursor()
        sql_query = SearchEngine.generate_query(field, search_value, operation, ranking_method='bm25')
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
        headline_values = []
        ts_query = "plainto_tsquery('english', %s)"  # Cambiato to_tsquery con plainto_tsquery
        if ranking_method == 'bm25':
            app = list()
            headline_parts = []
            query = f"""
            SELECT title, release_year, genres, description, type, average_rating,"""
            ts_vector = ""
            print(f"Criteria: {criteria}")
            for field, value, o in criteria:
                if field == "release_year" or field == "average_rating":
                    continue
                else:
                    ts_vector = SearchEngine.generate_ts_vector(field)
                    values.append(value)
                    app.append(f"""
                        ts_rank_cd({ts_vector}, {ts_query})
                    """)
                    # Aggiungi ts_headline per evidenziare i risultati
                    headline_parts.append(f"""
                        ts_headline('english', {field}, {ts_query}) AS {field}_headline
                    """)
                    headline_values.append(value)
            # Aggiunta delle colonne headline nel SELECT
            if headline_parts:
                query += "\n" + ",\n".join(headline_parts) + ","        
            query += " + ".join(app)
            app = list()
            query +=""" AS rank
            FROM dataset
            WHERE """
            for field, value, o in criteria:
                if field == "release_year":
                    if 'TO' in value:
                        app.append(f"""
                            {field} BETWEEN %s AND %s
                        """)
                        val = value.split(" TO ")
                        values.append(int(val[0][1:]))
                        values.append(int(val[1][:-1]))
                    else:
                        app.append(f"""
                            {field} {o} %s
                        """)
                        values.append(value)
                elif field == "average_rating":
                    if 'TO' in value:
                        app.append(f"""
                            ROUND({field}::numeric,1) BETWEEN %s AND %s
                        """)
                        val = value.split(" TO ")
                        values.append(int(val[0][1:]))
                        values.append(int(val[1][:-1]))
                    else:
                        app.append(f"""
                        ROUND({field}::numeric,1) {o} %s
                        """)
                        values.append(value)
                else:
                    ts_vector = SearchEngine.generate_ts_vector(field)
                    values.append(value)
                    app.append(f"""
                        {ts_vector} @@ {ts_query}
                    """)
            s = ""
            i = 0
            for a in app:
                s += a
                if i < len(operator):
                    s += f" {operator[i]} "
                i += 1
            query += f" {s}"
            query +=f"""
            ORDER BY rank DESC
            LIMIT 10;
            """
        else:
            app = list()
            headline_parts = []
            query = f"""
            SELECT title, release_year, genres, description, type, average_rating,"""
            ts_vector = ""
            print(f"Criteria: {criteria}")
            for field, value, o in criteria:
                if field == "release_year" or field == "average_rating":
                    continue
                else:
                    ts_vector = SearchEngine.generate_ts_vector(field)
                    values.append(value)
                    app.append(f"""
                        ts_rank({ts_vector}, {ts_query})
                    """)
                    # ts_headline
                    headline_parts.append(f"""
                        ts_headline('english', {field}, {ts_query}) AS {field}_headline
                    """)
                    headline_values.append(value)
            # Aggiunta delle colonne headline nel SELECT
            if headline_parts:
                query += "\n" + ",\n".join(headline_parts) + ","
            query += " + ".join(app)
            app = list()
            query +=""" AS rank
            FROM dataset
            WHERE """
            for field, value, o in criteria:
                if field == "release_year":
                    if 'TO' in value:
                        app.append(f"""
                            {field} BETWEEN %s AND %s
                        """)
                        val = value.split(" TO ")
                        values.append(int(val[0][1:]))
                        values.append(int(val[1][:-1]))
                    else:
                        app.append(f"""
                            {field} {o} %s
                        """)
                        values.append(value)
                elif field == "average_rating":
                    if 'TO' in value:
                        app.append(f"""
                            ROUND({field}::numeric,1) BETWEEN %s AND %s
                        """)
                        val = value.split(" TO ")
                        values.append(int(val[0][1:]))
                        values.append(int(val[1][:-1]))
                    else:
                        app.append(f"""
                        ROUND({field}::numeric,1) {o} %s
                        """)
                        values.append(value)
                else:
                    ts_vector = SearchEngine.generate_ts_vector(field)
                    values.append(value)
                    app.append(f"""
                        {ts_vector} @@ {ts_query}
                    """)
            s = ""
            i = 0
            for a in app:
                s += a
                if i < len(operator):
                    s += f" {operator[i]} "
                i += 1
            query += f" {s}"
            query +=f"""
            ORDER BY rank DESC
            LIMIT 10;
            """
        # Inserisce prima i valori per ts_headline, poi gli altri
        final_values = headline_values + values

        print(query)
        print(f"Valori: {final_values}")
        return query, final_values

    @staticmethod
    def get_pairs(word):
        pairs = word.split(" ")
        opp = list()
        for i in range(len(pairs)):
            if "AND" in pairs[i] or "OR" in pairs[i]:
                if "NOT" in pairs[i+1]:
                    opp.append(pairs[i]+" " + pairs[i+1])
                else:
                    opp.append(pairs[i])

        pairs = list()
        app = word.split(" AND ")
        for a in app:
            if "OR" in a:
                app2 = a.split(" OR ")
                for b in app2:
                    pairs.append(b)
            elif "NOT" in a:
                pairs.append(a[4:])
            else:
                pairs.append(a)

        return pairs, opp