"""
Questo programma utilizza l'API di The Movie Database (TMDB) per scaricare e salvare dettagli di film e serie TV popolari. 
Le principali funzionalità includono:
- Scaricare una lista di film e serie TV popolari.
- Estrarre solo i campi rilevanti per ciascun elemento, come titolo, anno di uscita, generi, valutazione media e descrizione.
- Salvare i dati estratti in file JSON all'interno di una cartella specificata.

L'obiettivo è creare un dataset organizzato per l'analisi o altre applicazioni.

Requisiti:
- Una chiave API valida per TMDB.
- La libreria `requests` per le chiamate API.
- La libreria `tqdm` per visualizzare una barra di avanzamento.

"""

import os
import requests
import json
from tqdm import tqdm

# Contatore per il nome dei file
c = 0

# Configurazione
API_KEY = "b6a7a4090be318ff17964505db350975"
BASE_URL = "https://api.themoviedb.org/3"
DIR = "Dataset"  # Nome della cartella

######## FUNZIONI PER LE LISTE DI ELEMENTI ########
# Funzione per scaricare una lista di film
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
# Funzione per scaricare una lista di serie tv
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

######## FUNZIONI PER L'ESTRAZIONE DEI DATI DEGLI ELEMENTI ########
# Funzione per l'estrazione dei dati dei film
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
# Funzione per l'estrazione dei dati delle serie tv
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

######## FUNZIONI PER L'ESTRAZIONE DEI FIELD DEGLI ELEMENTI ########
# Funzione per l'estrazione dei field necessari dei film
def extract_relevant_fields_film(movie_details):
    global c
    """Estrae solo i campi richiesti dai dettagli di un film."""
    release_year = movie_details.get("release_date", "")[:4]  # Solo anno
    description = movie_details.get("overview", "")
    #Controllo sulla descrizione - se l'anno è 2025
    if release_year == "2025" and not description:
        description = "This content is coming soon."
    elif not description:
        description = "No description available."
    #Contatore per l'id
    c += 1
    return {
        "id": str(c),
        "title": movie_details.get("title"),
        "release_year": release_year,
        "genres": [genre["name"] for genre in movie_details.get("genres", [])],
        "average_rating": movie_details.get("vote_average"),
        "description": description,
        "type": "movie"  # Tipo fisso
    }
# Funzione per l'estrazione dei field necessari delle serie
def extract_relevant_fields_series(series_details):
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

######## FUNZIONI PER IL SALVATAGGIO DEGLI ELEMENTI ########
# Funzione per il salvataggio dei film in un file Json
def save_json_film(movie):
    """Salva i dettagli di un film e serie tv come file JSON."""
    movie_id = movie.get('id')
    if movie_id is None:
        print(f"ID mancante per il film: {movie}")
        return
    file_path = os.path.join(DIR, f"{movie_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(movie, f, indent=4)
# Funzione per il salvataggio delle serie in un file Json
def save_series_as_json(series):
    """Salva i dettagli di una serie TV come file JSON."""
    series_id = series.get('id')
    if series_id is None:
        print(f"ID mancante per la serie TV: {series}")
        return
    file_path = os.path.join(DIR, f"{series_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(series, f, indent=4)

# Funzione per il download del dataset
def create():
    total_pages = 500  # TMDB permette un massimo di 500 pagine per endpoint
    movies_saved = 0
    series_saved = 0

    # Creazione della directory per salvare i file
    os.makedirs(DIR, exist_ok=True)

    print("Film:")
    # Ciclo per prendere tutti i film
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
                relevant_data = extract_relevant_fields_film(movie_details)
                # Salva il film nei file JSON
                save_json_film(relevant_data)
                movies_saved += 1
        except Exception as e:
            print(f"Errore nella pagina {page}: {e}")

    print("Serie TV:")
    # Ciclo per prendere tutti le serie tv
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
                relevant_data = extract_relevant_fields_series(series_details)
                # Salva la serie nei file JSON
                save_series_as_json(relevant_data)
                series_saved += 1
        except Exception as e:
            print(f"Errore nella pagina {page}: {e}")

    # Stampa della buona riuscita del download
    print(f"Dataset generato con {c} elementi, {movies_saved} filme e {series_saved} serie tv.")

# Inizio programma
if __name__ == '__main__':
    create()