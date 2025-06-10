# librerie di sistema
import os
import zipfile
from tqdm import tqdm
import nltk  
import time
import shutil

# Importiamo i 3 motori di ricerca (IR, cartella che contiene l'IR)
import Postgres.main_postgres
import Postgres 
from Postgres import *

import Pylucene.pylucene_IR
import Pylucene
from Pylucene.pylucene_IR import PyLuceneIR

import Whoosh.IRmodel
import Whoosh.index
import Whoosh
from Whoosh import *

# importo la creazione del dataset
from create_dataset import *

# Funzione che apre lo ZIP del dataset, estrae tutto il contenuto nella directory di destinazione
def download_dataset():
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

# Funzione che setuppa e indicizza i 3 motori
def setup():
    print("Setup in corso...")
    time.sleep(2) 
    os.system('cls' if os.name == 'nt' else 'clear')

    print("Postgres...")
    Postgres.main_postgres.setup_postgres()  # Chiama la funzione setup_postgres del modulo Postgres
    print("Postgres è stato setuppato correttamente!")
    time.sleep(2)  
    os.system('cls' if os.name == 'nt' else 'clear')

    print("Pylucene...")
    PyLuceneIR.create_index()  # Chiama la funzione create_index del modulo Pylucene
    print("\nPylucene è stato setuppato correttamente!")
    time.sleep(2)  
    os.system('cls' if os.name == 'nt' else 'clear')

    print("Whoosh...")
    i = Whoosh.index.main_whoosh_setup()  # Chiama la funzione main del modulo Whoosh
    print("\nWhoosh è stato setuppato correttamente!")
    time.sleep(2) 
    os.system('cls' if os.name == 'nt' else 'clear')

    print("Setup completato!")
    time.sleep(3)  # Attendi 3 secondi prima di pulire la console

# Chiamata dei 3 IR (in base al valore della scelta)

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
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    # Box con bordo e colori
    border = Fore.CYAN + "═" * 40
    empty_line = Fore.CYAN + "║" + " " * 38 + "║"
    print()
    print(border)
    print(empty_line)
    print(Fore.CYAN + "║" + Fore.YELLOW + Style.BRIGHT + "     🚪  Uscita dal programma...      " + Fore.CYAN + "║")
    print(Fore.CYAN + "║" + Fore.MAGENTA + Style.BRIGHT + "        👋  Arrivederc!!!!            " + Fore.CYAN + "║")
    print(empty_line)
    print(border)
    # Piccola pausa prima di pulire
    time.sleep(1.5)
    # Effetto "caricamento" con colori e emoji
    loading_msg = Fore.GREEN + Style.BRIGHT + "Sto chiudendo il programma "
    print("\n" + loading_msg, end="", flush=True)
    for i in range(3):
        print(Fore.GREEN + Style.BRIGHT + "🔒", end="", flush=True)
        time.sleep(0.7)
    print()
    # Pulizia console
    os.system('cls' if os.name == 'nt' else 'clear')
    exit()


search = [postgres,pylucene,whoosh,uscita]  # lista degli IR: è lui a chiamare le funzioni

# Funzione main
def main():
    nltk.download('stopwords') 
    nltk.download('punkt_tab')  # Scarica il pacchetto NLTK 
    os.system('cls' if os.name == 'nt' else 'clear') 

    #Scaricamento Dataset + setup 
    download_dataset()
    setup()
    os.system('cls' if os.name == 'nt' else 'clear') 

    # Corpo della scelta dell'IR
    terminal_width = shutil.get_terminal_size().columns
    titolo = "🦇 \033[1mBENVENUTO NEL PROGRAMMA DI GESTIONE DEL DATASET PER FILM E SERIE TV!!!\033[0m 🦇"
    print(titolo.center(terminal_width))
    while True:
        try:
            print("Scegli quale motore di ricerca vuoi utilizzare:")
            print("  \033[1;32m1\033[0m: \033[1mPostgres\033[0m")
            print("  \033[1;32m2\033[0m: \033[1mPylucene\033[0m")
            print("  \033[1;32m3\033[0m: \033[1mWhoosh\033[0m")
            print("  \033[1;32m4\033[0m: \033[1mEsci dal programma\033[0m")
            print("  \033[1;38;5;229m61016\033[0m: \033[1mUna sorpresa🎁\033[0m")
            choice = int(input("\033[1mInserisci la tua scelta\033[0m (1/2/3/4): "))
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
            print("\n\033[91mOPS! LA TUA SCELTA NON SEMBRA CORRETTA.\033[0m\n")

# Inizio programma
if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')  # Pulisce la console
    main()