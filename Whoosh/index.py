import os
import json
import yaml
from whoosh.fields import Schema, TEXT, ID, NUMERIC, KEYWORD
from whoosh import index
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from whoosh.analysis import StandardAnalyzer
import nltk

# Scaricamento del dizionario di stopwords & di wordnet
nltk.download('stopwords')
nltk.download('wordnet')

# Pre-processing del campo "description"
def nltk_analyzer(text):
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(text.lower())  # indicizzazione case insensitive
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]  # eliminazione delle stopwords
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]  # operazione di lemmatizzazione
    return " ".join(tokens)  # unione di tutti i token ottenuti in un'unica stringa

def print_progress_bar(percentage):
    bar_length = 20
    filled_length = int(round(bar_length * percentage / 100))
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    print(f'\rProgresso: |{bar}| {percentage:.1f}% completato', end='', flush=True)

# Indicizzazione
class Index:

    # inizializzazione di schema + indice, chiamato quando si crea un nuovo index
    def __init__(self):
        self.schema = self.setupSchema()
        self.index = self.createIndex()

    # definisce la struttura dell'indice dei documenti che verranno indicizzati
    def setupSchema(self):
        schema = Schema(
            id=ID(stored=True, unique=True),
            title=TEXT(stored=True, field_boost=2.0), #il campo title ha più peso degli altri
            release_year=NUMERIC(stored=True, numtype=int),
            genres=KEYWORD(stored=True, commas=True), #i generi sono una lista di keywords, intervallati da virgole
            average_rating=NUMERIC(stored=True, numtype=float),
            description=TEXT(stored=True),  # descrizione non processata
            processed_description=TEXT(stored=True),  # campo per il testo pre-processato
            type=TEXT(stored=True)
        )
        return schema

    # definisce l'indice vero e proprio
    def createIndex(self):

        # lettura del file config.yaml
        with open('Whoosh/config.yaml', 'r') as file:
            config_data = yaml.safe_load(file)
        index_dir = os.path.join(config_data['INDEX']['MAINDIR'], config_data['INDEX']['ACCDIR'])
        data_dir = config_data['DATA']['DATADIR']

        # se la cartella indice non esiste, la crea passandogli lo schema
        if not os.path.exists(index_dir):
            os.makedirs(index_dir)
        ix = index.create_in(index_dir, self.schema)
        writer = ix.writer()

        # lettura e indicizzazione dei file JSON
        # Modifica SOLO questa sezione del codice:
# (dalla riga 76 alla 108 del metodo createIndex)

# lettura e indicizzazione dei file JSON
        json_files = os.listdir(data_dir)
        total_files = len(json_files)

        for i, jsonFile in enumerate(json_files):
            try:
                with open(os.path.join(data_dir, jsonFile), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # Calcola la percentuale
                    progress = (i + 1) / total_files * 100
                    print_progress_bar(progress)

                    # prepara il campo "generi" all'indicizzazione
                    genres_list = data.get("genres", [])  # Usa .get() per sicurezza
                    if not isinstance(genres_list, list):
                        genres_list = [genres_list]
                    normalized_genres = ",".join([str(genre).strip().lower() for genre in genres_list])
                    
                    # prepara il campo "description" all'indicizzazione
                    processed_description = nltk_analyzer(str(data.get("description", "")))

                    # Gestione release_year
                    release_year = data.get("release_year")
                    try:
                        release_year = int(release_year) if release_year else None
                    except (ValueError, TypeError):
                        release_year = None

                    # Costruisci il documento
                    doc_fields = {
                        "id": str(data.get("id", "")),
                        "title": str(data.get("title", "")),
                        "genres": normalized_genres,
                        "average_rating": int(data.get("average_rating", 0)),  # Usa 0 come default
                        "description": str(data.get("description", "")),
                        "processed_description": processed_description,
                        "type": str(data.get("type", ""))
                    }
                    if release_year is not None:
                        doc_fields["release_year"] = release_year

                    writer.add_document(**doc_fields)

            except Exception as e:
                print(f"\n⚠️ Errore in {jsonFile}: {str(e)}")

        # Sposta questi FUORI dal loop
        writer.commit()
        return ix

def main_whoosh_setup():
    print("Inizio indicizzazione con Whoosh...")
    return Index()

if __name__ == '__main__':
    main_whoosh_setup()