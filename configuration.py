from pathlib import Path

# Paths
BASE_DIR = (Path(__file__).parent).resolve()
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"
TEMP_DIR = BASE_DIR / "temp"

# FILE_PURCHASES_N26 = "n26_compras.json"
# FILE_SALES_EARNINGS_N26 = "n26_ventas_con_ganancias.json"
# FILE_SALES_LOSSES_N26 = "n26_ventas_con_perdidas.json"
# FILE_DISTRIBUTIONS_N26 = "n26_distribution.json"
#
# FILE_PURCHASES_SC = "sc_compras.json"
# FILE_SALES_EARNINGS_SC = "sc_ventas_con_ganancias.json"
# FILE_SALES_LOSSES_SC = "sc_ventas_con_perdidas.json"
# FILE_DISTRIBUTIONS_SC = "sc_distribution.json"
#
# FILE_TRANSACTIONS_SC = "sc_transactions.csv"

if __name__ == "__main__":
    print("PATHS")
    print("=====")
    print(f"BASE_DIR = {BASE_DIR}")
    print(f"DATA_DIR = {DATA_DIR}")
    print(f"REPORT_DIR = {REPORT_DIR}")
    print(f"TEMP_DIR = {TEMP_DIR}")
