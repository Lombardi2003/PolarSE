import lucene
from org.apache.lucene.store import FSDirectory
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.search import IndexSearcher, BooleanQuery, BooleanClause, TermQuery
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import Term
from org.apache.lucene.document import IntPoint
from org.apache.lucene.search.similarities import BM25Similarity, ClassicSimilarity
from org.apache.lucene.search.spell import SpellChecker
from org.apache.lucene.search.spell import LuceneDictionary
from java.nio.file import Paths

# Inizializzo la JVM
lucene.initVM(vmargs=['-Djava.awt.headless=true'])

def suggest_correction(correct_index_path, query_str):
    """
    Suggerisco correzioni per i termini di una query basandomi sull'indice del correttore.
    """
    spellchecker_dir = FSDirectory.open(Paths.get(correct_index_path))
    spellchecker = SpellChecker(spellchecker_dir)

    corrected_query = []
    terms = query_str.split(" AND ")  # Divido la query in base a "AND"

    for term in terms:
        if ":" in term:  # Gestisco termini specifici (es. title:nosferatu)
            field, value = term.split(":", 1)
            field = field.strip()
            value = value.strip()

            # Controllo se il termine è errato e suggerisco correzioni
            if not spellchecker.exist(value):
                suggestions = spellchecker.suggestSimilar(value, 1)  # Al massimo 1 suggerimento
                if suggestions:
                    corrected_query.append(f"{field}:{suggestions[0]}")
                else:
                    corrected_query.append(term)
            else:
                corrected_query.append(term)
        else:
            corrected_query.append(term)  # Termini non specifici di campo

    spellchecker.close()
    return " AND ".join(corrected_query)

def parse_numeric_query(field, value):
    """
    Gestisco query numeriche con operatori come >, <, >=, <= e range query [X TO Y].
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
    elif value.startswith("[") and value.endswith("]") and "TO" in value:
        # Gestione del range query [X TO Y]
        try:
            start, end = map(int, value.strip("[]").split(" TO "))
            return IntPoint.newRangeQuery(field, start, end)
        except ValueError:
            raise ValueError(f"Formato range query non valido: {value}")
    else:  # Query esatta
        return IntPoint.newExactQuery(field, int(value))

def search_index(index_path, query_str, ranking="BM25", limit=10):
    """
    Cerco nell'indice utilizzando il metodo di ranking specificato (BM25 o TF-IDF).
    """
    # Apro l'indice
    directory = FSDirectory.open(Paths.get(index_path))
    reader = DirectoryReader.open(directory)
    searcher = IndexSearcher(reader)

    # Configuro il ranking in base alla scelta dell'utente
    if ranking == "TFIDF":
        searcher.setSimilarity(ClassicSimilarity())  # TF-IDF (Classic in PyLucene)
    else:
        searcher.setSimilarity(BM25Similarity())

    # Costruisco la query booleana
    analyzer = StandardAnalyzer()
    boolean_query_builder = BooleanQuery.Builder()

    try:
        print("\nEseguendo parsing della query: " + query_str)
        terms = query_str.split(" AND ")  # Divido i termini con "AND"

        for term in terms:
            if ":" in term:  # Termini specifici di campo (es. title:Nosferatu)
                field, value = term.split(":", 1)
                field = field.strip()
                value = value.strip()

                if field == "release_year" or field == "average_rating":  # Gestisco campi numerici
                    numeric_query = parse_numeric_query(field, value)
                    boolean_query_builder.add(
                        numeric_query,
                        BooleanClause.Occur.MUST
                    )
                else:  # Per campi testuali come description
                    query_parser = QueryParser(field, analyzer)
                    text_query = query_parser.parse(value)
                    boolean_query_builder.add(
                        text_query,
                        BooleanClause.Occur.MUST
                    )
            else:  # Termini generici (senza specificare il campo)
                for field in ["processed_description", "title", "genres"]:
                    boolean_query_builder.add(
                        TermQuery(Term(field, term.strip().lower())),
                        BooleanClause.Occur.SHOULD
                    )

        # Combino le sotto-query
        boolean_query = boolean_query_builder.build()
        print("Query costruita: " + str(boolean_query))

        # Eseguo finalmente la ricerca
        hits = searcher.search(boolean_query, limit).scoreDocs

        # Stampo i risultati
        print(f"\nRisultati trovati: {len(hits)}\n")
        for i, hit in enumerate(hits, start=1):
            doc = searcher.storedFields().document(hit.doc)
            print(f"Risultato {i}: {doc.get('title')} [{doc.get('type')}]")
            print(f"  Anno di uscita: {doc.get('release_year')}")
            print(f"  Generi: {doc.get('genres')}")
            print(f"  Descrizione: {doc.get('description')}")
            print(f"  Similarità Calcolata: {hit.score}")
            print("-" * 40)

    except Exception as e:
        print(f"\nErrore durante la ricerca: {e}\n")

    finally:
        reader.close()

# Percorsi principali
INDEX_PATH = "lucene_index/userindex"
SPELLCHECKER_PATH = "lucene_index/correctindex"

if __name__ == "__main__":
    print("\nPuoi cercare su più campi! \n")
    print('  ESEMPIO: title:Sweethearts AND release_year:2024')
    print('           genres:Horror AND description:"vampire romance" AND release_year:[2000 TO 2024] AND average_rating:>8\n')
    search_query = input("\nINSERISCI LA QUERY: ").strip()

    # Suggerisco correzioni per la query
    corrected_query = suggest_correction(SPELLCHECKER_PATH, search_query)
    if corrected_query != search_query:
        print(f"\nHAI CERCATO '{search_query}', MA FORSE INTENDEVI '{corrected_query}'.")
        confirmation = input("ACCETTI LA CORREZIONE? [s/n]: ").strip().lower()
        if confirmation == "s":
            search_query = corrected_query

    print("\nSono disponibili 2 metodi di ranking: \n")
    print("  1. BM25 Similarity (Predefinito di PyLucene)")
    print("  2. TF-IDF (Per confronto con PostgreSQL)\n")
    ranking_choice = input("INSERISCI IL NUMERO DEL MODELLO [1/2]: ").strip()
    ranking_method = "TFIDF" if ranking_choice == "2" else "BM25"

    search_index(INDEX_PATH, search_query, ranking=ranking_method)
