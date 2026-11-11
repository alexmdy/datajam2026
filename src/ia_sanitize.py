"""Strip identifying fields from Inside Airbnb files before they are stored in data/raw/.
The competition rules forbid showing host names, listing URLs or licence numbers, so the repo never keeps them:
  listings: drops names, URLs, host profile text/photos, host ids; the licence text is replaced by its
            category only (city_licence / exempt / other_text / none), which is all the analysis uses.
  reviews:  keeps listing_id and date only (no reviewer names, reviewer ids or review text).
Calendar files carry no identifying fields and are kept as downloaded. Run on a freshly downloaded file:
  python src/ia_sanitize.py <path-to-listings.csv.gz | reviews.csv.gz>
"""
import sys, os
import numpy as np, pandas as pd

DROP = ["listing_url", "name", "description", "neighborhood_overview", "picture_url", "host_id", "host_url",
        "host_profile_id", "host_profile_url", "host_name", "host_location", "host_about", "host_thumbnail_url",
        "host_picture_url", "host_neighbourhood", "host_verifications"]

def licence_category(lic):
    lic = lic.fillna("")
    return np.select([lic.str.contains(r"Municipal registration number: \d{2}-\d{6}"),
                      lic.str.contains("Exempt", case=False), lic.str.len() > 0],
                     ["city_licence", "exempt", "other_text"], default="none")

def sanitize_listings(path):
    L = pd.read_csv(path, low_memory=False)
    if "license" in L.columns:
        L.insert(L.columns.get_loc("license"), "license_category", licence_category(L["license"]))
        L = L.drop(columns=["license"])
    L = L.drop(columns=[c for c in DROP if c in L.columns])
    L.to_csv(path, index=False, compression="gzip")

def sanitize_reviews(path):
    R = pd.read_csv(path, usecols=["listing_id", "date"])
    R.to_csv(path, index=False, compression="gzip")

def sanitize(path):
    name = os.path.basename(path)
    if name.startswith("listings"): sanitize_listings(path)
    elif name.startswith("reviews"): sanitize_reviews(path)

if __name__ == "__main__":
    for p in sys.argv[1:]: sanitize(p); print("sanitized", p)
