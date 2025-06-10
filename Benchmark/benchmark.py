# librerie di sistema
import os
import sys
import time
import pandas as pd
import json

# librerie per Postgres
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Postgres.database_config import DatabaseConfig
from Postgres.main_postgres import db_connection, close_connection, create_db, table_exists, create_table, control_popolate, popolate_table, index_exists, create_indexes
from Postgres.search_engine import SearchEngine

# librerie per realizzzare i grafici
import matplotlib.pyplot as plt
import seaborn as sns

# librerie per pylucene
from Pylucene.pylucene_IR import PyLuceneIR

# librerie per whoosh 
from Whoosh.IRmodel import IRModel
import yaml
from whoosh.scoring import BM25F

# definizione della lista di query usate
def estrai_json():
    with open("Benchmark/Query per golden list.json", 'r') as file:
        dati = json.load(file)
    lista_valori = list(dati.values())
    return lista_valori

QUERY_LIST = estrai_json()

# definizione delle liste di liste (golden, pg, pylucene, whoosh)

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

    return results

def benchmark_pylucene():
    print("Inizio benchmark per Pylucene...\n")
    results_all = []
    for q in QUERY_LIST:
        if not q.strip():
            results_all.append([])
        else:
            hits = PyLuceneIR.search_index(q, max_results=10, ranking_method="1")
            # Stampo a video quanti hit ho trovato (solo per debug):
            print(f"CIAO, SONO UN MESSAGGIO DI DEBUG: per query '{q}' ho ottenuto {len(hits)} hit da PyLucene.")

            ids = [doc["id"] for doc in hits]
            results_all.append(ids)  
    
    return results_all

def benchmark_whoosh():
    
    # inizializzo il motore whoosh
    with open('Whoosh/config.yaml', 'r') as file:
        config_data = yaml.safe_load(file)
    index_dir = f"{config_data['INDEX']['MAINDIR']}/{config_data['INDEX']['ACCDIR']}"
    ranking_model = BM25F

    # creo il motore whoosh
    whoosh_engine = IRModel(index_dir, weightingModel=ranking_model)
    print("Inizio benchmark per Whoosh...\n")

    # creo la lista di liste per i risultati
    results = []

    for q in QUERY_LIST:
        if q == "":
            search_results = whoosh_engine.search("", fuzzy=False)
        else:
            search_results = whoosh_engine.search(q, fuzzy=False)

        id_list = [int(id_str) for id_str in search_results.keys()]
        results.append(id_list)

    return results


# formule per il confronto di prestazioni

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

# calcolo dei parametri per ogni IR

def compute_metrics(bench_results, golden_results, engine_name, k=5):
    precisions = []
    recalls = []
    f1s = []
    aps = []

    for i in range(len(golden_results)):
        p = precision_at_k(bench_results[i], golden_results[i], k=k)
        r = recall_at_k(bench_results[i], golden_results[i], k=k)
        f1 = f1_at_k(p, r)
        ap = average_precision(bench_results[i], golden_results[i])

        precisions.append(p)
        recalls.append(r)
        f1s.append(f1)
        aps.append(ap)

    # Media dei valori
    precision_final = sum(precisions) / len(precisions)
    recall_final = sum(recalls) / len(recalls)
    f1_final = sum(f1s) / len(f1s)
    ap_final = sum(aps) / len(aps)
    map_final = mean_average_precision(bench_results, golden_results)

    # Stampa
    print(f"\n== {engine_name.upper()} RESULTS ==")
    print(f"Precision@{k}: {precision_final:.3f}")
    print(f"Recall@{k}: {recall_final:.3f}")
    print(f"F1@{k}: {f1_final:.3f}")
    print(f"Average Precision: {ap_final:.3f}")
    print(f"Mean Average Precision: {map_final:.3f}")

    # Ritorna i valori
    return precision_final, recall_final, f1_final, ap_final, map_final

# costruzione dei grafici

