# **🎬 PolarSE**

Benvenuto nel progetto di ricerca di film e serie TV, sviluppato come parte del corso di **Gestione dell'Informazione (Information Retrieval)** per l'anno accademico 2024/2025! 

Questo motore di ricerca consente di esplorare una vasta libreria di film e serie TV utilizzando i dati forniti da [**The Movie Database (TMDb)**](https://www.themoviedb.org/). È dotato di tre motori di ricerca, ognuno con due metodi di ranking personalizzati per migliorare l'esperienza di ricerca.

---

## 🧑‍💻 **Creato da:**
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
     - PyLucene e Whoosh utilizzano l'algoritmo BM25, uno dei metodi più efficaci per la rilevanza dei risultati nella ricerca testuale.
     - Postgres impiega un'emulazione di TF-IDF, un metodo basato sulla frequenza dei termini rispetto alla loro unicità nel corpus

  - **Alternate Ranking**:
     - Postgres utilizza BM25, ma in maniera inversa, basandosi sul ranking degli utenti di TMDb (average_rating), quindi favorendo i contenuti più apprezzati.
     - PyLucene e Whoosh, invece, adottano TF-IDF nel ranking alternativo, garantendo un criterio differente di classificazione rispetto al ranking predefinito.

---

## 📦 **Configurazioni**:
Per scaricare il progetto in locale, lanciare il comando:
```bash
   git clone https://github.com/Lombardi2003/PolarSE.git
   ```

All'interno del progetto è stato creato un file `requirements.txt`, che permette di scaricare in maniera automatizzata tutte le librerie e le dipendenze necessarie per il corretto funzionamento del programma
```bash
   pip install -r requirements.txt
   ```
Per avviare il programma occorre lanciare il file `main.py`
```bash
   python main.py
   ```
In caso di errori legati a NLTK in fase di avvio del main, è possibile risolvere lanciando i seguenti comandi (all'interno di una shell Python):
```bash
   >>> import nltk
   >>> nltk.download('stopwords')
   >>> nltk.download('punkt_tab')
   ```

### **PostgresSQL**
Per utilizzare il motore di ricerca **PostgreSQL**, è necessario avere un database PostgreSQL attivo.  
Nel progetto, **pgAdmin** viene utilizzato come interfaccia grafica per la gestione e il monitoraggio del database.

Assicurati di:
- Avere **PostgreSQL** installato e funzionante.
- Avere **pgAdmin** configurato per connettersi al tuo database.
- Verificare che le credenziali di accesso e le informazioni di rete corrispondano a quelle specificate nel file `postgres.json`

### **Whoosh**
L’indice Whoosh viene generato automaticamente all’avvio del programma, **non è necessario configurare nulla manualmente**.  
Assicurati solo che la directory dei file indicizzati sia scrivibile e che tutte le dipendenze Python siano installate correttamente (tramite `requirements.txt`).

### **Pylucene**

Durante la fase di sviluppo del progetto PolarSE, sono emerse alcune incompatibilità ambientali con PyLucene, soprattutto legate alla configurazione della JVM e alla compilazione delle librerie native. Per risolvere questi problemi e garantire un ambiente stabile e coerente su qualsiasi macchina, il progetto è stato completamente containerizzato.

L’utilizzo di Docker permette di avviare l'intero sistema — motori di ricerca, database e interfaccia — in maniera semplificata, senza dover gestire manualmente le dipendenze o configurare ambienti complessi.

Per eseguire PolarSE in Docker, segui questi passaggi:
1. **Scarica l’immagine Docker preconfigurata con PyLucene**:
   
    ```bash
       docker pull coady/pylucene
    ```
2. **Avvia un nuovo contenitore, montando il progetto all’interno:**

    ```bash
       docker run -it --name polar-se -v .:/workspace -w /workspace coady/pylucene bash
   ```
3. **Riavvia un contenitore già esistente:**
   
   ```bash
       docker start -ai polar-se
   ```
4. **Esegui il progetto all'interno del container. Una volta dentro il container:**
   
   ```bash
       cd /workspace
    ```
 
### 🛠️ **Configurazione della Connessione a PostgreSQL**

Se stai utilizzando Docker per eseguire l’applicazione, ma PostgreSQL è installato localmente sul tuo host, dovrai modificare la configurazione della connessione al database:

1. **Apri il file:**

   ```bash
       Postgres/Postgres.json
    ```
2. **Individua il campo:**

   ```bash
       "IP_ADDRESS": "127.0.0.1"
    ```
3. **Sostituiscilo con:**
 
   ```bash
       "IP_ADDRESS": "host.docker.internal"
    ```


> Questo cambiamento permette al container di connettersi correttamente al database PostgreSQL in esecuzione sull'host.

---
## 📊 **Benchmark**
Per il calcolo del benchmark è stato creato uno script [benchmark.py](Benchmark/benchmark.py), che esegue le stesse query su tutti i Search Engine e procede al confronto tramite delle funzioni che si occupano di confrontare le varie metriche di prestazione per i tre motori di ricerca. 
Per eseguire lo script bisogna eseguire il comando:

   ```bash
      cd Benchmark
      python benchmark.py
   ```
oppure anche

   ```bash
      python Benchmark/benchmark.py
   ```
Lo script restituirà 3 liste con gli *id* dei film che corrisponderano alle query testate e plotta dei grafici e tabelle nella cartella Benchmark/graphics, per aiutare a visualizzare a colpo d'occhio le metriche per ogni motore.

In benchmark.py si vanno a calcolare i seguenti parametri:
- `Precision@5`, che misura la frazione dei primi 5 risultati restituiti dal motore che sono rilevanti (cioè presenti nella golden list);
- `Recall@5`, che misura la frazione dei documenti rilevanti (golden list) che sono stati trovati nei primi k risultati;
- `F1@5`, che e la media armonica tra precision e recall. È utile quando si vuole un equilibrio tra i due;
- `Average precision`, che misura la precisione media al momento in cui ogni documento rilevante viene trovato. Tiene conto dell'ordine dei risultati. È più sofisticata di Precision@5;
- `Mean average precision`, che è la media di tutte le Average Precision calcolate su più query. Dà una misura complessiva dell’efficacia del motore

---
## 📝 **Informazioni aggiuntive**
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

## 🛠️ **Tecnologie Utilizzate**
- **Python** 🐍
- **TMDb API** 🎬
- **PostgreSQL** 🗃️
- **Lucene** 🔍
- **Whoosh** 🔍
