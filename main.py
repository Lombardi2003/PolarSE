import os
from create_dataset import *


# Supponiamo che esista una cartella chiamata "Dataset"
path = "Dataset"
def download_dataset():
    if os.path.isdir(path):
        print(f"{path} è caricato.")
    else:
        print(f"Inizio download del dataset")
        create()

# Funzione main
def main():
    download_dataset()

# Inizio programma
if __name__ == '__main__':
    main()