import os
import requests
import json
from tqdm import tqdm

# Configurazione
API_KEY = "b6a7a4090be318ff17964505db350975"
BASE_URL = "https://api.themoviedb.org/3"
TV_SHOWS_DIR = "tv_shows_dataset"  # Directory per salvare le serie TV

# Creazione della directory per salvare i file
os.makedirs(TV_SHOWS_DIR, exist_ok=True)

def fetch_tv_shows(page):
    """Scarica una lista di serie TV da TMDB."""
    url = f"{BASE_URL}/tv/popular"
    params = {
        "api_key": API_KEY,
        "language": "en-US",
        "page": page
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def fetch_tv_show_details(tv_id):
    """Ottiene i dettagli di una serie TV specifica."""
    url = f"{BASE_URL}/tv/{tv_id}"
    params = {
        "api_key": API_KEY,
        "language": "en-US"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def extract_relevant_fields(tv_details):
    """Estrae solo i campi richiesti dai dettagli di una serie TV."""
    release_date = tv_details.get("first_air_date", "")
    release_year = release_date[:4] if release_date else ""
    description = tv_details.get("overview", "")
    
    # Se l'anno è 2025 e la descrizione è vuota
    if release_year == "2025" and not description:
        description = "This content is coming soon."

    return {
        "id": tv_details.get("id"),
        "title": tv_details.get("name"),  # Nome della serie TV
        "release_year": release_year,     # Solo anno di uscita
        "genres": [genre["name"] for genre in tv_details.get("genres", [])],
        "average_rating": tv_details.get("vote_average"),
        "description": description,
        "type": "tv"  # Tipo fisso
    }

def save_tv_show_as_json(tv_show):
    """Salva i dettagli di una serie TV come file JSON."""
    tv_id = tv_show.get('id')
    if tv_id is None:
        print(f"ID mancante per la serie TV: {tv_show}")
        return
    file_path = os.path.join(TV_SHOWS_DIR, f"{tv_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(tv_show, f, indent=4)

def main():
    total_pages = 500  # TMDB permette un massimo di 500 pagine per endpoint
    tv_shows_saved = 0

    for page in tqdm(range(1, total_pages + 1)):
        try:
            data = fetch_tv_shows(page)
            for tv_show in data['results']:
                if 'id' not in tv_show:
                    print(f"ID mancante per la serie TV: {tv_show}")
                    continue

                # Ottieni i dettagli completi per ogni serie TV
                tv_details = fetch_tv_show_details(tv_show['id'])

                # Estrai solo i campi richiesti
                relevant_data = extract_relevant_fields(tv_details)

                # Salva la serie TV nei file JSON
                save_tv_show_as_json(relevant_data)
                tv_shows_saved += 1

        except Exception as e:
            print(f"Errore nella pagina {page}: {e}")

        # Interrompi se hai salvato abbastanza serie TV
        if tv_shows_saved >= 30000:
            break

    print(f"Dataset generato con {tv_shows_saved} serie TV salvate.")

if __name__ == "__main__":
    main()
