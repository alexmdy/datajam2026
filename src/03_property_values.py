"""Acquisition cost by local area from the City's 2026 property tax report (BC Assessment values,
valuation date July 1 2025), joined to parcel points -> local-area polygons, rolled forward to mid-2026
with GVR MLS HPI one-year change. Writes outputs/acquisition_cost_by_area.csv and outputs/value_validation.csv
"""
import pandas as pd, numpy as np
from common import *

T = pd.read_csv(os.path.join(RAW, "vancouver_opendata", "property_tax_report_2026.csv"), dtype={'land_coordinate': str})
P = pd.read_csv(os.path.join(RAW, "vancouver_opendata", "property_parcel_points.csv"), dtype={'tax_coord': str})
T.columns = [c.lstrip('﻿') for c in T.columns]; P.columns = [c.lstrip('﻿') for c in P.columns]
T = T[T.tax_assessment_year == 2026]
T['value'] = T.current_land_value + T.current_improvement_value
P = P.drop_duplicates('tax_coord')
P[['lat', 'lon']] = P.geo_point_2d.str.split(',', expand=True).astype(float)
P['local_area'] = assign_local_area(P.lat.values, P.lon.values)
T = T.merge(P[['tax_coord', 'local_area']], left_on='land_coordinate', right_on='tax_coord', how='left')
print("join rate", T.local_area.notna().mean().round(4))

condo = T[(T.legal_type == 'STRATA') & T.zoning_classification.isin(
    ['Comprehensive Development', 'Residential', 'Commercial', 'Historical Area']) & T.value.between(250_000, 5_000_000)]
house = T[(T.legal_type == 'LAND') & (T.zoning_district == 'R1-1') & T.value.between(500_000, 20_000_000)]

WEST = {"Arbutus Ridge","Downtown","Dunbar-Southlands","Fairview","Kerrisdale","Kitsilano","Marpole","Oakridge",
        "Shaughnessy","South Cambie","West End","West Point Grey"}
G = pd.read_csv(os.path.join(MAN, "gvr_hpi_june2026.csv")).set_index(['property_type', 'gvr_area'])
def adj(area, ptype):
    side = "Vancouver West" if area in WEST else "Vancouver East"
    return 1 + G.loc[(ptype, side), 'one_year_change_pct'] / 100

rows = []
for seg, df, ptype in [("condo_1-2br", condo, "Apartment"), ("house_3br+", house, "Detached")]:
    g = df.groupby('local_area').value.agg(n_units='size', assessed_median='median',
                                          assessed_p25=lambda s: s.quantile(.25), assessed_p75=lambda s: s.quantile(.75))
    g['gvr_adj'] = [adj(a, ptype) for a in g.index]
    g['price_est_mid2026'] = (g.assessed_median * g.gvr_adj).round(-3)
    g['segment'] = seg; rows.append(g.reset_index())
A = pd.concat(rows); A.to_csv(os.path.join(OUT, "acquisition_cost_by_area.csv"), index=False)
print(A[A.segment == 'condo_1-2br'][['local_area','n_units','assessed_median','price_est_mid2026']].to_string(index=False))

# validation: our assessed-value proxy vs the independent GVR benchmark
val = []
for ptype, df in [("Apartment", condo), ("Detached", house)]:
    for side, mask in [("Vancouver West", df.local_area.isin(WEST)), ("Vancouver East", ~df.local_area.isin(WEST))]:
        f = 1 + G.loc[(ptype, side), 'one_year_change_pct'] / 100
        ours = df[mask].value.median() * f; bench = G.loc[(ptype, side), 'benchmark_price_jun2026']
        val.append([ptype, side, round(ours, -3), bench, round(ours / bench - 1, 3)])
V = pd.DataFrame(val, columns=['type', 'area', 'our_median_mid2026', 'gvr_benchmark_jun2026', 'pct_diff'])
V.to_csv(os.path.join(OUT, "value_validation.csv"), index=False); print(V.to_string(index=False))
