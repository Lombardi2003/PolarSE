# **🎬 Motore di Ricerca di Film e Serie TV**

Benvenuto nel progetto di ricerca di film e serie TV, sviluppato come parte del corso di **Gestione dell'Informazione (Information Retrieval)** per l'anno accademico 2024/2025! 

Questo motore di ricerca consente di esplorare una vasta libreria di film e serie TV utilizzando i dati forniti da [**The Movie Database (TMDb)**](https://www.themoviedb.org/). È dotato di tre motori di ricerca, ognuno con due metodi di ranking personalizzati per migliorare l'esperienza di ricerca.

---

### 🧑‍💻 **Creato da:**
- **Checola Francesca Rosa (MATR. 180957 -- 324595@studenti.unimore.it)**
- **Cocciardi Daniele Silvestro (MATR. 142029 -- 275438@studenti.unimore.it)**
- **Gnaccarini Susanna (MATR. 184144 -- 326451@studenti.unimore.it)** 
- **Lombardi Daniele (MATR. 180850 -- 324683@studenti.unimore.it)**

---

## 🚀 **Funzionalità Principali**

- **🎥 Dataset**:
  - Questo progetto include un vasto set di dati (in inglese) relativi a film e serie TV, contenenti informazioni dettagliate come titolo, anno di uscita, descrizione, generi e valutazione media.
  - I dati vengono recuperati direttamente dalla potente API di **TMDb**.

- **🔍 3 Motori di Ricerca Disponibili**:
  - **PostgreSQL**: Un potente motore di ricerca basato su un database relazionale, perfetto per ricerche rapide e strutturate.
  - **PyLucene**: Un'implementazione di Lucene in Python che consente ricerche full-text avanzate.
  - **Whoosh**: Una libreria Python nativa, leggera e facile da usare per ricerche full-text.

- **📊 2 Metodi di Ranking per Ogni Motore**:
  - **Default Ranking**:
     - Il metodo di ranking predefinito del sistema, che applica algoritmi come **BM25** per **PyLucene** e **Whoosh**, ottimizzando la rilevanza dei risultati.
  - **dARR (Dumb Average Rating Ranking)**:
     - Un metodo personalizzato che ordina i risultati in base alla **valutazione media** (`average_rating`) degli utenti di TMDb, offrendo una classifica dei film/serie più apprezzati.

---

## ⚙️ **Requisiti**

### 📦 **Librerie e Strumenti Necessari**:
- **Python 3.8+**
- Librerie Python:
  - `lucene` 🔍
  - `whoosh` 🔍
  - `NLTK` 🔍
  - `psycopg2` 🗃️
  - `requests` 🌐
  - `tqdm` ⏳
  
- **PostgreSQL**:
  - ?????????????????????????

---

## 📝 **Istruzioni**
All'avvio, il programma esegue i seguenti passaggi:
1. **Verifica della presenza del dataset**
   - Se il dataset è disponibile, procede con l'inizializzazione dei motori di ricerca.
   - Se il dataset non è presente, lo recupera dalla cartella appropriata.
   - Se la cartella non esiste, effettua automaticamente il download del dataset.
2. **Inizializzazione dei motori di ricerca**
   - Caricamento e configurazione di Postgres, Pylucene e Whoosh.
3. **Esecuzione delle query**
   - L'utente può interrogare i dati utilizzando uno dei tre motori di ricerca.

---

## 🛠️ **Tecnologie Utilizzate**:
- **Python** 🐍
- **TMDb API** 🎬
- **PostgreSQL** 🗃️
- **Lucene & Whoosh** 🔍

---

💬 Se hai domande, dubbi o hai bisogno di supporto, non esitare a **contattarci**! 💬
