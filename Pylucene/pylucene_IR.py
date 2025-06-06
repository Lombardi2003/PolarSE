# DESCRIZIONE: Script che gestisce l'intero motore creato in PyLucene
    # Crea un indice e cerca in PyLucene, da un dataset di film e serie TV in JSON.
    # Ordina con BM25, ma consente ranking TF-IDF.

import os
import json
import shutil
from glob import glob
import lucene
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, TextField, StoredField, IntPoint, StringField, DoublePoint
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, Term, DirectoryReader
from org.apache.lucene.store import FSDirectory
from org.apache.lucene.search import IndexSearcher, BooleanQuery, BooleanClause, TermQuery, PhraseQuery
from org.apache.lucene.search.similarities import BM25Similarity, ClassicSimilarity
from org.apache.lucene.search.spell import SpellChecker, LuceneDictionary

# NLTK per preprocessing testuale
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import shlex

# TQDM per mostrare la progress bar
from tqdm import tqdm

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
    DATASET_PATH = "Dataset"  # Qui ci sono i file JSON
    INDEX_PATH = "Pylucene/lucene_index"             # Cartella per gli indici
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
        

    #@staticmethod
    def create_index():
        PyLuceneIR.init_lucene()
        PyLuceneIR.prepare_index_dir()

        main_index_dir = FSDirectory.open(Paths.get(PyLuceneIR.MAIN_INDEX))
        main_analyzer = StandardAnalyzer()
        main_config = IndexWriterConfig(main_analyzer)
        main_writer = IndexWriter(main_index_dir, main_config)

        json_files = glob(os.path.join(PyLuceneIR.DATASET_PATH, "*.json"))
        if not json_files:
            print("Nessun file JSON trovato nel dataset")
            return

        # Inizializzazione progress bar
        progress_bar = tqdm(
            json_files,
            desc="Creazione indici",
            bar_format="{l_bar}{bar:40}| {n_fmt}/{total_fmt} | {postfix[0]}",
            postfix=["Inizio..."],
            dynamic_ncols=True,
            unit="film"
        )

        for file in progress_bar:
            with open(file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    print(f"\n Errore nel file {file}: {e}")
                    progress_bar.set_postfix_str("Errore in ultimo file!")
                    continue

                doc = Document()

                id = data.get("id")
                doc.add(StringField("id", id, Field.Store.YES))

                title = data.get("title", "Senza titolo")
                
                # Costruzione documento
                doc.add(TextField("title", title, Field.Store.YES))
                doc.add(TextField("processed_title", preprocess_text(title), Field.Store.NO))
                
                description = data.get("description", "")
                doc.add(TextField("description", description, Field.Store.YES))
                doc.add(TextField("processed_description", preprocess_text(description), Field.Store.NO))
                
                type_val = data.get("type", "UNKNOWN").lower()
                doc.add(StoredField("type", type_val))
                doc.add(StringField("type_txt", type_val, Field.Store.NO))
                
                genres = data.get("genres", [])
                genres_str = ", ".join(genres) if isinstance(genres, list) else str(genres)
                doc.add(StoredField("genres", genres_str))
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
                        doc.add(DoublePoint("average_rating", rating))
                        doc.add(StringField("average_rating_str", str(rating), Field.Store.NO))
                    except ValueError:
                        print(f"Valore non valido per average_rating in {file}: {average_rating}")

                main_writer.addDocument(doc)
                progress_bar.set_postfix_str(f"Ultimo: {title[:15] + '...' if len(title) > 15 else title}")

        progress_bar.close()
        main_writer.commit()
        main_writer.close()

        # Creazione indice spellchecker
        spell_dir = FSDirectory.open(Paths.get(PyLuceneIR.SPELLCHECKER_INDEX))
        spell_config = IndexWriterConfig(StandardAnalyzer())
        spell_checker = SpellChecker(spell_dir)
        
        reader = DirectoryReader.open(main_index_dir)
        spell_checker.indexDictionary(LuceneDictionary(reader, "genres_txt"), spell_config, True)
        
        reader.close()
        spell_checker.close()
        
        print("\n Indicizzazione completata con successo!")
        
    
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
                    choice = input(f"INTENDEVI '{field}:{suggestions[0]}' INVECE DI '{part}'? (s/n): ")
                    corrected = f"{field}:{suggestions[0]}" if choice.lower() == 's' else part
                    corrected_parts.append(corrected)
                else:
                    corrected_parts.append(part)
            else:
                suggestions = spell_checker.suggestSimilar(part, 1)
                if suggestions:
                    choice = input(f"INTENDEVI '{suggestions[0]}' INVECE DI '{part}'? (s/n): ")
                    corrected_parts.append(suggestions[0] if choice.lower() == 's' else part)
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
            # Riconosco operatori booleani esplicitamente
            if token.upper() in ("AND", "OR", "NOT"):
                if token.upper() == "AND":
                    current_operator = BooleanClause.Occur.MUST
                elif token.upper() == "OR":
                    current_operator = BooleanClause.Occur.SHOULD
                elif token.upper() == "NOT":
                    current_operator = BooleanClause.Occur.MUST_NOT
                continue

            subquery = None

            # Token del tipo campo:valore
            if ":" in token:
                field, value = token.split(":", 1)

                # Gestione type
                if field.lower() == "type":
                    value = value.lower()
                    if value not in ["movie", "tv"]:
                        print(f"Tipo non valido: {value}. Usa 'movie' o 'tv'")
                        continue
                    subquery = TermQuery(Term("type_txt", value))
                    # Aggiungo subito e passo al token successivo
                    occur = BooleanClause.Occur.SHOULD if (force_should and current_operator != BooleanClause.Occur.MUST_NOT) else current_operator
                    builder.add(subquery, occur)
                    continue

                if field.lower() == "release_year":
                    if value.isdigit():
                        num_val = int(value)
                        subquery = IntPoint.newRangeQuery("release_year", num_val, num_val)
                        occur = (BooleanClause.Occur.SHOULD 
                                if (force_should and current_operator != BooleanClause.Occur.MUST_NOT) 
                                else current_operator)
                        builder.add(subquery, occur)
                        continue

                if field.lower() == "average_rating":
                    # Provo un match esatto su float (es. "4.0" o "4")
                    try:
                        fval = float(value)
                        subquery = DoublePoint.newExactQuery("average_rating", fval)
                        occur = (BooleanClause.Occur.SHOULD 
                                if (force_should and current_operator != BooleanClause.Occur.MUST_NOT) 
                                else current_operator)
                        builder.add(subquery, occur)
                        continue
                    except ValueError:
                        # Non è un float esatto, passo alla gestione range
                        pass

                    # Gestione range su float (>=, >, <=, <)
                    if any(value.startswith(op) for op in (">=", ">", "<=", "<")):
                        op = value[:2] if value[:2] in (">=", "<=") else value[0]
                        raw = value[2:] if op in (">=", "<=") else value[1:]
                        try:
                            fval = float(raw)
                            if op == ">=":
                                subquery = DoublePoint.newRangeQuery("average_rating", fval, float("Infinity"))
                            elif op == ">":
                                import math
                                subquery = DoublePoint.newRangeQuery(
                                    "average_rating",
                                    math.nextafter(fval, float("inf")),
                                    float("Infinity")
                                )
                            elif op == "<=":
                                subquery = DoublePoint.newRangeQuery("average_rating", float("-Infinity"), fval)
                            elif op == "<":
                                import math
                                subquery = DoublePoint.newRangeQuery(
                                    "average_rating",
                                    float("-Infinity"),
                                    math.nextafter(fval, float("-inf"))
                                )
                        except ValueError:
                            subquery = None

                        if subquery is not None:
                            occur = (BooleanClause.Occur.SHOULD 
                                    if (force_should and current_operator != BooleanClause.Occur.MUST_NOT) 
                                    else current_operator)
                            builder.add(subquery, occur)
                        continue

                    # Se non è né un float né un range, ignoro il token
                    continue

                # Mappatura speciale per genres
                if field.lower() == "genres":
                    field = "genres_txt"

                # Gestione range numerico per NON float
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
                    # Term o frase in campo specifico
                    if value.startswith('"') and value.endswith('"'):
                        terms = value.strip('"').split()
                        term_builder = BooleanQuery.Builder()
                        for term in terms:
                            term_builder.add(TermQuery(Term(field, term.lower())), BooleanClause.Occur.MUST)
                        subquery = term_builder.build()
                    else:
                        subquery = TermQuery(Term(field, value.lower()))

            else:
                # Token generico: singolo termine o frase
                if token.startswith('"') and token.endswith('"'):
                    terms = token.strip('"').split()
                    combined_builder = BooleanQuery.Builder()

                    # processed_title
                    title_builder = BooleanQuery.Builder()
                    for term in terms:
                        title_builder.add(TermQuery(Term("processed_title", term.lower())), BooleanClause.Occur.MUST)
                    combined_builder.add(title_builder.build(), BooleanClause.Occur.SHOULD)

                    # processed_description
                    desc_builder = BooleanQuery.Builder()
                    for term in terms:
                        desc_builder.add(TermQuery(Term("processed_description", term.lower())), BooleanClause.Occur.MUST)
                    combined_builder.add(desc_builder.build(), BooleanClause.Occur.SHOULD)

                    # title NON processato
                    title_raw = BooleanQuery.Builder()
                    for term in terms:
                        title_raw.add(TermQuery(Term("title", term.lower())), BooleanClause.Occur.MUST)
                    combined_builder.add(title_raw.build(), BooleanClause.Occur.SHOULD)

                    # description NON processata
                    desc_raw = BooleanQuery.Builder()
                    for term in terms:
                        desc_raw.add(TermQuery(Term("description", term.lower())), BooleanClause.Occur.MUST)
                    combined_builder.add(desc_raw.build(), BooleanClause.Occur.SHOULD)

                    subquery = combined_builder.build()
                else:
                    # Singolo termine non in virgolette
                    combined_builder = BooleanQuery.Builder()
                    combined_builder.add(TermQuery(Term("processed_title", token.lower())), BooleanClause.Occur.SHOULD)
                    combined_builder.add(TermQuery(Term("processed_description", token.lower())), BooleanClause.Occur.SHOULD)
                    combined_builder.add(TermQuery(Term("title", token.lower())), BooleanClause.Occur.SHOULD)
                    combined_builder.add(TermQuery(Term("description", token.lower())), BooleanClause.Occur.SHOULD)
                    subquery = combined_builder.build()

            # Aggiungo la subquery al builder principale solo se non gestita sopra
            if subquery is not None:
                occur = BooleanClause.Occur.SHOULD if (force_should and current_operator != BooleanClause.Occur.MUST_NOT) else current_operator
                builder.add(subquery, occur)

        return builder.build()


    @staticmethod
    def search_index(query_str, max_results=10, ranking_method="1"):
        try:
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

                try:
                    # Recupero l'ID come intero nelle StoredField
                    docid = int(doc.get("id"))
                except Exception as e:
                    print(f"\n\033[91mErrore nel recupero dell'ID: {e}\033[0m")
                    continue
            
                results.append({
                    "id": docid,
                    "title": doc.get("title"),
                    "description": doc.get("description"),
                    "release_year": doc.get("release_year"),
                    "average_rating": doc.get("average_rating"),
                    "type": doc.get("type"),
                    "genres": doc.get("genres"),
                    "score": hit.score
                })

            reader.close()
            return results
        except Exception as e:
            print(f"\n\033[91mErrore durante la ricerca: {e}\033[0m")
            return []


    def main_pylucene():
        os.system('clear' if os.name == 'posix' else 'cls')

        #PyLuceneIR.create_index()
        
        original_query = input("\nINSERISCI LA QUERY DI RICERCA: ")
        corrected_query = PyLuceneIR.check_spelling(original_query)
        
        while True:
            print("\nSCEGLI IL METODO DI RANKING DEI RISULTATI:")
            ranking = input("1 BM25, predefinito di PyLucene\n2 TF-IDF, per confronto con PostgreSQL (1/2): ")
            
            if ranking in ('1', '2'):
                break
            print("\n\033[91mOPS! LA TUA SCELTA NON SEMBRA CORRETTA. DIGITA SOLAMENTE '1' O '2'.\033[0m\n")
        
        results = PyLuceneIR.search_index(corrected_query, ranking_method=ranking)
        
        for idx, doc in enumerate(results, 1):
            t = doc.get("type", "UNKNOWN")
            if t.lower() == "tv":
                type_str = "TV SHOW"
            elif t.lower() == "movie":
                type_str = "MOVIE"
            else:
                type_str = t.upper()
            print(f"\nRIS. {idx}: {doc['title']} [{type_str}]")
            print(f"ANNO DI USCITA: {doc['release_year']}")
            print(f"GENERI: {doc['genres']}")
            print(f"VALUTAZIONE MEDIA: {doc['average_rating']}")
            print(f"DESCRIZIONE (EN): {doc['description']}")
            print("*" * 40)


if __name__ == "__main__":
    PyLuceneIR.main_pylucene()