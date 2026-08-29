"""Quick SQL runner: python q.py "SELECT * FROM suppliers LIMIT 5" """
import sys
import duckdb
import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

if len(sys.argv) < 2:
    print('Usage: python q.py "SELECT ..."')
    sys.exit(1)

query = sys.argv[1]
con = duckdb.connect("data/factory.duckdb", read_only=True)
try:
    print(con.execute(query).fetchdf())
except Exception as exc:
    print("ERROR:", exc)
finally:
    con.close()