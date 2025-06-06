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

def estrai_json():
    with open(os.path.dirname(".")+"Query per golden list.json", 'r') as file:
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
        if q == "":
            results.append(motorone.tfidf_search())
        else:
            results.append(motorone.tfidf_search(q))
    return results

def benchmark_pylucene():
    pass

def benchmark_whoosh():
    pass

def main():
    bench_postgres = benchmark_postgres()       # Lista dei risultati per Postgres
    bench_pylucene = benchmark_pylucene()       # Lista dei risultati per Pylucene
    bench_whoosh = benchmark_whoosh()           # Lista dei risultati per Whoosh

if __name__ == "__main__":
    main()