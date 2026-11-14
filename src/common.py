"""Shared paths, loaders and the local-area spatial join."""
import os, json
import numpy as np, pandas as pd
from shapely.geometry import shape, Point
from shapely.prepared import prep

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
MAN = os.path.join(ROOT, "data", "manual")
PROC = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(ROOT, "outputs")
SNAP = "2026-06-15"
os.makedirs(PROC, exist_ok=True); os.makedirs(OUT, exist_ok=True)

def ia_path(snapshot, f):
    return os.path.join(RAW, f"insideairbnb_vancouver_{snapshot}", f)

def money(s):
    """Prices are stored as text ('$1,234.00')."""
    return pd.to_numeric(s.astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce")

def load_local_areas():
    gj = json.load(open(os.path.join(RAW, "vancouver_opendata", "local_area_boundary.geojson")))
    return [(f["properties"]["name"], prep(shape(f["geometry"]))) for f in gj["features"]]

def assign_local_area(lat, lon, areas=None):
    """Point-in-polygon join to the City's 22 official local planning areas."""
    areas = areas or load_local_areas()
    out = np.empty(len(lat), dtype=object)
    for i, (y, x) in enumerate(zip(lat, lon)):
        p = Point(x, y); out[i] = None
        for name, poly in areas:
            if poly.contains(p): out[i] = name; break
    return out

def load_assumptions():
    import yaml
    return yaml.safe_load(open(os.path.join(MAN, "assumptions.yaml")))

def ltr_rent_condo(downtown_comps):
    """Long-term rental benchmark rent (per month) for the Downtown 1-2BR mix: Statistics Canada table 46-10-0092-01,
    AVERAGE ASKING rent, Vancouver CMA, Q1 2026, 1BR and 2BR weighted by the Downtown comparables' bedroom mix."""
    lt = load_assumptions()['long_term_rental']
    q = pd.read_csv(os.path.join(RAW, "statcan", "statcan_46100092_vancouver.csv"))
    q = q[(q.REF_DATE == lt['rent_source_quarter']) & (q.Estimates == 'Average asking rent')].set_index('Rental unit type').VALUE
    share_2br = (downtown_comps.bedrooms.fillna(1).clip(1, 2) == 2).mean()
    return (1 - share_2br) * q['Apartment - 1 bedroom'] + share_2br * q['Apartment - 2 bedrooms'], q
