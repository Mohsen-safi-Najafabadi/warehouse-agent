"""A quick sanity check that the whole environment works."""
import sys
import duckdb
import pandas as pd

print("Python:", sys.version.split()[0])
print("DuckDB:", duckdb.__version__)
print("pandas:", pd.__version__)

# Make a tiny in-memory database and query it
con = duckdb.connect()
con.execute("CREATE TABLE t (name VARCHAR, qty INTEGER)")
con.execute("INSERT INTO t VALUES ('bolt', 10), ('nut', 25), ('washer', 7)")
df = con.execute("SELECT name, qty FROM t WHERE qty > 8 ORDER BY qty DESC").fetchdf()
print(df)
con.close()

print("\n✅ Everything works.")