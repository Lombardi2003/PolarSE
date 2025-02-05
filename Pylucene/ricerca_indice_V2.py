import lucene
import os
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.store import FSDirectory
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.search import IndexSearcher, BooleanQuery, BooleanClause, TermQuery
from org.apache.lucene.index import Term
from org.apache.lucene.document import IntPoint
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search.similarities import BM25Similarity, ClassicSimilarity
from org.apache.lucene.search.spell import SpellChecker, LuceneDictionary

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Inizializza Lucene e NLTK
lucene.initVM(vmargs=['-Djava.awt.headless=true'])
nltk.data.path = ['/root/nltk_data']
stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()

def preprocess_query(query):
    """
    Preprocessa la query applicando tokenizzazione, rimozione delle stopwords e stemming.
    """
    tokens = word_tokenize(query.lower())
    processed_tokens = [stemmer.stem(word) for word in tokens if word.isalpha() and word not in stop_words]
    return " ".join(processed_tokens)

def parse_numeric_query(field, value):
    """
    Gestisce query numeriche con operatori <, >, <=, >= per release_year e average_rating.
    """
    try:
        if value.startswith(">="):
            return IntPoint.newRangeQuery(field, int(value[2:]), int(1e9))
        elif value.startswith(">"):
            return IntPoint.newRangeQuery(field, int(value[1:]) + 1, int(1e9))
        elif value.startswith("<="):
            return IntPoint.newRangeQuery(field, int(-1e9), int(value[2:]))
        elif value.startswith("<"):
            return IntPoint.newRangeQuery(field, int(-1e9), int(value[1:]) - 1)
        else:  # Query esatta
            return IntPoint.newExactQuery(field, int(value))
    except ValueError:
        return None

def search_index(query_str, base_index_path, ranking_method):
    """
    Esegue la ricerca nell'indice, corregge la query se necessario e applica il ranking scelto.
    """
    user_index_path = os.path.join(base_index_path, "userindex")
    index_dir = FSDirectory.open(Paths.get(user_index_path))
    searcher = IndexSearcher(DirectoryReader.open(index_dir))

    if ranking_method == "2":
        searcher.setSimilarity(ClassicSimilarity())
    else:
        searcher.setSimilarity(BM25Similarity())

    analyzer = StandardAnalyzer()

    # Costruisco la query finale
    boolean_query_builder = BooleanQuery.Builder()
    query_tokens = query_str.split(" AND ")

    # PRIMA: Aggiungo filtri numerici (FILTRANO I RISULTATI)
    numeric_queries = []
    text_queries = []

    for token in query_tokens:
        if ":" in token:
            field, value = token.split(":", 1)
            field, value = field.strip(), value.strip()

            if field in ["release_year", "average_rating"]:
                numeric_query = parse_numeric_query(field, value)
                if numeric_query:
                    numeric_queries.append(numeric_query)  # Aggiunge al filtro
            else:
                text_queries.append((field, value))
        else:
            text_queries.append(("default", token))  # Termini senza campo

    # CREO UN SOTTO-GRUPPO DI QUERY TESTUALI PER EVITARE L'OR ERRATO
    text_query_builder = BooleanQuery.Builder()

    # Aggiungo le query testuali (CERCANO I TERMINI)
    for field, value in text_queries:
        if field == "default":  # Termini senza campo specifico
            for search_field in ["processed_description", "title", "genres"]:
                parser = QueryParser(search_field, analyzer)
                field_query = parser.parse(value)
                text_query_builder.add(field_query, BooleanClause.Occur.SHOULD)
        else:
            parser = QueryParser(field, analyzer)
            field_query = parser.parse(value)
            text_query_builder.add(field_query, BooleanClause.Occur.SHOULD)

    # APPLICO I FILTRI NUMERICI PRIMA DELLE QUERY TESTUALI
    for nq in numeric_queries:
        boolean_query_builder.add(nq, BooleanClause.Occur.FILTER)

    # ORA AGGIUNGO LE QUERY TESTUALI COME UN BLOCCO UNICO
    boolean_query_builder.add(text_query_builder.build(), BooleanClause.Occur.MUST)

    final_query = boolean_query_builder.build()

    print(f"Eseguendo parsing della query: {query_str}")
    print(f"Query costruita: {final_query}")

    hits = searcher.search(final_query, 10).scoreDocs

    print(f"\nRisultati trovati: {len(hits)}\n")
    for i, hit in enumerate(hits, start=1):
        doc = searcher.storedFields().document(hit.doc)
        
        title = doc.get("title") or "Sconosciuto"
        release_year = doc.get("release_year") or "N/A"
        genres = doc.get("genres") or "N/A"
        description = doc.get("description") or "Nessuna descrizione disponibile"
        avg_rating = doc.get("average_rating") if doc.get("average_rating") else "N/A"
        content_type = doc.get("type").upper() if doc.get("type") else "UNKNOWN"

        print(f"RISULTATO {i}: {title} [{content_type}]")
        print(f"  ANNO DI USCITA: {release_year}")
        print(f"  GENERI: {genres}")
        print(f"  VALUTAZIONE MEDIA: {avg_rating}")
        print(f"  DESCRIZIONE: {description}")
        print("-" * 40)

if __name__ == "__main__":
    BASE_INDEX_PATH = "lucene_index"

    print("\nPuoi cercare con field specifici o solamente con keyword!")
    print("\n--- ESEMPIO CON FIELD: title:nosferatu AND release_year:2024")
    print("--- ESEMPIO SENZA FIELD: nosferatu drama")

    query = input("\nINSERISCI LA QUERY: ")
    
    print("\nSono disponibili 2 metodi di ranking:")
    print("  1. BM25 Similarity (Predefinito di PyLucene)")
    print("  2. TF-IDF (ClassicSimilarity)")

    ranking_choice = input("\nINSERISCI IL NUMERO DEL MODELLO [1/2]: ")
    
    search_index(query, BASE_INDEX_PATH, ranking_choice)
