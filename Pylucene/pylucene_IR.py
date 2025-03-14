# DESCRIZIONE: Script che gestisce l'intero motore creato in PyLucene

# Crea un indice e cerca in PyLucene, da un dataset di film e serie TV in JSON.

# Ordina con BM25, ma consente ranking personalizzabile!

# Librerie Python
import os
import json
import shutil
from glob import glob

#Librerie Lucene
import lucene
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, TextField, StoredField, IntPoint, StringField
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, Term
from org.apache.lucene.store import FSDirectory

#Librerie NLTK, per preprocessing testuale
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import shlex

# Libreria per i due ranking
from org.apache.lucene.search.similarities import BM25Similarity, ClassicSimilarity
from org.apache.lucene.search import BooleanQuery, BooleanClause, TermQuery, PhraseQuery

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
    DATASET_PATH = "dataset_film_serietv" # Qui ci sono i file JSON
    INDEX_PATH = "lucene_index" # Cartella per gli indici
    MAIN_INDEX = os.path.join(INDEX_PATH, "mainindex") # Sottocartella per l'indice di ricerca
    USER_INDEX = os.path.join(INDEX_PATH, "userindex") # Sottocartella per spelling correction

    @staticmethod
    def init_lucene():
        # Inizializza la JVM di Lucene SOLO SE non è già attiva
        if not lucene.getVMEnv():
            lucene.initVM(vmargs=['-Djava.awt.headless=true'])

    @staticmethod
    def prepare_index_dir():
        # Elimina l'indice esistente e crea le cartelle per il nuovo indice
        if os.path.exists(PyLuceneIR.INDEX_PATH):
            shutil.rmtree(PyLuceneIR.INDEX_PATH)
        os.makedirs(PyLuceneIR.MAIN_INDEX, exist_ok=True)

    @staticmethod
    def create_index():
        # Crea l'indice leggendo i file JSON e applicando il preprocessing
        PyLuceneIR.init_lucene()
        PyLuceneIR.prepare_index_dir()

        index_dir = FSDirectory.open(Paths.get(PyLuceneIR.MAIN_INDEX))
        analyzer = StandardAnalyzer()
        config = IndexWriterConfig(analyzer)
        writer = IndexWriter(index_dir, config)

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

                release_year = data.get("release_year", None)
                if release_year:
                    try:
                        year = int(release_year)
                        doc.add(StoredField("release_year", year))
                        doc.add(IntPoint("release_year", year))
                        doc.add(StringField("release_year_str", str(year), Field.Store.NO))
                    except ValueError:
                        print(f"Valore non valido per release_year in {file}: {release_year}")

                average_rating = data.get("average_rating", None)
                if average_rating:
                    try:
                        rating = int(float(average_rating))
                        doc.add(StoredField("average_rating", rating))
                        doc.add(IntPoint("average_rating", rating))
                        doc.add(StringField("average_rating_str", str(rating), Field.Store.NO))
                    except ValueError:
                        print(f"Valore non valido per average_rating in {file}: {average_rating}")

                writer.addDocument(doc)

        writer.commit()
        writer.close()
        print(f"Indice creato in: {PyLuceneIR.MAIN_INDEX}")

    @staticmethod
    def build_query(query_str, analyzer):
        # Costruisce una query Lucene a partire da una stringa in ingresso
        from org.apache.lucene.search import BooleanQuery, BooleanClause, TermQuery, PhraseQuery
        from org.apache.lucene.index import Term
        from org.apache.lucene.document import IntPoint

        tokens = shlex.split(query_str) # suddivide rispettando le virgolette
        builder = BooleanQuery.Builder()
        current_operator = BooleanClause.Occur.MUST # operatore di default

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

            # Se il token contiene ':' è una query su un campo specifico
            if ":" in token:
                field, value = token.split(":", 1)
                # Se il valore inizia con un operatore di range
                if value.startswith(">=") or value.startswith(">") or value.startswith("<=") or value.startswith("<"):
                    op = None
                    if value.startswith(">="):
                        op = ">="
                        num_val = value[2:]
                    elif value.startswith(">"):
                        op = ">"
                        num_val = value[1:]
                    elif value.startswith("<="):
                        op = "<="
                        num_val = value[2:]
                    elif value.startswith("<"):
                        op = "<"
                        num_val = value[1:]

                    try:
                        num_val = int(num_val)
                    except ValueError:
                        num_val = None

                    if num_val is not None:
                        if op in (">", ">="):
                            lower = num_val + (1 if op == ">" else 0)
                            upper = 2147483647
                        else:
                            lower = -2147483648
                            upper = num_val - (1 if op == "<" else 0)
                        
                        subquery = IntPoint.newRangeQuery(field, lower, upper)
                else:
                    # Per i campi testuali, miglioriamo la gestione
                    if field in ["title", "description"]:
                        # Creiamo un subbuilder per combinare le ricerche in campi preprocessati e normali
                        subbuilder = BooleanQuery.Builder()
                        
                        # Prima cerchiamo nel campo preprocessato
                        if value.startswith('"') and value.endswith('"'):
                            # Gestione delle frasi tra virgolette
                            phrase_text = value.strip('"')
                            processed_phrase = preprocess_text(phrase_text)
                            if processed_phrase:
                                terms = processed_phrase.split()
                                phrase_builder = PhraseQuery.Builder()
                                for pos, term in enumerate(terms):
                                    phrase_builder.add(Term(f"processed_{field}", term), pos)
                                subbuilder.add(phrase_builder.build(), BooleanClause.Occur.SHOULD)
                        else:
                            # Gestione dei termini semplici
                            processed_value = preprocess_text(value)
                            if processed_value:
                                for term in processed_value.split():
                                    subbuilder.add(TermQuery(Term(f"processed_{field}", term)), BooleanClause.Occur.SHOULD)
                        
                        # Poi cerchiamo anche nel campo originale per sicurezza
                        if value.startswith('"') and value.endswith('"'):
                            phrase_text = value.strip('"')
                            terms = phrase_text.lower().split()
                            phrase_builder = PhraseQuery.Builder()
                            for pos, term in enumerate(terms):
                                phrase_builder.add(Term(field, term), pos)
                            subbuilder.add(phrase_builder.build(), BooleanClause.Occur.SHOULD)
                        else:
                            for term in value.lower().split():
                                subbuilder.add(TermQuery(Term(field, term)), BooleanClause.Occur.SHOULD)
                        
                        subquery = subbuilder.build()
                    else:
                        # Per campi numerici
                        if field in ["release_year", "average_rating"]:
                            try:
                                int_value = int(value)
                                subquery = IntPoint.newExactQuery(field, int_value)
                            except ValueError:
                                # Fallback a ricerca per stringa
                                subquery = TermQuery(Term(f"{field}_str", value))
                        else:
                            # Per altri campi non testuali/numerici
                            subquery = TermQuery(Term(field, value))
            else:
                # Query senza campo specificato (cerca in campi testuali)
                if ">=" in token or ">" in token or "<=" in token or "<" in token:
                    op = None
                    field = None
                    if ">=" in token:
                        field, num_val = token.split(">=", 1)
                        op = ">="
                    elif ">" in token:
                        field, num_val = token.split(">", 1)
                        op = ">"
                    elif "<=" in token:
                        field, num_val = token.split("<=", 1)
                        op = "<="
                    elif "<" in token:
                        field, num_val = token.split("<", 1)
                        op = "<"

                    try:
                        num_val = int(num_val)
                    except ValueError:
                        num_val = None

                    if num_val is not None:
                        if op in (">", ">="):
                            lower = num_val + (1 if op == ">" else 0)
                            upper = 2147483647
                        else:
                            lower = -2147483648
                            upper = num_val - (1 if op == "<" else 0)
                        
                        subquery = IntPoint.newRangeQuery(field, lower, upper)
                else:
                    # Ricerca in tutti i campi testuali (prima preprocessati, poi originali)
                    text_builder = BooleanQuery.Builder()
                    
                    # Aggiunge query per i campi preprocessati
                    if token.startswith('"') and token.endswith('"'):
                        # Gestione delle frasi tra virgolette
                        phrase_text = token.strip('"')
                        processed_phrase = preprocess_text(phrase_text)
                        if processed_phrase:
                            terms = processed_phrase.split()
                            
                            for field in ["processed_title", "processed_description"]:
                                phrase_builder = PhraseQuery.Builder()
                                for pos, term in enumerate(terms):
                                    phrase_builder.add(Term(field, term), pos)
                                text_builder.add(phrase_builder.build(), BooleanClause.Occur.SHOULD)
                        
                        # Cerchiamo anche nei campi originali
                        terms = phrase_text.lower().split()
                        for field in ["title", "description"]:
                            phrase_builder = PhraseQuery.Builder()
                            for pos, term in enumerate(terms):
                                phrase_builder.add(Term(field, term), pos)
                            text_builder.add(phrase_builder.build(), BooleanClause.Occur.SHOULD)
                    else:
                        # Gestione termini singoli
                        processed_value = preprocess_text(token)
                        if processed_value:
                            for term in processed_value.split():
                                text_builder.add(TermQuery(Term("processed_title", term)), BooleanClause.Occur.SHOULD)
                                text_builder.add(TermQuery(Term("processed_description", term)), BooleanClause.Occur.SHOULD)
                        
                        # Cerchiamo anche nei campi originali
                        for term in token.lower().split():
                            text_builder.add(TermQuery(Term("title", term)), BooleanClause.Occur.SHOULD)
                            text_builder.add(TermQuery(Term("description", term)), BooleanClause.Occur.SHOULD)
                    
                    subquery = text_builder.build()

            if subquery is not None:
                builder.add(subquery, current_operator)
                current_operator = BooleanClause.Occur.MUST

        return builder.build()

    @staticmethod
    def search_index(query_str, max_results=10, ranking_method="1"):
        # Cerca nell'indice usando la query costruita e imposta il ranking in base al numero scelto
        from org.apache.lucene.index import DirectoryReader
        from org.apache.lucene.search import IndexSearcher

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
                "score": hit.score
            })

        reader.close()
        return results

if __name__ == "__main__":
    # Esegue l'indicizzazione e consente ricerche con ranking scelto tramite numero
    PyLuceneIR.create_index()
    query_input = input("Inserisci la query di ricerca: ")
    ranking_input = input("Inserisci il metodo di ranking (1 per BM25, 2 per TFIDF): ")
    risultati = PyLuceneIR.search_index(query_input, ranking_method=ranking_input)
    for idx, doc in enumerate(risultati, 1):
        print(f"Risultato {idx}: {doc}")
