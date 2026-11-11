"""Clean the 2026-06-15 detailed listings file and build the comparable set.
Writes data/processed/listings_all.csv (all rows + flags), data/processed/comparables.csv,
outputs/cleaning_waterfall.csv, outputs/data_quality.csv
"""
import pandas as pd, numpy as np
from common import *

L = pd.read_csv(ia_path(SNAP, "listings.csv.gz"))
print("raw shape", L.shape)
# Never carry identifying fields forward (rules: no host names, URLs, licence numbers)
L = L.drop(columns=[c for c in L.columns if c in ("listing_url","host_url","host_name","host_profile_url",
          "host_thumbnail_url","host_picture_url","picture_url","host_about","name","description",
          "neighborhood_overview","host_profile_id")])

# ---- parse explicitly ----
for c in ["last_scraped","calendar_last_scraped","first_review","last_review","host_since",
          "price_quote_checkin_date","price_quote_checkout_date"]:
    L[c] = pd.to_datetime(L[c], format="%Y-%m-%d", errors="coerce")
L["price_num"] = money(L["price"])
L["quote_nights"] = (L.price_quote_checkout_date - L.price_quote_checkin_date).dt.days
L["quote_lead_days"] = (L.price_quote_checkin_date - L.last_scraped).dt.days
# raw files hold only the licence CATEGORY (src/ia_sanitize.py); licence numbers are never stored
if "license_category" in L.columns:
    L["lic_cat"] = L["license_category"]
else:                                   # an unsanitized download: categorize, then discard the text
    from ia_sanitize import licence_category
    L["lic_cat"] = licence_category(L["license"])
L["str_policy"] = np.where(L.minimum_nights >= 30, "monthly_30plus", "nightly_lt30")
L = L.drop(columns=[c for c in ("license", "license_category", "host_id") if c in L.columns])   # keep only lic_cat

# ---- spatial join to official local areas (IA has 23 labels incl. 'Downtown Eastside'; City has 22) ----
L["local_area"] = assign_local_area(L.latitude.values, L.longitude.values)

# ---- data-quality checks ----
dq = {
  "rows": len(L), "unique_ids": L.id.nunique(),
  "scrape_dates": ", ".join(f"{d.date()}:{n}" for d, n in L.last_scraped.value_counts().sort_index().items()),
  "price_missing_pct": round(L.price_num.isna().mean()*100, 1),
  "price_from_90night_quote_pct": round((L.quote_nights >= 28).mean()*100, 1),
  "price_lt_30_count": int((L.price_num < 30).sum()), "price_gt_3000_count": int((L.price_num > 3000).sum()),
  "bedrooms_missing_pct": round(L.bedrooms.isna().mean()*100, 1),
  "reviews_ltm_zero_pct": round((L.number_of_reviews_ltm == 0).mean()*100, 1),
  "est_occupancy_cap_nights": int(L.estimated_occupancy_l365d.max()),
  "listings_at_occ_cap": int((L.estimated_occupancy_l365d == L.estimated_occupancy_l365d.max()).sum()),
  "entire_min30plus_pct": round((L[L.room_type=="Entire home/apt"].minimum_nights >= 30).mean()*100, 1),
  "no_licence_text_pct": round((L.lic_cat == "none").mean()*100, 1),
  "outside_city_polygons": int(L.local_area.isna().sum()),
  "ia_neighbourhood_labels": L.neighbourhood_cleansed.nunique(),
}
pd.Series(dq).to_csv(os.path.join(OUT, "data_quality.csv"), header=["value"])
print(pd.Series(dq).to_string())

# ---- comparable set: what a compliant, professionally run DDD unit would compete with ----
steps = []
def step(mask, label):
    global C
    C = C[mask(C)]; steps.append((label, len(C)))
C = L.copy(); steps.append(("All listings (snapshot 2026-06-15)", len(C)))
step(lambda d: d.room_type == "Entire home/apt", "Entire home/apt only (DDD buys whole units)")
step(lambda d: d.minimum_nights < 30, "Nightly STRs (min nights < 30; drops monthly rentals)")
step(lambda d: d.last_review >= d.last_scraped - pd.Timedelta(days=365), "Active: reviewed in last 12 months")
step(lambda d: d.first_review <= d.last_scraped - pd.Timedelta(days=365), "Full-year operators: first review >12 months ago")
step(lambda d: d.lic_cat == "city_licence", "Shows a City licence number (compliant comparables)")
step(lambda d: d.price_num.notna() & (d.quote_nights <= 7), "Usable nightly price (quote of <=7 nights)")
step(lambda d: d.price_num.between(60, 1500), "Price outliers removed (<$60 or >$1,500/night)")
step(lambda d: d.local_area.notna(), "Inside a City local-area polygon")
wf = pd.DataFrame(steps, columns=["step", "listings"]); wf.to_csv(os.path.join(OUT, "cleaning_waterfall.csv"), index=False)
print(wf.to_string())

# property segment used for acquisition matching
apt_types = {"Entire condo","Entire rental unit","Entire serviced apartment","Entire loft","Entire home/apt"}
house_types = {"Entire home","Entire townhouse","Entire villa","Entire bungalow","Entire house","Entire cottage"}
def seg(r):
    b = r.bedrooms if pd.notna(r.bedrooms) else 1
    if r.property_type in apt_types: return "condo_1-2br" if b <= 2 else "condo_3br+"
    if r.property_type in house_types: return "house_3br+" if b >= 3 else "house_1-2br"
    return "suite_or_other"   # guest suites, guesthouses (laneways): not separately purchasable
L["segment"] = L.apply(seg, axis=1)
C = C.merge(L[["id","segment"]], on="id")
print(C.segment.value_counts())
L.to_csv(os.path.join(PROC, "listings_all.csv"), index=False)
C.to_csv(os.path.join(PROC, "comparables.csv"), index=False)
