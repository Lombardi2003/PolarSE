#qua ho aggiornato tutto
from whoosh import index
from whoosh.qparser import MultifieldParser, AndGroup
from whoosh.query import Or, Term, NumericRange
from whoosh.scoring import BM25F, TF_IDF
from whoosh.fields import Schema, TEXT, NUMERIC
from whoosh.analysis import StandardAnalyzer
import yaml
from whoosh.query import FuzzyTerm  # Import per la ricerca fuzzy

class IRModel:
    def __init__(self, index_dir: str, weightingModel):
        self.index_dir = index_dir
        self.model = weightingModel
        self.index = index.open_dir(self.index_dir)

    def search(self, query: str, resLimit=10, fuzzy=False):
        # Definizione dei campi sui quali effettuare ricerche
        fields = ["title", "genres", "release_year", "average_rating", "type", "id", "processed_description"]

        # Configura il MultifieldParser con lo StandardAnalyzer
        parser = MultifieldParser(fields, schema=self.index.schema, group=AndGroup)

        # Controllo per operatori <, >, <=, >=
        operators = [">=", "<=", ">", "<"]
        for op in operators:
            if op in query:
                field, value = query.split(":", 1)  # Dividi il campo dal valore
                value = value.strip()  # Rimuovi eventuali spazi
                operator_pos = value.find(op)
                if operator_pos != -1:
                    op_value = float(value[operator_pos + len(op):])  # Ottieni il valore numerico
                    if field in ["release_year", "average_rating"]:
                        if op == ">":
                            parsed_query = NumericRange(field, op_value, None, startexcl=True)
                        elif op == ">=":
                            parsed_query = NumericRange(field, op_value, None, startexcl=False)
                        elif op == "<":
                            parsed_query = NumericRange(field, None, op_value, endexcl=True)
                        elif op == "<=":
                            parsed_query = NumericRange(field, None, op_value, endexcl=False)
                    else:
                        print(f"Campo {field} non valido per operatori numerici.")
                    break
        else:
            # Gestione delle range query con intervallo aperto
            if "[" in query and "]" in query:
                field, range_values = query.split(":", 1)
                range_values = range_values.strip("[]").split(" TO ")
                start_value = float(range_values[0]) if range_values[0] else None
                end_value = float(range_values[1]) if range_values[1] else None
                parsed_query = NumericRange(field, start_value, end_value)
            else:
                # Se non ci sono operatori, verifica se è una ricerca fuzzy
                if fuzzy:
                    field, term = query.split(":", 1)
                    term = term.strip()
                    # Applica FuzzyTerm al termine
                    parsed_query = FuzzyTerm(field, term, maxdist=2)  # maxdist controlla la similarità
                else:
                    parsed_query = parser.parse(query)

        # Crea il searcher per eseguire la ricerca
        searcher = self.index.searcher(weighting=self.model)
        results = searcher.search(parsed_query, limit=resLimit)

        # Debug: visualizza la query che viene eseguita
        print(f"Query finale eseguita: {parsed_query}")

        # Mette i risultati in un dizionario
        res_dict = {}
        for hit in results:
            genres = hit['genres'].split(', ') if hit['genres'] else []
            res_dict[hit['id']] = {
                'id': hit['id'],
                'title': hit['title'],
                'release_year': hit['release_year'],
                'genres': genres,
                'average_rating': int(hit['average_rating']),
                'type': hit['type'],
                'description': hit['description'],
                'score': hit.score,
            }

        searcher.close()
        return res_dict

if __name__ == '__main__':
    with open('config.yaml', 'r') as file:
        config_data = yaml.safe_load(file)

    index_dir = f"{config_data['INDEX']['MAINDIR']}/{config_data['INDEX']['ACCDIR']}"

    print("Scegli il metodo di ranking:")
    print("1. BM25 Similarity (predefinito)")
    print("2. TF-IDF")
    choice = input("Inserisci il numero della scelta: ")

    if choice == "1":
        ranking_model = BM25F
    elif choice == "2":
        ranking_model = TF_IDF
    else:
        print("Scelta non valida")
        exit(1)

    ir_model = IRModel(index_dir, weightingModel=ranking_model)

    user_query = input("Inserisci la query di ricerca (es. title:animale): ")

    if user_query.startswith("title:") or user_query.startswith("description:"):
        print("Vuoi eseguire una ricerca fuzzy? (s/n)")
        fuzzy_choice = input("Inserisci 's' per sì, 'n' per no: ").lower()
        fuzzy_search = fuzzy_choice == 's'
    else:
        fuzzy_search = False

    results = ir_model.search(user_query, fuzzy=fuzzy_search)

    if results:
        print(f"\nRisultati trovati: {len(results)}\n")
        for i, (doc_id, doc_info) in enumerate(results.items(), start=1):
            print(f"Risultato {i}")
            print(f"Punteggio di score per questo documento: {doc_info['score']:.4f}")
            print(f"ID: {doc_info['id']}")
            print(f"Title: {doc_info['title']}")
            print(f"Release Year: {doc_info['release_year']}")
            print(f"Average rating: {doc_info['average_rating']}")
            print(f"Genres: {', '.join(doc_info['genres'])}")
            print(f"Description: {doc_info['description']}")
            print(f"Type: {doc_info['type']}")
            print("-" * 40)
    else:
        print("Nessun documento trovato.")