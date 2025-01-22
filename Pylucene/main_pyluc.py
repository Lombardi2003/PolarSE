import os
import sys
from contextlib import contextmanager

@contextmanager
def suppress_output():
    """Sopprime temporaneamente stdout e stderr."""
    with open(os.devnull, 'w') as fnull:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        try:
            sys.stdout = fnull
            sys.stderr = fnull
            yield
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr

def clear_terminal():
    """Pulisce il terminale."""
    os.system('cls' if os.name == 'nt' else 'clear')

def execute_script(script_name, suppress=True):
    """
    Esegue uno script Python direttamente sul terminale con opzione di soppressione.
    :param script_name: Nome dello script da eseguire.
    :param suppress: Se True, sopprime stdout e stderr.
    :return: True se l'esecuzione è riuscita, False altrimenti.
    """
    try:
        command = f"python {script_name}"
        if suppress:
            command += " > /dev/null 2>&1"  # Reindirizza stdout e stderr verso /dev/null
        exit_code = os.system(command)
        if exit_code == 0:
            return True
        else:
            print(f"\nErrore durante l'esecuzione di {script_name}.")
            return False
    except Exception as e:
        print(f"\nErrore: {e}")
        return False

def main():
    clear_terminal()
    print("Sto creando l'indice...\n")

    # Esegui create_index.py con soppressione dei warning
    if execute_script("create_index.py", suppress=True):
        print("\nIndice creato con successo. Ora eseguo il motore di ricerca...\n")
        # Esegui search_index.py con soppressione dei warning
        execute_script("search_index.py", suppress=False)
    else:
        print("\nErrore durante la creazione dell'indice. Interruzione del programma.")

if __name__ == "__main__":
    main()