"""Pre-flight check before the dashboard is started (also used by run_dashboard.bat / .sh).
Checks Python version, libraries, data files and one real calculation. Prints PASS/FAIL lines, exit code 1 if anything fails."""
import sys, pathlib, importlib

HERE = pathlib.Path(__file__).resolve().parent
bad = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f" ({detail})" if detail else ""))
    if not ok:
        bad.append(name)


check("Python 3.10 or newer", sys.version_info >= (3, 10), sys.version.split()[0])
for lib, min_major in [("streamlit", 1), ("pandas", 2), ("numpy", 1), ("plotly", 5), ("pyarrow", 15), ("openpyxl", 3)]:
    try:
        mod = importlib.import_module(lib)
        ver = getattr(mod, "__version__", "?")
        check(f"library {lib}", int(str(ver).split(".")[0]) >= min_major, ver)
    except Exception as ex:
        check(f"library {lib}", False, type(ex).__name__)
data = HERE / "data"
for f in ["electricity_clean.parquet", "outliers_log.csv", "cleaning_log.csv", "reconciliation.csv", "data_dictionary_clean.csv", "missing_data_table.csv"]:
    check(f"data file {f}", (data / f).exists() and (data / f).stat().st_size > 0)
try:
    import pandas as pd
    df = pd.read_parquet(data / "electricity_clean.parquet")
    need = {"timestamp", "room_id", "building_name", "energy_clean", "energy_kwh", "is_off_hours", "occupancy_people", "temperature_c", "flag_outlier"}
    check("data columns present", need <= set(df.columns), f"{len(df):,} rows")
    check("total kWh can be calculated", float(df["energy_clean"].sum()) > 0, f"{df['energy_clean'].sum():,.0f} kWh")
except Exception as ex:
    check("read data", False, type(ex).__name__)
check("Streamlit entry file", (HERE / "app.py").exists())
print("\nALL CHECKS PASSED" if not bad else f"\n{len(bad)} CHECK(S) FAILED: " + ", ".join(bad))
sys.exit(1 if bad else 0)
