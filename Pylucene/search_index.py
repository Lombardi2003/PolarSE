import lucene
from org.apache.lucene.store import FSDirectory
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.search import IndexSearcher, BooleanQuery, BooleanClause, TermQuery
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import Term
from org.apache.lucene.document import IntPoint
from java.nio.file import Paths

# Inizializza la JVM
lucene.initVM(vmargs=['-Djava.awt.headless=true'])

def parse_numeric_query(field, value):
    """
    Gestisce query numeriche con operatori come >, <, >=, <=.
    :param field: Campo della query
    :param value: Valore della query
    :return: Una query Lucene per il campo numerico
    """
    max_value = 10 if field == "average_rating" else int(1e9)
    min_value = 0 if field == "average_rating" else int(-1e9)

    if value.startswith(">="):
        return IntPoint.newRangeQuery(field, max(min_value, int(value[2:])), max_value)
    elif value.startswith(">"):
        return IntPoint.newRangeQuery(field, max(min_value, int(value[1:]) + 1), max_value)
    elif value.startswith("<="):
        return IntPoint.newRangeQuery(field, min_value, min(max_value, int(value[2:])))
    elif value.startswith("<"):
        return IntPoint.newRangeQuery(field, min_value, min(max_value, int(value[1:]) - 1))
    else:  # Query esatta
        return IntPoint.newExactQuery(field, int(value))

def search_index(index_path, query_str, ranking="BM25", limit=10):
    """
    Cerca nell'indice Lucene utilizzando una query multi-campo.
    :param index_path: Percorso dell'indice
    :param query_str: Query inserita dall'utente
    :param ranking: Metodo di ranking ('BM25' o 'average_rating')
    :param limit: Numero massimo di risultati
    """
    # Apri l'indice
    directory = FSDirectory.open(Paths.get(index_path))
    reader = DirectoryReader.open(directory)
    searcher = IndexSearcher(reader)

    # Crea un analizzatore
    analyzer = StandardAnalyzer()

    # Campi principali per la ricerca testuale
    text_fields = ["title", "description", "genres", "type"]

    # Costruisci manualmente una query booleana
    boolean_query_builder = BooleanQuery.Builder()

    try:
        print("\nEseguendo parsing della query: " + query_str)
        terms = query_str.split(" AND ")  # Dividi i termini per "AND"

        for term in terms:
            if ":" in term:  # Termini specifici di campo (es. title:Nosferatu)
                field, value = term.split(":", 1)
                field = field.strip()
                value = value.strip()

                if field == "release_year" or field == "average_rating":  # Gestisce campi numerici
                    numeric_query = parse_numeric_query(field, value)
                    boolean_query_builder.add(
                        numeric_query,
                        BooleanClause.Occur.MUST
                    )
                elif field in text_fields:  # Per campi testuali come description
                    query_parser = QueryParser(field, analyzer)
                    text_query = query_parser.parse(value)
                    boolean_query_builder.add(
                        text_query,
                        BooleanClause.Occur.MUST
                    )
            else:  # Termini generici (senza specificare il campo)
                for field in text_fields:
                    boolean_query_builder.add(
                        TermQuery(Term(field, term.strip().lower())),
                        BooleanClause.Occur.SHOULD
                    )

        # Combina le sotto-query
        boolean_query = boolean_query_builder.build()
        print("Query costruita: " + str(boolean_query))

        # Esegui la ricerca
        hits = searcher.search(boolean_query, limit).scoreDocs

        # Gestisci il ranking basato sul metodo scelto
        if ranking == "average_rating":
            # Recupera i documenti e ordina per average_rating
            results = []
            for hit in hits:
                doc = searcher.storedFields().document(hit.doc)
                avg_rating = float(doc.get("average_rating") or 0)
                results.append((doc, avg_rating))
            results.sort(key=lambda x: x[1], reverse=True)  # Ordina per punteggio medio
        else:
            # Usa il ranking predefinito (BM25)
            results = [(searcher.storedFields().document(hit.doc), hit.score) for hit in hits]

        # Stampa i risultati
        print(f"\nRisultati trovati: {len(results)}\n")
        for i, (doc, score) in enumerate(results, start=1):
            result_type = doc.get('type')
            type_label = "[MOVIE]" if result_type and result_type.lower() == "movie" else "[TV SHOW]"
            print(f"Risultato {i}: {doc.get('title')} {type_label} \n")
            print(f"  Anno di uscita: {doc.get('release_year')}")
            print(f"  Genere: {doc.get('genres')}")
            print(f"  Descrizione (Inglese): {doc.get('description')}")
            if ranking == "average_rating":
                print(f"  Valutazione media degli utenti: {score}")
            else:
                print(f"  Punteggio BM25: {score}")
            print("-" * 40)

    except Exception as e:
        print(f"\nErrore durante la ricerca: {e}\n")

    finally:
        reader.close()

# Percorso principale dell'indice
INDEX_PATH = "lucene_index"

if __name__ == "__main__":
    # Richiedi la query e il metodo di ranking all'utente
    print("\nPuoi cercare su più campi! \n")
    print('  ESEMPIO: title:Sweethearts AND release_year:2024')
    print('           genres:Horror AND description:"vampire romance" AND release_year:[2000 TO 2024] AND average_rating:>8\n')
    search_query = input("\nINSERISCI LA QUERY: ").strip()
    print("\nSono disponibili 2 metodi di ranking: \n")
    print("  1. BM25 Similarity (Predefinito di PyLucene)")
    print("  2. 'dumb' Average Rating Ranking - dARR (Custom: in base alla valutazione media)\n")
    ranking_choice = input("INSERISCI IL NUMERO DEL MODELLO [1/2]: ").strip()
    ranking_method = "average_rating" if ranking_choice == "2" else "BM25"

    search_index(INDEX_PATH, search_query, ranking=ranking_method)