def plot_metrics(precision_postgres_final, recall_postgres_final, f1_postgres_final, ap_postgres_final, map_postgres_final,
                 precision_whoosh_final, recall_whoosh_final, f1_whoosh_final, ap_whoosh_final, map_whoosh_final,
                 precision_pylucene_final, recall_pylucene_final, f1_pylucene_final, ap_pylucene_final, map_pylucene_final):
    
    # Creo la cartella per le immagini
    graphics_dir = os.path.join("benchmark", "graphics")
    os.makedirs(graphics_dir, exist_ok=True)

    # Costruisco il DataFrame
    df = pd.DataFrame({
        'Engine': ['Postgres', 'Whoosh', 'Pylucene'],
        'Precision@5': [precision_postgres_final, precision_whoosh_final, precision_pylucene_final],
        'Recall@5': [recall_postgres_final, recall_whoosh_final, recall_pylucene_final],
        'F1@5': [f1_postgres_final, f1_whoosh_final, f1_pylucene_final],
        'Average Precision': [ap_postgres_final, ap_whoosh_final, ap_pylucene_final],
        'Mean Average Precision': [map_postgres_final, map_whoosh_final, map_pylucene_final]
    })

    print("\n=== DATAFRAME DELLE METRICHE ===")
    print(df)

    # GRAFICO GENERALE (confronto generico)
    df_plot = df.set_index('Engine').T
    df_plot.plot(kind='bar', figsize=(10, 6))
    plt.title('Confronto dei motori su tutte le metriche')
    plt.ylabel('Valore')
    plt.xlabel('Metriche')
    plt.legend(title='Motore di Ricerca')
    plt.grid(axis='y')
    plt.tight_layout()
    plt.savefig(os.path.join(graphics_dir, 'grafico_metriche_totali.png'))
    plt.close()

    # GRAFICI SINGOLI (per ogni parametro)
    metrics = ['Precision@5', 'Recall@5', 'F1@5', 'Average Precision', 'Mean Average Precision']

    for metric in metrics:
        plt.figure(figsize=(6,4))
        sns.barplot(x='Engine', y=metric, data=df)
        plt.title(f'Confronto dei motori: {metric}')
        plt.ylim(0, 1)
        plt.grid(axis='y')
        plt.tight_layout()
        plt.savefig(os.path.join(graphics_dir, f'grafico_{metric.replace(" ", "_")}.png'))
        plt.close()
    

def main():

    # creo una lista di liste di ID per ogni IR
    bench_postgres = benchmark_postgres()
    bench_pylucene = benchmark_pylucene()
    bench_whoosh = benchmark_whoosh()

    # stampa liste (ci serve solo per la golden list)
    print("\n== LISTA DI LISTE DI ID: POSTGRES ==")
    for i, query_results in enumerate(bench_postgres, start=1):
        print(f"Query {i}: {query_results}")

    print("\n== LISTA DI LISTE DI ID: PYLUCENE ==")
    for i, query_results in enumerate(bench_pylucene, start=1):
        print(f"Query {i}: {query_results}")

    print("\n== LISTA DI LISTE DI ID: WHOOSH ==")
    for i, query_results in enumerate(bench_whoosh, start=1):
      print(f"Query {i}: {query_results}")

    # calcolo ogni parametro per tutti e 3 gli IR
    precision_postgres_final, recall_postgres_final, f1_postgres_final, ap_postgres_final, map_postgres_final = compute_metrics(bench_postgres, GOLDEN_RESULTS, "Postgres")
    precision_whoosh_final, recall_whoosh_final, f1_whoosh_final, ap_whoosh_final, map_whoosh_final = compute_metrics(bench_whoosh, GOLDEN_RESULTS, "Whoosh")
    precision_pylucene_final, recall_pylucene_final, f1_pylucene_final, ap_pylucene_final, map_pylucene_final = compute_metrics(bench_pylucene, GOLDEN_RESULTS, "Pylucene")

    # costruzione dei grafici
    plot_metrics(precision_postgres_final, recall_postgres_final, f1_postgres_final, ap_postgres_final, map_postgres_final,
             precision_whoosh_final, recall_whoosh_final, f1_whoosh_final, ap_whoosh_final, map_whoosh_final,
             precision_pylucene_final, recall_pylucene_final, f1_pylucene_final, ap_pylucene_final, map_pylucene_final)

if __name__ == "__main__":
    main()