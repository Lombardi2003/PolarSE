import os
import requests
import json
from tqdm import tqdm

c = 10000  # Inizio dell'ID

# Configurazione
API_KEY = "04878c2cc1d889a587277d56e95fb997" #Chiave della Susanna
BASE_URL = "https://api.themoviedb.org/3"
SERIES_DIR = "series_dataset_gestione"  # Nuovo nome della cartella

# Creazione della directory per salvare i file
os.makedirs(SERIES_DIR, exist_ok=True)

def fetch_series(page):
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

def fetch_series_details(series_id):
    """Ottiene i dettagli di una serie TV specifica."""
    url = f"{BASE_URL}/tv/{series_id}"
    params = {
        "api_key": API_KEY,
        "language": "en-US"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def extract_relevant_fields(series_details):
    global c
    """Estrae solo i campi richiesti dai dettagli di una serie TV."""
    release_year = series_details.get("first_air_date", "")[:4]  # Solo anno
    description = series_details.get("overview", "")
    # Controllo sulla descrizione - se l'anno è 2025
    if release_year == "2025" and not description:
        description = "This content is coming soon."
    elif not description:
        description = "No description available."
    # Contatore per l'id
    c += 1
    return {
        "id": str(c),
        "title": series_details.get("name"),
        "release_year": release_year,
        "genres": [genre["name"] for genre in series_details.get("genres", [])],
        "average_rating": series_details.get("vote_average"),
        "description": description,
        "type": "tv"  # Tipo fisso
    }

def save_series_as_json(series):
    """Salva i dettagli di una serie TV come file JSON."""
    series_id = series.get('id')
    if series_id is None:
        print(f"ID mancante per la serie TV: {series}")
        return
    file_path = os.path.join(SERIES_DIR, f"{series_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(series, f, indent=4)

def main():
    total_pages = 500  # TMDB permette un massimo di 500 pagine per endpoint
    series_saved = 0

    for page in tqdm(range(1, total_pages + 1)):
        try:
            data = fetch_series(page)
            for series in data['results']:
                if 'id' not in series:
                    print(f"ID mancante per la serie TV: {series}")
                    continue

                # Ottieni i dettagli completi per ogni serie TV
                series_details = fetch_series_details(series['id'])

                # Estrai solo i campi richiesti
                relevant_data = extract_relevant_fields(series_details)

                # Salva la serie nei file JSON
                save_series_as_json(relevant_data)
                series_saved += 1

        except Exception as e:
            print(f"Errore nella pagina {page}: {e}")

        # Interrompi se hai salvato abbastanza serie
        if series_saved >= 30000:
            break

    print(f"Dataset generato con {series_saved} serie TV salvate.")

if __name__ == "__main__":
    main()
