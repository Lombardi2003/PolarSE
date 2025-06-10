from whoosh import index
from whoosh.qparser import MultifieldParser, AndGroup
from whoosh.query import NumericRange, FuzzyTerm, Or
from whoosh.scoring import BM25F, TF_IDF
import yaml

# Configurazione del motore 
class IRModel:

    # Inizializzazione del modello (indice, ranking)
    def __init__(self, index_dir: str, weightingModel):
        self.index_dir = index_dir
        self.model = weightingModel
        self.index = index.open_dir(self.index_dir)

    # Ricerca nel modello 
    def search(self, query: str, fuzzy=False):
        fields = ["title", "genres", "release_year", "average_rating", "type", "id", "processed_description"]
        parser = MultifieldParser(fields, schema=self.index.schema, group=AndGroup)

        if fuzzy:
            if ":" in query:
                field, term = query.split(":", 1)
                term = term.strip()
                parsed_query = FuzzyTerm(field, term, maxdist=2)
            else:
                parsed_query = Or([FuzzyTerm("title", query, maxdist=2), FuzzyTerm("description", query, maxdist=2)])
        else:
            if ":" in query:
                field, term = query.split(":", 1)
                term = term.strip()
                parsed_query = parser.parse(f"{field}:{term}")
            else:
                parsed_query = parser.parse(query)

        searcher = self.index.searcher(weighting=self.model)
        results = searcher.search(parsed_query, limit=10)

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

def main_whoosh():
    # apertura dell'indice
    with open('Whoosh/config.yaml', 'r') as file:
        config_data = yaml.safe_load(file)
    index_dir = f"{config_data['INDEX']['MAINDIR']}/{config_data['INDEX']['ACCDIR']}"

    # scelta del metodo di ranking
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
    
    # inizializzazione del modello 
    ir_model = IRModel(index_dir, weightingModel=ranking_model)

    # input della query
    user_query = input("Inserisci la query di ricerca: ")

    # se la query è di tipo title, description, o senza campi, chiede se voglio effettuare la fuzzy
    if (not any(field in user_query for field in ["title:", "description:", "genres:", "release_year:", "average_rating:", "type:", "id:", "processed_description:"]) or (user_query.startswith("title:")) or (user_query.startswith("description:")) ):
        print("Vuoi eseguire una ricerca fuzzy nei campi 'title' e 'description'? (s/n)")
        fuzzy_choice = input("Inserisci 's' per sì, 'n' per no: ").lower()
        fuzzy_search = (fuzzy_choice == 's') # è un'espressione booleana: se fuzzy_choiche == s allora si imposta automaticamente a true
    else:
        fuzzy_search = False

    # effettiva ricerca
    results = ir_model.search(user_query, fuzzy_search)

    # formattazione dei risultati
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


# Gestione dell'interfaccia utente
if __name__ == '__main__':

    main_whoosh()