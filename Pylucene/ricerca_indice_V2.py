import lucene
import os
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.store import FSDirectory
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.search import IndexSearcher, BooleanQuery, BooleanClause
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search.similarities import BM25Similarity, ClassicSimilarity
from org.apache.lucene.search.spell import SpellChecker
from org.apache.lucene.search.spell import LuceneDictionary

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Inizializzo Lucene e NLTK
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

def suggest_correction(base_index_path, query_str):
    """
    Suggerisce correzioni ortografiche per ogni termine della query utilizzando l'indice del correttore.
    
    Viene costruito il percorso per il correttore a partire dalla directory base.
    """
    spellchecker_path = os.path.join(base_index_path, "correctindex")
    spell_index_dir = FSDirectory.open(Paths.get(spellchecker_path))
    spellchecker = SpellChecker(spell_index_dir)

    corrected_query_parts = []
    # Suddivido la query in token (in questo esempio una semplice suddivisione per spazio)
    query_tokens = query_str.split(" ")

    for token in query_tokens:
        if ":" in token:  # Caso in cui si specifichi il campo (es. "title:famuly")
            field, value = token.split(":", 1)
            field = field.strip()
            value = value.strip()
            suggestions = spellchecker.suggestSimilar(value, 1)  # Propongo una sola correzione
            # Se c'è una correzione (diversa dal termine attuale), la uso; altrimenti lascio il termine originale
            corrected_value = suggestions[0] if suggestions and suggestions[0].lower() != value.lower() else value
            corrected_query_parts.append(f"{field}:{corrected_value}")
        else:
            # Caso in cui il token non specifichi un campo
            suggestions = spellchecker.suggestSimilar(token.strip(), 1)
            corrected_query_parts.append(suggestions[0] if suggestions and suggestions[0].lower() != token.lower() else token)

    spellchecker.close()
    return " ".join(corrected_query_parts)

def search_index(query_str, base_index_path, ranking_method):
    """
    Esegue la ricerca nell'indice, corregge la query se necessario e applica il ranking scelto.
    
    Parametri:
      - query_str: query inserita dall'utente.
      - base_index_path: directory base degli indici (es. "lucene_index").
      - ranking_method: "1" per BM25 o "2" per TF-IDF (ClassicSimilarity).
    """
    # 1. Correzione ortografica
    corrected_query = suggest_correction(base_index_path, query_str)
    
    if corrected_query != query_str:
        print(f"\nQUERY ORIGINALE: {query_str}")
        print(f"Did you mean... {corrected_query}?")
        confirmation = input("Vuoi cercare con la query corretta? [y/n]: ").strip().lower()
        if confirmation == "y":
            query_str = corrected_query

    # 2. Apro l'indice principale (userindex)
    user_index_path = os.path.join(base_index_path, "userindex")
    index_dir = FSDirectory.open(Paths.get(user_index_path))
    searcher = IndexSearcher(DirectoryReader.open(index_dir))
    
    # Imposto il ranking in base alla scelta
    if ranking_method == "2":
        searcher.setSimilarity(ClassicSimilarity())
    else:
        searcher.setSimilarity(BM25Similarity())
    
    analyzer = StandardAnalyzer()

    # 3. Costruisco la query: se non specifica un campo, applico il preprocessamento e cerco su più campi
    if ":" not in query_str:
        print("\nLa query non specifica un campo. Applicando il preprocessamento con NLTK...\n")
        query_str = preprocess_query(query_str)
        fields = ["processed_description", "title", "genres"]
        boolean_query_builder = BooleanQuery.Builder()
        for field in fields:
            parser = QueryParser(field, analyzer)
            field_query = parser.parse(query_str)
            boolean_query_builder.add(field_query, BooleanClause.Occur.SHOULD)
        final_query = boolean_query_builder.build()
    else:
        # Se la query specifica i campi, uso un parser sul campo di default (ad es. processed_description)
        parser = QueryParser("processed_description", analyzer)
        final_query = parser.parse(query_str)

    print(f"Eseguendo parsing della query: {query_str}")
    print(f"Query costruita: {final_query}")

    # 4. Eseguo la ricerca
    hits = searcher.search(final_query, 10).scoreDocs

    # Se non ci sono risultati, provo a cercare sul campo "description" (non preprocessato)
    if not hits:
        print("\nNessun risultato trovato. Provo con il campo 'description' invece di 'processed_description'...\n")
        parser = QueryParser("description", analyzer)
        fallback_query = parser.parse(query_str)
        hits = searcher.search(fallback_query, 10).scoreDocs

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
    # Directory base degli indici: qui vengono creati "userindex" e "correctindex"
    BASE_INDEX_PATH = "lucene_index"

    print("\nPuoi cercare con field specifici o solamente con keyword!")
    print("\n--- ESEMPIO CON FIELD: title:famuly AND genres:hortor")
    print("--- ESEMPIO SENZA FIELD: nosferatu drama")
    query = input("\nINSERISCI LA QUERY: ")
    
    print("\nSono disponibili 2 metodi di ranking:")
    print("  1. BM25 Similarity (Predefinito di PyLucene)")
    print("  2. TF-IDF (ClassicSimilarity)")
    ranking_choice = input("\nINSERISCI IL NUMERO DEL MODELLO [1/2]: ")
    
    search_index(query, BASE_INDEX_PATH, ranking_choice)
