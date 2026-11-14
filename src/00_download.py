"""Download every public dataset used in the analysis (run once).
All sources are public, free, no login. Inside Airbnb data: CC BY 4.0.
Usage: python src/00_download.py
"""
import io, os, csv, urllib.request, urllib.parse
import pandas as pd
from ia_sanitize import sanitize   # strips host names, URLs, licence numbers, reviewer data

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")

def get(url, dest, timeout=300):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print("exists", dest); return
    print("GET", url)
    with urllib.request.urlopen(url, timeout=timeout) as r, open(dest, "wb") as f:
        f.write(r.read())
    if "insideairbnb" in dest: sanitize(dest)

# 1) Inside Airbnb Vancouver -- REQUIRED snapshot 2026-06-15 (detailed files)
IA = "https://data.insideairbnb.com/canada/bc/vancouver/{d}/{f}"
for f in ["data/listings.csv.gz", "data/calendar.csv.gz", "data/reviews.csv.gz",
          "visualisations/neighbourhoods.geojson"]:
    get(IA.format(d="2026-06-15", f=f), os.path.join(RAW, "insideairbnb_vancouver_2026-06-15", os.path.basename(f)))
# Earlier quarterly snapshots (same source) -- used ONLY for the seasonal price index.
# The 2026-09-17 snapshot exists but post-dates the case snapshot, so it is deliberately NOT used.
for d in ["2025-12-14", "2026-03-21"]:
    get(IA.format(d=d, f="data/listings.csv.gz"), os.path.join(RAW, f"insideairbnb_vancouver_{d}", "listings.csv.gz"))

# 2) City of Vancouver Open Data (no host names / licence numbers / addresses are downloaded)
VOD = "https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets"
get(VOD + "/property-tax-report/exports/csv?delimiter=,&where=report_year=%222026%22&select=folio,legal_type,"
    "land_coordinate,zoning_district,zoning_classification,current_land_value,current_improvement_value,"
    "tax_assessment_year,previous_land_value,previous_improvement_value,year_built,tax_levy,neighbourhood_code,report_year",
    os.path.join(RAW, "vancouver_opendata", "property_tax_report_2026.csv"))
get(VOD + "/property-parcel-polygons/exports/csv?delimiter=,&select=tax_coord,geo_point_2d",
    os.path.join(RAW, "vancouver_opendata", "property_parcel_points.csv"))
get(VOD + "/local-area-boundary/exports/geojson", os.path.join(RAW, "vancouver_opendata", "local_area_boundary.geojson"))
get(VOD + "/business-licences/exports/csv?delimiter=,&where=businesstype=%22Short-term%20Rental%20Operator%22"
    "&select=folderyear,status,businesstype,businesssubtype,localarea,issueddate,expireddate,feepaid",
    os.path.join(RAW, "vancouver_opendata", "str_business_licences_2024_2026.csv"))

# 3) CMHC Rental Market Survey via the Housing Market Information Portal (HMIP): public, free, no login.
#    We use the portal's own "Export -> CSV" function (the same request as the Export button on each table page),
#    not the web page itself. CMHC Licence Agreement for the Use of Data: reproduced accurately, source acknowledged.
HMIP_EXPORT = "https://www03.cmhc-schl.gc.ca/hmip-pimh/en/TableMapChart/ExportTable"
def hmip_table(params):
    """Download one HMIP table as CSV and return its data rows (zone/city, then 12 value/reliability columns)."""
    body = dict(DisplayAs="Table", Ytd="False", DefaultDataField="vacancy_rate_pct", Survey="Rms", exportType="csv")
    body.update(params)
    req = urllib.request.Request(HMIP_EXPORT, data=urllib.parse.urlencode(body).encode())
    with urllib.request.urlopen(req, timeout=120) as r:
        rows = list(csv.reader(r.read().decode("latin-1").splitlines()))
    start = next(i for i, x in enumerate(rows) if len(x) > 1 and x[0] == "" and x[1].startswith("Vacancy Rate")) + 1
    out = []
    for x in rows[start:]:
        if not x or not x[0].strip(): break
        out.append([c.strip().replace(",", "") for c in x[:12]])   # "1,914" -> "1914"; "c " -> "c"
    return out

# 3a) Table 2.1.31.3: Vancouver CMA by zone, October 2023-2025 (cross-check)
cols = ['zone','vacancy_rate_pct','vac_rel','availability_rate_pct','avail_rel','avg_rent','rent_rel',
        'median_rent','med_rel','pct_change_rent','chg_rel','units']
for y in [2023, 2024, 2025]:
    dest = os.path.join(RAW, "cmhc", f"cmhc_rms_vancouver_cma_by_zone_oct{y}.csv")
    if os.path.exists(dest): print("exists", dest); continue
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    t = pd.DataFrame(hmip_table({"TableId": "2.1.31.3", "GeographyId": "2410", "GeographyTypeId": "3",
                                 "BreakdownGeographyTypeId": "5", "GeograghyName": "Vancouver",
                                 "ForTimePeriod.Year": str(y), "ForTimePeriod.Month": "10"}), columns=cols)
    t["survey"] = f"October {y}"; t.to_csv(dest, index=False); print("saved", dest)

# 3b) Table 2.1.31.2: CITY-level (census subdivision, CY) published vacancy rates, October 2023-2025.
#     The opt-out test is about a municipality's published rate, so these official city figures are used for it.
CSD = {"Vancouver": 5915022, "Burnaby": 5915025, "New Westminster": 5915029, "Surrey": 5915004, "Richmond": 5915015}
dest = os.path.join(RAW, "cmhc", "cmhc_rms_city_vacancy_oct2023_2025.csv")
if os.path.exists(dest): print("exists", dest)
else:
    rows = []
    for city, g in CSD.items():
        for y in [2023, 2024, 2025]:
            x = hmip_table({"TableId": "2.1.31.2", "GeographyId": str(g), "GeographyTypeId": "4",
                            "BreakdownGeographyTypeId": "0", "GeograghyName": city,
                            "ForTimePeriod.Year": str(y), "ForTimePeriod.Month": "10"})[0]
            rows.append({"city": city, "csd_name": f"{x[0]} (CY)", "year": y, "vacancy_rate_pct": x[1],
                         "reliability": x[2], "units": x[11]})
    pd.DataFrame(rows).to_csv(dest, index=False); print("saved", dest)
# CMHC reliability codes: a = excellent, b = very good, c = good, d = poor (use with caution).

# 5) Statistics Canada, Quarterly Rent Statistics, table 46-10-0092-01 (asking rents by unit type and bedrooms,
#    experimental estimates, conducted with CMHC). Free CSV, no login. Only the Vancouver CMA rows are kept.
#    Used for the long-term-rental benchmark: Q1 2026 (released 2026-06-09) is the latest quarter published
#    before the 2026-06-15 case snapshot; later quarters in the file are ignored.
dest = os.path.join(RAW, "statcan", "statcan_46100092_vancouver.csv")
if os.path.exists(dest): print("exists", dest)
else:
    import zipfile
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print("GET StatCan 46-10-0092-01")
    with urllib.request.urlopen("https://www150.statcan.gc.ca/n1/tbl/csv/46100092-eng.zip", timeout=300) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    t = pd.read_csv(z.open("46100092.csv"), low_memory=False)
    t[t.GEO.str.startswith("Vancouver")].to_csv(dest, index=False); print("saved", dest)

# 4) Greater Vancouver REALTORS MLS HPI, June 2026 stats package (public PDF, free, no login). Only six published
#    benchmark figures are needed, so they were transcribed by hand into data/manual/gvr_hpi_june2026.csv with the URL.
