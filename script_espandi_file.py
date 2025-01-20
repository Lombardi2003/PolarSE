import os
import requests
import json
from tqdm import tqdm

# Configurazione
API_KEY = "04878c2cc1d889a587277d56e95fb997"
BASE_URL = "https://api.themoviedb.org/3"
MOVIES_DIR = "movies_dataset_v2"  # Nome della cartella dove salvare i film


# Creazione della directory per salvare i file
os.makedirs(MOVIES_DIR, exist_ok=True)

def fetch_popular_movies(page):
    """Scarica una lista di film popolari in italiano da TMDB."""
    url = f"{BASE_URL}/movie/popular"
    params = {
        "api_key": API_KEY,
        "language": "it-IT",  # Ottieni film in italiano
        "page": page
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def fetch_movie_details(movie_id):
    """Ottiene i dettagli di un film specifico."""
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {
        "api_key": API_KEY,
        "language": "it-IT"  # Lingua italiana per i dettagli
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def save_movie_as_json(movie):
    """Salva i dettagli di un film come file JSON, se non è già presente."""
    movie_id = movie.get('id')  # Usa .get() per evitare KeyError se 'id' manca
    if movie_id is None:
        print(f"ID mancante per il film: {movie}")
        return
    file_path = os.path.join(MOVIES_DIR, f"{movie_id}.json")
    
    # Controlla se il file esiste già
    if os.path.exists(file_path):
        print(f"Film {movie_id} già salvato. Salto il download.")
        return

    # Salva il film nei file JSON
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(movie, f, indent=4)

def main():
    total_pages = 500  # TMDB permette un massimo di 500 pagine per endpoint
    movies_saved = 0

    for page in tqdm(range(1, total_pages + 1)):
        try:
            data = fetch_popular_movies(page)
            for movie in data['results']:
                # Controlla se 'id' è presente
                if 'id' not in movie:
                    print(f"ID mancante per il film: {movie}")
                    continue  # Salta il film se manca l'ID
                
                # Ottieni i dettagli completi per ogni film
                movie_details = fetch_movie_details(movie['id'])

                # Salva il film nei file JSON, solo se non è già presente
                save_movie_as_json(movie_details)
                movies_saved += 1

        except Exception as e:
            print(f"Errore nella pagina {page}: {e}")

        # Interrompi se hai salvato abbastanza film
        if movies_saved >= 30000:
            break

    print(f"Dataset generato con {movies_saved} film salvati.")

if __name__ == "__main__":
    main()
