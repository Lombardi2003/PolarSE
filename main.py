# Librerie di sistema
import os
import zipfile
from tqdm import tqdm  # Importiamo tqdm per la barra di avanzamento
# Importazione di funzioni personali
from create_dataset import *

# Supponiamo che esista una cartella chiamata "Dataset"
path = "Dataset"
def download_dataset():# Apri il file ZIP e estrai tutto il suo contenuto nella directory di destinazione
    if os.path.isdir(path):
        print(f"{path} è caricato.")
    elif os.path.exists(path+'.zip'):
        print("Estrazione del dataset...")
        with zipfile.ZipFile(path+'.zip', 'r') as zip_ref:
            # Otteniamo la lista dei file nello ZIP
            file_list = zip_ref.namelist()  # Otteniamo la lista dei file nello ZIP
            total_files = len(file_list)
            if total_files == 0:
                print("L'archivio ZIP è vuoto!")
                return
            # Usa tqdm per mostrare la barra di avanzamento
            with tqdm(total=total_files, desc="Estrazione file", unit="file") as pbar:
                for file in file_list:
                    zip_ref.extract(file)  # Estrai il file
                    pbar.update(1)  # Aggiorna la barra di avanzamento
        print("Dataset estratto con successo!")
    else:
        print(f"Inizio download del dataset")
        create()

# Funzione main
def main():
    download_dataset()

# Inizio programma
if __name__ == '__main__':
    main()