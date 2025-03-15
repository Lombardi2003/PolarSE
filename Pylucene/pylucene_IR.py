# DESCRIZIONE: Script che gestisce l'intero motore creato in PyLucene
    # Crea un indice e cerca in PyLucene, da un dataset di film e serie TV in JSON.
    # Ordina con BM25, ma consente ranking personalizzabile!

import os
import json
import shutil
from glob import glob
import lucene
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, TextField, StoredField, IntPoint, StringField
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, Term, DirectoryReader
from org.apache.lucene.store import FSDirectory
from org.apache.lucene.search import IndexSearcher, BooleanQuery, BooleanClause, TermQuery, PhraseQuery
from org.apache.lucene.search.similarities import BM25Similarity, ClassicSimilarity
from org.apache.lucene.search.spell import SpellChecker, LuceneDictionary

# NLTK imports per preprocessing testuale
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import shlex

nltk.data.path = ['/root/nltk_data']
stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()

def preprocess_text(text):
    # Tokenizza, rimuove stopwords e applica lo stemming
    if not text:
        return ""
    tokens = word_tokenize(text.lower())
    processed_tokens = [stemmer.stem(token) for token in tokens if token.isalpha() and token not in stop_words]
    return " ".join(processed_tokens)

class PyLuceneIR:
    DATASET_PATH = "dataset_film_serietv"  # Qui ci sono i file JSON
    INDEX_PATH = "lucene_index"             # Cartella per gli indici
    MAIN_INDEX = os.path.join(INDEX_PATH, "mainindex")  # Sottocartella per l'indice di ricerca
    SPELLCHECKER_INDEX = os.path.join(INDEX_PATH, "spellchecker")  # Sottocartella per spell correction

    @staticmethod
    def init_lucene():
        # Inizializzo la JVM di Lucene SOLO SE non è già attiva
        if not lucene.getVMEnv():
            lucene.initVM(vmargs=['-Djava.awt.headless=true'])

    @staticmethod
    def prepare_index_dir():
        # Elimino l'indice esistente e creo le cartelle per il nuovo indice
        if os.path.exists(PyLuceneIR.INDEX_PATH):
            shutil.rmtree(PyLuceneIR.INDEX_PATH)
        os.makedirs(PyLuceneIR.MAIN_INDEX, exist_ok=True)
        os.makedirs(PyLuceneIR.SPELLCHECKER_INDEX, exist_ok=True)

    @staticmethod
    def create_index():
        PyLuceneIR.init_lucene()
        PyLuceneIR.prepare_index_dir()

        # Creazione indice principale
        main_index_dir = FSDirectory.open(Paths.get(PyLuceneIR.MAIN_INDEX))
        main_analyzer = StandardAnalyzer()
        main_config = IndexWriterConfig(main_analyzer)
        main_writer = IndexWriter(main_index_dir, main_config)

        json_files = glob(os.path.join(PyLuceneIR.DATASET_PATH, "*.json"))
        if not json_files:
            print("Nessun file JSON trovato nel dataset")
            return

        for file in json_files:
            with open(file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    print(f"Errore nel file {file}: {e}")
                    continue

                doc = Document()
                title = data.get("title", "")
                doc.add(TextField("title", title, Field.Store.YES))
                doc.add(TextField("processed_title", preprocess_text(title), Field.Store.NO))
                
                description = data.get("description", "")
                doc.add(TextField("description", description, Field.Store.YES))
                doc.add(TextField("processed_description", preprocess_text(description), Field.Store.NO))
                
                # Usa il campo "media_type" se presente, altrimenti "type"
                media_type = data.get("media_type", data.get("type", "UNKNOWN"))
                doc.add(StoredField("media_type", media_type))
                doc.add(TextField("media_type_txt", media_type, Field.Store.NO))
                
                genres = data.get("genres", [])
                genres_str = ", ".join(genres) if isinstance(genres, list) else str(genres)
                doc.add(StoredField("genres", genres_str))
                # Campo indicizzato per la ricerca sui generi
                doc.add(TextField("genres_txt", genres_str, Field.Store.NO))

                if release_year := data.get("release_year"):
                    try:
                        year = int(release_year)
                        doc.add(StoredField("release_year", str(year)))
                        doc.add(IntPoint("release_year", year))
                        doc.add(StringField("release_year_str", str(year), Field.Store.NO))
                    except ValueError:
                        print(f"Valore non valido per release_year in {file}: {release_year}")

                if average_rating := data.get("average_rating"):
                    try:
                        rating = float(average_rating)
                        doc.add(StoredField("average_rating", str(rating)))
                        doc.add(IntPoint("average_rating", int(rating)))
                        doc.add(StringField("average_rating_str", str(rating), Field.Store.NO))
                    except ValueError:
                        print(f"Valore non valido per average_rating in {file}: {average_rating}")

                main_writer.addDocument(doc)

        main_writer.commit()
        main_writer.close()

        # Creazione indice spellchecker
        spell_dir = FSDirectory.open(Paths.get(PyLuceneIR.SPELLCHECKER_INDEX))
        spell_config = IndexWriterConfig(StandardAnalyzer())
        spell_checker = SpellChecker(spell_dir)
        
        reader = DirectoryReader.open(main_index_dir)
        # Uso il campo indicizzato "genres_txt" per il dizionario dello spellchecker
        spell_checker.indexDictionary(LuceneDictionary(reader, "genres_txt"), spell_config, True)
        
        reader.close()
        spell_checker.close()

        print("Indici creati con successo")

    @staticmethod
    def check_spelling(query):
        PyLuceneIR.init_lucene()
        spell_dir = FSDirectory.open(Paths.get(PyLuceneIR.SPELLCHECKER_INDEX))
        spell_checker = SpellChecker(spell_dir)
        
        corrected_parts = []
        for part in query.split():
            if ':' in part:
                field, value = part.split(':', 1)
                suggestions = spell_checker.suggestSimilar(value, 1)
                if suggestions:
                    choice = input(f"Intendevi '{field}:{suggestions[0]}' invece di '{part}'? (y/n): ")
                    corrected = f"{field}:{suggestions[0]}" if choice.lower() == 'y' else part
                    corrected_parts.append(corrected)
                else:
                    corrected_parts.append(part)
            else:
                suggestions = spell_checker.suggestSimilar(part, 1)
                if suggestions:
                    choice = input(f"Intendevi '{suggestions[0]}' invece di '{part}'? (y/n): ")
                    corrected_parts.append(suggestions[0] if choice.lower() == 'y' else part)
                else:
                    corrected_parts.append(part)
        
        spell_checker.close()
        return ' '.join(corrected_parts)

    @staticmethod
    def build_query(query_str, analyzer):
        tokens = shlex.split(query_str)
        builder = BooleanQuery.Builder()
        # Se la query contiene " OR ", forzo tutte le clausole (eccetto NOT) ad essere SHOULD
        force_should = " OR " in query_str.upper()
        current_operator = BooleanClause.Occur.MUST

        for token in tokens:
            if token.upper() in ("AND", "OR", "NOT"):
                if token.upper() == "AND":
                    current_operator = BooleanClause.Occur.MUST
                elif token.upper() == "OR":
                    current_operator = BooleanClause.Occur.SHOULD
                elif token.upper() == "NOT":
                    current_operator = BooleanClause.Occur.MUST_NOT
                continue

            subquery = None

            if ":" in token:
                field, value = token.split(":", 1)
                # Se il campo è "genres", mappo su "genres_txt"
                if field.lower() == "genres":
                    field = "genres_txt"
                if any(value.startswith(op) for op in (">=", ">", "<=", "<")):
                    op = value[:2] if value[:2] in (">=", "<=") else value[0]
                    num_val = value[2:] if op in (">=", "<=") else value[1:]
                    try:
                        num_val = int(num_val)
                        if op == ">=":
                            subquery = IntPoint.newRangeQuery(field, num_val, 2147483647)
                        elif op == ">":
                            subquery = IntPoint.newRangeQuery(field, num_val + 1, 2147483647)
                        elif op == "<=":
                            subquery = IntPoint.newRangeQuery(field, -2147483648, num_val)
                        elif op == "<":
                            subquery = IntPoint.newRangeQuery(field, -2147483648, num_val - 1)
                    except ValueError:
                        pass
                else:
                    if value.startswith('"') and value.endswith('"'):
                        terms = value.strip('"').split()
                        term_builder = BooleanQuery.Builder()
                        for term in terms:
                            term_builder.add(TermQuery(Term(field, term.lower())), BooleanClause.Occur.MUST)
                        subquery = term_builder.build()
                    else:
                        subquery = TermQuery(Term(field, value.lower()))
            else:
                if token.startswith('"') and token.endswith('"'):
                    terms = token.strip('"').split()
                    combined_builder = BooleanQuery.Builder()
                    title_builder = BooleanQuery.Builder()
                    for term in terms:
                        title_builder.add(TermQuery(Term("title", term.lower())), BooleanClause.Occur.MUST)
                        title_builder.add(TermQuery(Term("processed_title", preprocess_text(term))), BooleanClause.Occur.MUST)
                    desc_builder = BooleanQuery.Builder()
                    for term in terms:
                        desc_builder.add(TermQuery(Term("description", term.lower())), BooleanClause.Occur.MUST)
                        desc_builder.add(TermQuery(Term("processed_description", preprocess_text(term))), BooleanClause.Occur.MUST)
                    combined_builder.add(title_builder.build(), BooleanClause.Occur.SHOULD)
                    combined_builder.add(desc_builder.build(), BooleanClause.Occur.SHOULD)
                    subquery = combined_builder.build()
                else:
                    subquery = TermQuery(Term("title", token.lower()))

            if subquery is not None:
                # Se force_should è vero e l'operatore corrente non è NOT, forzo l'uso di SHOULD
                if force_should and current_operator != BooleanClause.Occur.MUST_NOT:
                    builder.add(subquery, BooleanClause.Occur.SHOULD)
                else:
                    builder.add(subquery, current_operator)
            # Mantengo l'operatore corrente
        return builder.build()

    @staticmethod
    def search_index(query_str, max_results=10, ranking_method="1"):
        PyLuceneIR.init_lucene()
        index_dir = FSDirectory.open(Paths.get(PyLuceneIR.MAIN_INDEX))
        reader = DirectoryReader.open(index_dir)
        searcher = IndexSearcher(reader)
        analyzer = StandardAnalyzer()

        query = PyLuceneIR.build_query(query_str, analyzer)
        if ranking_method == "2":
            searcher.setSimilarity(ClassicSimilarity())
        else:
            searcher.setSimilarity(BM25Similarity())
        hits = searcher.search(query, max_results).scoreDocs
        results = []

        for hit in hits:
            doc = searcher.storedFields().document(hit.doc)
            results.append({
                "title": doc.get("title"),
                "description": doc.get("description"),
                "release_year": doc.get("release_year"),
                "average_rating": doc.get("average_rating"),
                "media_type": doc.get("media_type"),
                "genres": doc.get("genres"),
                "score": hit.score
            })

        reader.close()
        return results

if __name__ == "__main__":
    PyLuceneIR.create_index()
    
    original_query = input("Inserisci la query di ricerca: ")
    corrected_query = PyLuceneIR.check_spelling(original_query)
    
    print(f"\nEsecuzione ricerca con query: {corrected_query}")
    ranking = input("Scegli il ranking (1=BM25, 2=TFIDF): ")
    
    results = PyLuceneIR.search_index(corrected_query, ranking_method=ranking)
    
    for idx, doc in enumerate(results, 1):
        # Controllo il media_type: "tv" → "TV SHOW", "movie" → "MOVIE"
        media = doc.get("media_type", "UNKNOWN")
        if media.lower() == "tv":
            media_str = "TV SHOW"
        elif media.lower() == "movie":
            media_str = "MOVIE"
        else:
            media_str = media.upper()
        print(f"\nRIS. {idx}: {doc['title']} [{media_str}]")
        print(f"ANNO DI USCITA: {doc['release_year']}")
        print(f"GENERI: {doc['genres']}")
        print(f"VALUTAZIONE MEDIA: {doc['average_rating']}")
        print(f"DESCRIZIONE (EN): {doc['description']}")
        print("*" * 40)
