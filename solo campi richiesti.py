import os
import requests
import json
from tqdm import tqdm

# Configurazione
API_KEY = "b6a7a4090be318ff17964505db350975"
BASE_URL = "https://api.themoviedb.org/3"
MOVIES_DIR = "movies_dataset_gestione"  # Nuovo nome della cartella

# Creazione della directory per salvare i file
os.makedirs(MOVIES_DIR, exist_ok=True)

def fetch_movies(page):
    """Scarica una lista di film da TMDB."""
    url = f"{BASE_URL}/movie/popular"
    params = {
        "api_key": API_KEY,
        "language": "en-US",
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
        "language": "en-US"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def extract_relevant_fields(movie_details):
    """Estrae solo i campi richiesti dai dettagli di un film."""
    return {
        "id": movie_details.get("id"),
        "title": movie_details.get("title"),
        "release_year": movie_details.get("release_date", "")[:4],  # Solo anno
        "genres": [genre["name"] for genre in movie_details.get("genres", [])],
        "average_rating": movie_details.get("vote_average"),
        "num_votes": movie_details.get("vote_count"),
        "description": movie_details.get("overview")
    }

def save_movie_as_json(movie):
    """Salva i dettagli di un film come file JSON."""
    movie_id = movie.get('id')
    if movie_id is None:
        print(f"ID mancante per il film: {movie}")
        return
    file_path = os.path.join(MOVIES_DIR, f"{movie_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(movie, f, indent=4)

def main():
    total_pages = 500  # TMDB permette un massimo di 500 pagine per endpoint
    movies_saved = 0

    for page in tqdm(range(1, total_pages + 1)):
        try:
            data = fetch_movies(page)
            for movie in data['results']:
                if 'id' not in movie:
                    print(f"ID mancante per il film: {movie}")
                    continue

                # Ottieni i dettagli completi per ogni film
                movie_details = fetch_movie_details(movie['id'])

                # Estrai solo i campi richiesti
                relevant_data = extract_relevant_fields(movie_details)

                # Salva il film nei file JSON
                save_movie_as_json(relevant_data)
                movies_saved += 1

        except Exception as e:
            print(f"Errore nella pagina {page}: {e}")

        # Interrompi se hai salvato abbastanza film
        if movies_saved >= 30000:
            break

    print(f"Dataset generato con {movies_saved} film salvati.")

if __name__ == "__main__":
    main()
