# **Progetto-Gestione: Motore di Ricerca di Film e Serie TV**

Questo progetto è un motore di ricerca per film e serie TV basato sui dati forniti da [The Movie Database (TMDb)](https://www.themoviedb.org/). Consente di utilizzare tre diversi motori, ciascuno con due metodi di ranking. Creato per il corso di Gestione dell'informazione (Information Retrieval) nell'AA 2024/2025 da **INSERIRE MATRICOLE + NOMI E COGNOMI**

---

## **Funzionalità Principali**

- **Dataset**: 
  - Include dettagli (in inglese) su film e serie TV, come: titolo, anno di uscita, descrizione, generi, valutazione media.
  - I dati vengono estratti da TMDb utilizzando la loro API.

- **3 Motori di Ricerca Disponibili**:
  I. **PostgreSQL**: Utilizza il database relazionale PostgreSQL per l'archiviazione e la ricerca;
  II. **PyLucene**: Utilizza l'implementazione di Lucene in Python per ricerche full-text;
  III. **Whoosh**: Utilizza la libreria nativa di Python.

- **2 Metodi di Ranking per Ogni Motore**:
  I. **Default Ranking**:
     - Il metodo di ranking predefinito del sistema (ad esempio, BM25 per PyLucene e Whoosh).
  II. **dARR: Dumb Average Rating Ranking**:
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
