import os
import sys
import time
import pandas as pd
import json
import json
#Librerie per Postgres
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Postgres.database_config import DatabaseConfig
from Postgres.main_postgres import db_connection, close_connection, create_db, table_exists, create_table, control_popolate, popolate_table, index_exists, create_indexes
from Postgres.search_engine import SearchEngine
# Librerie per realizzzare i grafici
#import matplotlib.pyplot as plt
#import seaborn as sns

# Motore in Pylucene
from Pylucene.pylucene_IR import PyLuceneIR

def estrai_json():
    with open("Benchmark/Query per golden list.json", 'r') as file:
        dati = json.load(file)
    lista_valori = list(dati.values())
    return lista_valori

QUERY_LIST = estrai_json()

GOLDEN_RESULTS = [
    [],
    [],
    [],
    [],
    []
]

def benchmark_postgres():
    database = DatabaseConfig()
    conn = db_connection(database, False,False)
    motorone = SearchEngine(database, conn)
    results = list()
    print ("Inizio benchmark per Postgres...\n")
    for q in QUERY_LIST:
        tmp = motorone.tfidf_search(q)
        nuova_lista = list()
        for i in range(len(tmp)):
            nuova_lista.append(tmp[i][0])
        results.append(nuova_lista)
    for i in results:
        print(i)
        
    return results

def benchmark_pylucene():
    results_all = []
    for q in QUERY_LIST:
        if not q.strip():
            # Se la query è vuota, append una lista vuota
            results_all.append([])
        else:
            hits = PyLuceneIR.search_index(q, max_results=10, ranking_method="1")
            # Estraggo solamente l'intero "id" da ogni risultato, a fini di benchmarking
            ids = [doc["id"] for doc in hits]
            results_all.append(ids)
    return results_all    

def benchmark_whoosh():
    pass

# Creazione di tutte le formule per il confronto delle prestazioni

# Precision@5
def precision_at_k(results, k):
    return sum(1 for result in results if result in GOLDEN_RESULTS) / k
# Recall@5
def recall_at_k(results, k):
    return sum(1 for result in results if result in GOLDEN_RESULTS) / len(GOLDEN_RESULTS)  
# F1@5
def f1_at_k(precision, recall):
    if precision + recall == 0:
        return 0
    return 2 * (precision * recall) / (precision + recall)
# Average Precision
def average_precision(results):
    total_precision = 0
    for i, result in enumerate(results):
        if result in GOLDEN_RESULTS:
            total_precision += precision_at_k(results[:i + 1], i + 1)
    return total_precision / len(GOLDEN_RESULTS) if len(GOLDEN_RESULTS) > 0 else 0
# Mean Average Precision
def mean_average_precision(results_list):
    return sum(average_precision(results) for results in results_list) / len(results_list)

def main():
    bench_postgres = benchmark_postgres()       # Lista dei risultati per Postgres
    bench_pylucene = benchmark_pylucene()       # Lista dei risultati per Pylucene
    bench_whoosh = benchmark_whoosh()           # Lista dei risultati per Whoosh
    # Creazione del DataFrame per i risultati
    data = {
        "Engine": ["Postgres", "Pylucene", "Whoosh"],
        "Precision@5": [
            precision_at_k(bench_postgres, 5),
            #precision_at_k(bench_pylucene, 5),
            #precision_at_k(bench_whoosh, 5)
        ],
        "Recall@5": [
            recall_at_k(bench_postgres, 5),
            #recall_at_k(bench_pylucene, 5),
            #recall_at_k(bench_whoosh, 5)
        ],
        "F1@5": [
            #f1_at_k(data["Precision@5"][0], data["Recall@5"][0]),
            #f1_at_k(data["Precision@5"][1], data["Recall@5"][1]),
            #f1_at_k(data["Precision@5"][2], data["Recall@5"][2])
        ],
        "Average Precision": [
            average_precision(bench_postgres),
            #average_precision(bench_pylucene),
            #average_precision(bench_whoosh)
        ],
        "Mean Average Precision": mean_average_precision([bench_postgres])
    }

    #Stampa di questi risultati
    #df = pd.DataFrame(data) # Grazie al DataFrame possiamo visualizzare i risultati in modo tabellare
    #print("\nRisultati del benchmark:")
    #print(df)

if __name__ == "__main__":
    main()