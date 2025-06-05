# Librerie di sistema
import os
import zipfile
from tqdm import tqdm  # Importiamo tqdm per la barra di avanzamento
import Postgres.main_postgres
import Pylucene.pylucene_IR
import Whoosh.IRmodel
import Whoosh.index
from create_dataset import *
# Richiamo la cartellla Postgres per avviare il suo main
import Postgres  # Assicurati che il modulo postgres sia presente nella stessa directory
from Postgres import *

import Pylucene
from Pylucene.pylucene_IR import PyLuceneIR

import Whoosh
from Whoosh import *

import nltk  # Importa la libreria NLTK per il tokenizzatore
import time

# Supponiamo che esista una cartella chiamata "Dataset"
PATH = "Dataset"
def postgres():
    print("Postgres è stato scelto come motore di ricerca.")
    Postgres.main_postgres.main_postgres() # Chiama la funzione main del modulo Postgres
def pylucene():
    print("Pylucene è stato scelto come motore di ricerca.")
    PyLuceneIR.main_pylucene()  # Chiama la funzione main del modulo Pylucene
def whoosh():
    print("Whoosh è stato scelto come motore di ricerca.")
    Whoosh.IRmodel.main_whoosh()  # Chiama la funzione main del modulo Whoosh
def uscita():
    print("Uscita dal programma...")
    print("Arrivederci!")
    time.sleep(1)  # Attendi 1 secondo
    os.system('cls' if os.name == 'nt' else 'clear')  # Pulisce la console
    exit()  # Esce dal programma

search = [postgres,pylucene,whoosh,uscita]  # Lista dei motori di ricerca disponibili

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
    time.sleep(2)  # Attendi 3 secondi
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Postgres...")
    #Postgres.main_postgres.setup_postgres()  # Chiama la funzione setup_postgres del modulo Postgres
    print("Postgres è stato setuppato correttamente!")
    time.sleep(2)  # Attendi 3 secondi
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Pylucene...")
    #PyLuceneIR.create_index()  # Chiama la funzione create_index del modulo Pylucene
    print("\nPylucene è stato setuppato correttamente!")
    time.sleep(2)  # Attendi 3 secondi
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Whoosh...")
    #i = Whoosh.index.main_whoosh_setup()  # Chiama la funzione main del modulo Whoosh
    print("\nWhoosh è stato setuppato correttamente!")
    time.sleep(2)  # Attendi 3 secondi
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Setup completato!")
    # Aspetto 3 secondi prima di pulire la console
    time.sleep(3)  # Attendi 3 secondi


# Funzione main
def main():
    nltk.download('punkt_tab')  # Scarica il pacchetto NLTK per il tokenizzatore
    os.system('cls' if os.name == 'nt' else 'clear')
    download_dataset()
    #setup()
    os.system('cls' if os.name == 'nt' else 'clear')  # Pulisce la console
    print("BENVENUTO NEL PROGRAMMA DI GESTIONE DEL DATASET PER FILM E SERIE TV!")
    while True:
        try:
            print("Scegli quale motore di ricerca vuoi utilizzare:")
            print("1: Postgres")
            print("2: Pylucene")
            print("3: Whoosh")
            print("4: Esci dal programma")
            print("61016: Una sorpresa")
            choice = int(input("Inserisci la tua scelta (1/2/3/4): "))
            if choice==61016:
                os.system('cls' if os.name == 'nt' else 'clear')
                print("*" * 60)
                print("If you see something that doesn't look right,")
                print("Speak to staff or text police. 61016.")
                print("We'll sort it.\n")
                print("See it. Say it. Sorted!")
                print("*" * 60)
                time.sleep(6)  # Mostra l'easter egg per 6 secondi, poi ritorna al menu principale
                os.system('cls' if os.name == 'nt' else 'clear')  # Pulisce la console
            else:
                search[choice-1]()
        except Exception:
            print("\n\033[91mOPS! LA TUA SCELTA NON SEMBRA CORRETTA...\033[0m\n")

# Inizio programma
if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')  # Pulisce la console
    main()