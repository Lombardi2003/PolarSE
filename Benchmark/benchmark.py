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
import matplotlib.pyplot as plt
import seaborn as sns

from Pylucene.pylucene_IR import PyLuceneIR

from Whoosh.IRmodel import IRModel
import yaml
from whoosh.scoring import BM25F

def estrai_json():
    with open("Benchmark/Query per golden list.json", 'r') as file:
        dati = json.load(file)
    lista_valori = list(dati.values())
    return lista_valori

QUERY_LIST = estrai_json()

GOLDEN_RESULTS = [
         [17406, 17774, 4314, 15304, 303, 13813, 14946, 18370, 19800, 6859],
         [197, 144, 93, 279, 182, 258, 160, 201, 8131, 1246],
         [181, 12920, 4990, 45, 12687, 6696, 13474, 6385, 6482, 16517],
         [10007, 10030, 10041, 10051, 10059, 10061, 10064, 10067, 10074, 10081],
         [1031, 1389, 1640, 1719, 2154, 2293, 2379, 2578, 2702, 2753],
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
    
    # Inizializza il motore Whoosh
    with open('Whoosh/config.yaml', 'r') as file:
        config_data = yaml.safe_load(file)
    index_dir = f"{config_data['INDEX']['MAINDIR']}/{config_data['INDEX']['ACCDIR']}"

    # Scegli il modello di ranking (BM25F per coerenza con Postgres tfidf_search)
    ranking_model = BM25F

    # Crea il motore Whoosh
    whoosh_engine = IRModel(index_dir, weightingModel=ranking_model)
    print("Inizio benchmark per Whoosh...\n")

    # Lista di liste per i risultati
    results = []

    # Per ogni query nella QUERY_LIST
    for q in QUERY_LIST:
        if q == "":
            search_results = whoosh_engine.search("", fuzzy=False)
        else:
            search_results = whoosh_engine.search(q, fuzzy=False)

        # Estrai SOLO gli ID dei risultati e mettili in una lista
        # Estrai SOLO gli ID dei risultati e converti in interi
        id_list = [int(id_str) for id_str in search_results.keys()]


        # Aggiungi la lista degli ID alla lista di liste dei risultati
        results.append(id_list)
    
    print("\nLISTA DI LISTE DI ID (Whoosh):")
    for i, query_results in enumerate(results, start=1):
        print(f"Query {i}: {query_results}")

    return results


# Creazione di tutte le formule per il confronto delle prestazioni

# Precision@5
def precision_at_k(results, golden, k):
    retrieved_k = results[:k]
    relevant_retrieved = [r for r in retrieved_k if r in golden]
    return len(relevant_retrieved) / k  

# Recall@5
def recall_at_k(results, golden, k):
    retrieved_k = results[:k]
    relevant_retrieved = [r for r in retrieved_k if r in golden]
    return len(relevant_retrieved) / len(golden) if golden else 0


# F1@5
def f1_at_k(precision, recall):
    if precision + recall == 0:
        return 0
    return 2 * (precision * recall) / (precision + recall)

# Average Precision
def average_precision(results, golden):
    if not golden:
        return 0
    
    total_precision = 0
    num_relevant = 0

    for i, r in enumerate(results):
        if r in golden:
            num_relevant += 1
            precision_at_i = num_relevant / (i + 1)
            total_precision += precision_at_i

    return total_precision / len(golden)

# Mean Average Precision
def mean_average_precision(results_list, golden_list):
    assert len(results_list) == len(golden_list)
    ap_list = []
    for results, golden in zip(results_list, golden_list):
        ap = average_precision(results, golden)
        ap_list.append(ap)
    return sum(ap_list) / len(ap_list) if ap_list else 0


def main():
    # Eseguiamo i benchmark dei motori:
    bench_postgres = benchmark_postgres()
    #bench_pylucene = benchmark_pylucene()
    bench_whoosh = benchmark_whoosh()

    # === POSTGRES ===
    precisions_postgres = []
    recalls_postgres = []
    f1s_postgres = []
    aps_postgres = []

    for i in range(len(GOLDEN_RESULTS)):
        p = precision_at_k(bench_postgres[i], GOLDEN_RESULTS[i], k=5)
        r = recall_at_k(bench_postgres[i], GOLDEN_RESULTS[i], k=5)
        f1 = f1_at_k(p, r)
        ap = average_precision(bench_postgres[i], GOLDEN_RESULTS[i])

        precisions_postgres.append(p)
        recalls_postgres.append(r)
        f1s_postgres.append(f1)
        aps_postgres.append(ap)

    # Calcoliamo i valori finali per Postgres:
    precision_postgres_final = sum(precisions_postgres) / len(precisions_postgres)
    recall_postgres_final = sum(recalls_postgres) / len(recalls_postgres)
    f1_postgres_final = sum(f1s_postgres) / len(f1s_postgres)
    ap_postgres_final = sum(aps_postgres) / len(aps_postgres)
    map_postgres_final = mean_average_precision(bench_postgres, GOLDEN_RESULTS)

    # STAMPA risultati per Postgres:
    print("\n== POSTGRES RESULTS ==")
    print(f"Precision@5: {precision_postgres_final:.3f}")
    print(f"Recall@5: {recall_postgres_final:.3f}")
    print(f"F1@5: {f1_postgres_final:.3f}")
    print(f"Average Precision: {ap_postgres_final:.3f}")
    print(f"Mean Average Precision: {map_postgres_final:.3f}")

    # === WHOOSH === (puoi fare LO STESSO ciclo per Whoosh!)
    precisions_whoosh = []
    recalls_whoosh = []
    f1s_whoosh = []
    aps_whoosh = []

    for i in range(len(GOLDEN_RESULTS)):
        p = precision_at_k(bench_whoosh[i], GOLDEN_RESULTS[i], k=5)
        r = recall_at_k(bench_whoosh[i], GOLDEN_RESULTS[i], k=5)
        f1 = f1_at_k(p, r)
        ap = average_precision(bench_whoosh[i], GOLDEN_RESULTS[i])

        precisions_whoosh.append(p)
        recalls_whoosh.append(r)
        f1s_whoosh.append(f1)
        aps_whoosh.append(ap)

    # Calcoliamo i valori finali per Whoosh:
    precision_whoosh_final = sum(precisions_whoosh) / len(precisions_whoosh)
    recall_whoosh_final = sum(recalls_whoosh) / len(recalls_whoosh)
    f1_whoosh_final = sum(f1s_whoosh) / len(f1s_whoosh)
    ap_whoosh_final = sum(aps_whoosh) / len(aps_whoosh)
    map_whoosh_final = mean_average_precision(bench_whoosh, GOLDEN_RESULTS)

    # STAMPA risultati per Whoosh:
    print("\n== WHOOSH RESULTS ==")
    print(f"Precision@5: {precision_whoosh_final:.3f}")
    print(f"Recall@5: {recall_whoosh_final:.3f}")
    print(f"F1@5: {f1_whoosh_final:.3f}")
    print(f"Average Precision: {ap_whoosh_final:.3f}")
    print(f"Mean Average Precision: {map_whoosh_final:.3f}")

    #Stampa di questi risultati
    #df = pd.DataFrame(data) # Grazie al DataFrame possiamo visualizzare i risultati in modo tabellare
    #print("\nRisultati del benchmark:")
    #print(df)

if __name__ == "__main__":
    main()