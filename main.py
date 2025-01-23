# Librerie di sistema
import os
import zipfile
# Importazione di funzioni personali
from create_dataset import *

# Supponiamo che esista una cartella chiamata "Dataset"
path = "Dataset"
def download_dataset():
    if os.path.isdir(path):
        print(f"{path} è caricato.")
    elif os.path.exists(path+'.zip'):
        print(f"Estrazione del dataset...")
        # Apri il file ZIP e estrai tutto il suo contenuto nella directory di destinazione
        with zipfile.ZipFile(path+'.zip', 'r') as zip_ref:
            zip_ref.extractall()
        print (f"Dataset estratto")
    else:
        print(f"Inizio download del dataset")
        create()

# Funzione main
def main():
    download_dataset()

# Inizio programma
if __name__ == '__main__':
    main()