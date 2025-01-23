import os
import yaml
from whoosh import index
from whoosh.qparser import MultifieldParser, OrGroup, QueryParser, AndGroup
from whoosh.scoring import BM25F

class IRModel:

    # Inizializzazione del modello
    def __init__(self, index_dir: str, weightingModel=BM25F):
        self.index_dir = index_dir
        self.model = weightingModel

        # Apertura dell'indice
        self.index = index.open_dir(self.index_dir)

    # Esecuzione effettiva della ricerca (max 10 risultati)
    def search(self, query: str, resLimit=10):
        # Parser per query booleane su più campi
        fields = ["title", "genres", "release_year", "average_rating", "type", "id", "processed_description"]
        parser = MultifieldParser(fields, schema=self.index.schema, group=OrGroup)

        # Parsing della query
        parsed_query = parser.parse(query)

        # Crea il searcher e esegui la ricerca
        searcher = self.index.searcher(weighting=self.model)
        results = searcher.search(parsed_query, limit=resLimit)

        # Costruisci un dizionario con i risultati
        res_dict = {}
        for hit in results:
            genres = hit['genres'].split(', ') if hit['genres'] else []

            res_dict[hit['id']] = {
                'id': hit['id'],
                'title': hit['title'],
                'release_year': hit['release_year'],
                'genres': genres,  # Assicurati che siano gestiti come lista di generi
                'average_rating': int(hit['average_rating']),  # Assicurati che 'average_rating' sia un intero
                'type': hit['type'],  # Campo 'type' aggiunto
                'description': hit['description']
            }

        # Chiudi il searcher
        searcher.close()

        return res_dict

if __name__ == '__main__':
    # Utilizza la configurazione presente nel file YAML
    with open('config.yaml', 'r') as file:
        config_data = yaml.safe_load(file)

    # Utilizza il percorso dell'indice presente nel file di configurazione
    index_dir = f"{config_data['INDEX']['MAINDIR']}/{config_data['INDEX']['ACCDIR']}"

    # Crea un'istanza del motore di ricerca
    ir_model = IRModel(index_dir)

    # Inserisci la tua query di ricerca
    user_query = input("Inserisci la query di ricerca: ")

    # Esegui la ricerca e recupera i risultati
    results = ir_model.search(user_query)

    # Stampa i risultati
    if results:
        print(f"\nRisultati trovati: {len(results)}\n")
        for i, (doc_id, doc_info) in enumerate(results.items(), start=1):
            print(f"Risultato {i}")
            print(f"ID: {doc_info['id']}")
            print(f"Title: {doc_info['title']}")
            print(f"Release Year: {doc_info['release_year']}")
            print(f"Average rating: {doc_info['average_rating']}")
            print(f"Genres: {', '.join(doc_info['genres'])}")
            print(f"Description: {doc_info['description']}")
            print(f"Type: {doc_info['type']}")
            print("-"*40)  
    else:
        print("Nessun documento trovato.")