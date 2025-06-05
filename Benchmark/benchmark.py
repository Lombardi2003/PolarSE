import os
import time
import pandas as pd
import json
# Librerie per realizzzare i grafici
import matplotlib.pyplot as plt
import seaborn as sns

QUERY_LIST = [
    "",
    "",
    "",
    "",
    ""
]

GOLDEN_RESULTS = [
    [],
    [],
    [],
    [],
    []
]

def bench_postgres():
    pass

def bench_pylucene():
    pass

def bench_whoosh():
    pass

def main():
    bench_postgres = bench_postgres()       # Lista dei risultati per Postgres
    bench_pylucene = bench_pylucene()       # Lista dei risultati per Pylucene
    bench_whoosh = bench_whoosh()           # Lista dei risultati per Whoosh

if __name__ == "__main__":
    main()