"""Reproduce every number and figure: python run_all.py  (add --download on a fresh clone)"""
import subprocess, sys, os
here = os.path.dirname(os.path.abspath(__file__))
steps = (["00_download.py"] if "--download" in sys.argv else []) + ["01_clean_listings.py", "02_seasonality.py",
         "03_property_values.py", "04_economics.py", "05_portfolio.py", "06_validation.py", "07_charts.py", "08_key_numbers.py", "09_deck_data.py"]
for s in steps:
    print(f"\n===== {s} =====", flush=True)
    subprocess.run([sys.executable, s], cwd=os.path.join(here, "src"), check=True)
