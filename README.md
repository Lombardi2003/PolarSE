# **Progetto-Gestione: Motore di Ricerca di Film e Serie TV**

Questo progetto è un motore di ricerca per film e serie TV basato sui dati forniti da [The Movie Database (TMDb)](https://www.themoviedb.org/). Consente di utilizzare tre diversi motori, ciascuno con due metodi di ranking.

---

## **Funzionalità Principali**

- **Dataset**: 
  - Include dettagli (in inglese) su film e serie TV, come: titolo, anno di uscita, descrizione, generi, valutazione media.
  - I dati vengono estratti da TMDb utilizzando la loro API.

- **3 Motori di Ricerca Disponibili**:
  1. **PostgreSQL**: Utilizza il database relazionale PostgreSQL per l'archiviazione e la ricerca;
  2. **PyLucene**: Utilizza l'implementazione di Lucene in Python per ricerche full-text;
  3. **Whoosh**: Utilizza la libreria nativa di Python.

- **2 Metodi di Ranking per Ogni Motore**:
  1. **Default Ranking**:
     - Il metodo di ranking predefinito del sistema (ad esempio, BM25 per PyLucene e Whoosh).
  2. **dARR: Dumb Average Rating Ranking**:
     - Ranking personalizzato basato sulle valutazioni medie (`average_rating`) fornite dagli utenti di TMDb.

---

## **Requisiti**

### **Librerie e Strumenti Necessari**
- **Python 3.8+**
- Librerie Python:
  - `lucene`
  - `whoosh`
  - `psycopg2`
  - `requests`
  - `tqdm`
- **PostgreSQL**:
  - ?????????????????????????

---

## **Istruzioni**
