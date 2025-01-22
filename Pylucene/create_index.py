import lucene
from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, TextField, StoredField, IntPoint
from org.apache.lucene.index import IndexWriter, IndexWriterConfig
from org.apache.lucene.store import FSDirectory
import os
import json
from glob import glob

# Inizializza la JVM per Lucene
lucene.initVM(vmargs=['-Djava.awt.headless=true'])

def create_index(dataset_path, index_path):
    # Crea la directory per l'indice
    index_dir = FSDirectory.open(Paths.get(index_path))
    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    writer = IndexWriter(index_dir, config)

    # Leggi i file JSON e aggiungili all'indice
    json_files = glob(os.path.join(dataset_path, "*.json"))

    for file in json_files:
        with open(file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)

                # Crea un documento Lucene per ogni file JSON
                doc = Document()
                doc.add(TextField("title", data.get("title", ""), Field.Store.YES))

                # Indicizza release_year come campo numerico
                release_year = data.get("release_year", None)
                if release_year:
                    try:
                        year = int(release_year)  # Converti in intero
                        doc.add(IntPoint("release_year", year))  # Campo per query numeriche
                        doc.add(StoredField("release_year", year))  # Campo memorizzato
                    except ValueError:
                        print(f"Valore non valido per release_year nel file {file}: {release_year}")

                # Indicizza average_rating come campo numerico
                average_rating = data.get("average_rating", None)
                if average_rating is not None:
                    try:
                        rating = int(float(average_rating)) # Converti in intero
                        doc.add(IntPoint("average_rating", rating))  # Campo per query numeriche
                        doc.add(StoredField("average_rating", rating))  # Campo memorizzato
                    except ValueError:
                        print(f"Valore non valido per average_rating nel file {file}: {average_rating}")

                doc.add(TextField("genres", ", ".join(data.get("genres", [])), Field.Store.YES))
                doc.add(TextField("description", data.get("description", ""), Field.Store.YES))
                doc.add(TextField("type", data["type"], Field.Store.YES))

                # Aggiungi il documento all'indice
                writer.addDocument(doc)

            except json.JSONDecodeError as e:
                print(f"Errore nella lettura del file {file}: {e}")

    # Chiudi il writer per salvare l'indice
    writer.close()
    print(f"Indice creato nella directory: {index_path}")

# Percorsi principali
DATASET_PATH = "dataset_film_serietv"  # Cartella con i file JSON
INDEX_PATH = "lucene_index"    # Cartella per salvare l'indice

if __name__ == "__main__":
    create_index(DATASET_PATH, INDEX_PATH)
