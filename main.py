# Librerie di sistema
import os
import zipfile
from tqdm import tqdm  # Importiamo tqdm per la barra di avanzamento
import Postgres.main_postgres
from create_dataset import *
# Richiamo la cartellla Postgres per avviare il suo main
import Postgres  # Assicurati che il modulo postgres sia presente nella stessa directory
from Postgres import *

# Supponiamo che esista una cartella chiamata "Dataset"
PATH = "Dataset"
def postgres():
    print("Postgres è stato scelto come motore di ricerca.")
    Postgres.main_postgres.main_postgres() # Chiama la funzione main del modulo Postgres
def pylucene():
    print("Pylucene è stato scelto come motore di ricerca.")
def whoosh():
    print("Whoosh è stato scelto come motore di ricerca.")

search = [postgres,pylucene,whoosh,exit]  # Lista dei motori di ricerca disponibili

def download_dataset():# Apri il file ZIP e estrai tutto il suo contenuto nella directory di destinazione
    if os.path.isdir(PATH):
        print(f"{PATH} è caricato.")
    elif os.path.exists(PATH+'.zip'):
        print("Estrazione del dataset...")
        with zipfile.ZipFile(PATH+'.zip', 'r') as zip_ref:
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

def setup():
    print("Setup in corso...")
    print("Postgres...")
    print("Pylucene...")
    print("Whoosh...")
    print("Setup completato!")
    # Aspetto 3 secondi prima di pulire la console
    import time
    time.sleep(3)  # Attendi 3 secondi


# Funzione main
def main():
    download_dataset()
    setup()
    os.system('cls' if os.name == 'nt' else 'clear')  # Pulisce la console
    print("Benvenuto nel programma di gestione del dataset!")
    while True:
        print("Scegli quale motore di ricerca vuoi utilizzare:")
        print("1: Postgres")
        print("2: Pylucene")
        print("3: Whoosh")
        print("4: EXIT")
        choice = int(input("Inserisci la tua scelta (1/2/3): "))-1
        search[choice]()

# Inizio programma
if __name__ == '__main__':
    main()