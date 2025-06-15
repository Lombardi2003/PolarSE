
import json

# === CARICAMENTO FILE BENCHMARK ===
with open("bench_save.json", "r") as f:
    data = json.load(f)

bench_postgres = data["bench_postgres"]
bench_pylucene = data["bench_pylucene"]
bench_whoosh = data["bench_whoosh"]

# === GOLDEN LIST ===
GOLDEN_LIST = [
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

# === FUNZIONE AP ===
def average_precision(result, golden):
    total_precision = 0
    relevant_found = 0
    for i, r in enumerate(result):
        if r in golden:
            relevant_found += 1
            total_precision += relevant_found / (i + 1)
    return total_precision / len(golden) if golden else 0

def compute_ap_per_query(engine_results, golden_results):
    return [round(average_precision(engine_results[i], golden_results[i]), 2) for i in range(len(golden_results))]

# === CALCOLO AP PER OGNI MOTORE ===
ap_postgres = compute_ap_per_query(bench_postgres, GOLDEN_LIST)
ap_pylucene = compute_ap_per_query(bench_pylucene, GOLDEN_LIST)
ap_whoosh = compute_ap_per_query(bench_whoosh, GOLDEN_LIST)

# === STAMPA RISULTATI ===
print("Average Precision per motore:")
print(f"Postgres: {ap_postgres}")
print(f"Pylucene: {ap_pylucene}")
print(f"Whoosh:   {ap_whoosh}")
