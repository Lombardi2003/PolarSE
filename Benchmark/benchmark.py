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
        [17406, 17774, 4314, 15304, 16005, 12156, 14946, 13813, 18370, 303],
        [144, 93, 197, 201, 1246, 279, 182, 258, 160, 201],
        [12687, 10777, 1788, 13474, 18132, 4332, 181, 18132, 4990, 19311],
        [10007, 10030, 10041, 10120, 10040, 10108, 11256, 12247, 12620, 13217],
        [17794, 6427, 9473, 1031, 1389, 1640, 10198, 10334, 10443, 10527],
        [10841, 13903, 17477, 10933, 16881, 18352, 16881, 17346, 18418, 12005],
        [1002, 10049, 10068, 10689, 1080, 11430, 12678, 1638, 18796, 19542],
        [702, 189, 567, 2303, 2868, 1300, 1414, 15377, 15997, 4944],
        [18453, 11139, 16745, 8212, 8520, 19054, 8941, 17732, 19149, 1014],
        [19851, 6410, 5304, 16788, 4807, 4490, 8946, 18633, 5032, 5350]
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

    # TABELLA (con formattazione decimale)
    df_formatted = df.copy()
    for col in df.columns[1:]: 
        df_formatted[col] = df[col].apply(lambda x: f"{x:.2f}")

    fig, ax = plt.subplots(figsize=(12, 3))
    ax.axis('off')

    table = ax.table(cellText=df_formatted.values,
                    colLabels=df_formatted.columns,
                    cellLoc='center',
                    loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.3, 1.8)

    for (row, col), cell in table.get_celld().items():
        cell.set_linewidth(1)
        cell.set_edgecolor("black")
        if row == 0: 
            cell.set_text_props(weight='bold', color='black')
            cell.set_facecolor('#e6e6e6')  
        
    plt.tight_layout()
    plt.savefig(os.path.join(graphics_dir, 'tabella_metriche.png'))
    plt.close()

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
    
def save_benchmark(bench_postgres, bench_pylucene, bench_whoosh):
    # Creo un dizionario strutturato con nomi chiari
    data = {
        "bench_postgres": bench_postgres,
        "bench_pylucene": bench_pylucene,
        "bench_whoosh": bench_whoosh
    }

    # Salvo in formato JSON ben formattato
    with open('Benchmark/bench_save.json', 'w') as f:
        json.dump(data, f, indent=4)

def main():
    # Creo una lista di liste di ID per ogni IR
    bench_postgres = benchmark_postgres()
    bench_pylucene = benchmark_pylucene()
    bench_whoosh = benchmark_whoosh()

    print("I risultati sono stati ottenuti con successo per tutti i motori di ricerca e sono stati salvati correttamente.\n")
    save_benchmark(bench_postgres, bench_pylucene, bench_whoosh)

    print("\n== LISTA DI LISTE DI GOLDEN LIST")
    for i, query_results in enumerate(GOLDEN_RESULTS, start=1):
        print(f"Query {i}: {query_results}")

    # Stampa liste (ci serve solo per la golden list)
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