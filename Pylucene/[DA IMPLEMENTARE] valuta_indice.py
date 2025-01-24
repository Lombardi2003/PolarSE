import lucene
from org.apache.lucene.store import FSDirectory
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.search.similarities import BM25Similarity
from java.nio.file import Paths

# Inizializzo la JVM
lucene.initVM(vmargs=['-Djava.awt.headless=true'])

def evaluate_precision(results, relevant_docs):
    """
    Calcolo della Precision per una query specifica.
    :param results: Lista di documenti restituiti dal motore di ricerca.
    :param relevant_docs: Set dei documenti rilevanti attesi (es. ID dei documenti).
    :return: Precision per la query.
    """
    if not results:
        return 0.0  # Precision è 0 se non ci sono risultati

    # Conteggio dei documenti rilevanti restituiti
    relevant_retrieved = sum(1 for doc in results if doc.get("id") in relevant_docs)
    precision = relevant_retrieved / len(results)
    return precision

def search_and_evaluate(index_path, query_examples):
    """
    Esegue la ricerca per ogni query e calcola precision e mean precision.
    :param index_path: Percorso dell'indice.
    :param query_examples: Lista di query e relativi documenti rilevanti.
    :return: Precision media.
    """
    precision_values = []

    # Apro l'indice
    directory = FSDirectory.open(Paths.get(index_path))
    reader = DirectoryReader.open(directory)
    searcher = IndexSearcher(reader)
    searcher.setSimilarity(BM25Similarity())  # Uso BM25 per il ranking

    # Crea un analizzatore
    analyzer = StandardAnalyzer()

    for example in query_examples:
        query_str = example["query"]
        relevant_docs = example["relevant_docs"]

        print(f"\nEseguo la query: {query_str}")

        # Costruisco la query
        query_parser = QueryParser("processed_description", analyzer)
        query = query_parser.parse(query_str)

        # Eseguo la ricerca
        hits = searcher.search(query, 10).scoreDocs
        results = [searcher.storedFields().document(hit.doc) for hit in hits]

        # Calcolo della precision per la query
        precision = evaluate_precision(results, relevant_docs)
        print(f"Precision per la query '{query_str}': {precision:.2f}")
        precision_values.append(precision)

    # Calcolo della Mean Precision
    mean_precision = sum(precision_values) / len(precision_values) if precision_values else 0
    print(f"\nMean Precision: {mean_precision:.2f}")

    reader.close()

    return mean_precision

if __name__ == "__main__":
    # Percorso dell'indice
    INDEX_PATH = "lucene_index/userindex"

    # Definizione delle query di esempio e dei documenti rilevanti
    query_examples = [
        {"query": "genres:Horror AND title:Dracula", "relevant_docs": {"1", "2"}},
        {"query": "title:Nosferatu", "relevant_docs": {"3"}},
        {"query": "release_year:[2000 TO 2020] AND genres:Action", "relevant_docs": {"5", "6"}}
    ]

    # Eseguo la valutazione
    search_and_evaluate(INDEX_PATH, query_examples)
