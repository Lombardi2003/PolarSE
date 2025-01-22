import lucene
from org.apache.lucene.store import FSDirectory
from org.apache.lucene.index import DirectoryReader
from java.nio.file import Paths

# Inizializza la JVM per Lucene
lucene.initVM(vmargs=['-Djava.awt.headless=true'])

def test_index(index_path):
    """
    Testa la creazione dell'indice Lucene.
    :param index_path: Percorso della directory dell'indice
    """
    # Apri l'indice
    directory = FSDirectory.open(Paths.get(index_path))
    reader = DirectoryReader.open(directory)

    # Conta il numero di documenti
    num_docs = reader.numDocs()
    print(f"Numero di documenti nell'indice: {num_docs}")

    # Chiudi il reader
    reader.close()

if __name__ == "__main__":
    # Percorso dell'indice
    INDEX_PATH = "lucene_index"
    test_index(INDEX_PATH)
