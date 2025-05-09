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
        with open('config.yaml', 'r') as file:
            config_data = yaml.safe_load(file)
        index_dir = os.path.join(config_data['INDEX']['MAINDIR'], config_data['INDEX']['ACCDIR'])
        data_dir = config_data['DATA']['DATADIR']

        # se la cartella indice non esiste, la crea passandogli lo schema
        if not os.path.exists(index_dir):
            os.makedirs(index_dir)
        ix = index.create_in(index_dir, self.schema)
        writer = ix.writer()

        # lettura e indicizzazione dei file JSON
        for i, jsonFile in enumerate(os.listdir(data_dir)):
            try:
                with open(os.path.join(data_dir, jsonFile), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    print(f"Indicizzando il file: {jsonFile}")

                    # prepara il campo "generi" all'indicizzazione
                    genres_list = data["genres"] if isinstance(data["genres"], list) else [data["genres"]]
                    normalized_genres = ",".join([genre.strip().lower() for genre in genres_list])
                    
                    # prepara il campo "description" all'indicizzazione
                    processed_description = nltk_analyzer(str(data["description"]))

                    # aggiunta del documento all'indice
                    writer.add_document(
                        id=str(data["id"]),
                        title=str(data["title"]),
                        release_year=int(data["release_year"]),
                        genres=normalized_genres,  # memorizzazione dei generi normalizzati
                        average_rating=int(data["average_rating"]),
                        description=str(data["description"]),  # memorizzazione del testo originale
                        processed_description=processed_description,  # memorizzazione del testo processato
                        type=str(data["type"])
                    )
            except Exception as e:
                print(f"Errore durante l'indicizzazione del file {jsonFile}: {e}")

        # il return della funzione è l'indice creato
        writer.commit()
        return ix

if __name__ == '__main__':
    my_index = Index()