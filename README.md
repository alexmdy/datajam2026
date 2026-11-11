# DataJam 2026 — The Airbnb Vancouver Problem

Reproducible analysis behind our recommendation to Data-Driven Developments (DDD): **buy 12 one- and two-bedroom condos in Downtown Vancouver (~$9.0M all-in, ~$1.0M reserve) and run them seasonally** — nightly guests May–Oct, furnished stays of 30+ nights Jan–Apr and Nov–Dec, so the units are not "vacant" for Vancouver's 3% Empty Homes Tax or BC's 1% Speculation and Vacancy Tax.

Expected 2027: net operating income ≈ $370k (P10–P90: $280k–$470k), 4.1% net yield on capital deployed (P10–P90: 3.1%–5.3%).

Data: Inside Airbnb, Vancouver, 15 June 2026, CC BY 4.0.

## Run it

```bash
pip install -r requirements.txt
python run_all.py --download   # first run: downloads every public dataset, then runs 01–09
python run_all.py              # later runs: recompute everything from data/raw
python run_all.py --verbose    # same, but also show each step's full printout on screen
PPTX_SKILL=<path to a folder containing scripts/apply_theme.js> node deck/build_deck.js   # draft deck from outputs/deck_data.json (needs the pptxgenjs npm package)
```

`deck/DDD_DataJam2026_Pitch.pptx` is the submitted pitch. It started from `build_deck.js` and was then edited by hand (slides reordered: Where/what is slide 3, the operating model slide 4), so slide numbers in a fresh build differ; every number on it is in `outputs/key_numbers.csv`.

Monte Carlo seeds are fixed, so every number reproduces exactly.

**What you see when it runs:** one progress line per step, then a summary of every pitch number grouped the way the pitch tells the story (recommendation, data and cleaning, area ranking, decisions D1-D4, risks, validation, assumptions). Each group has a heading saying what the numbers mean, the slides that use them and the output file they come from. The summary is also saved to `outputs/report.txt`; each step's full printout is in `outputs/run_log.txt`.

**Privacy:** the Inside Airbnb files in `data/raw/` are stored *sanitized* (`src/ia_sanitize.py`, applied automatically by `00_download.py`): no host names, listing URLs, host profiles, licence numbers or reviewer names/text are kept. The licence text is replaced by its category (`license_category`: city_licence / exempt / other_text / none), which is all the analysis uses. The original detailed listings file has 90 columns; the stored copy keeps 74.

**Note:** Inside Airbnb keeps only about 12 months of snapshots on its public page. The 15 June 2026 and 21 March 2026 Vancouver files were downloadable in November 2026; if they roll off, the copies in `data/raw/` are the only source.

## Pipeline

| Script | What it does | Main outputs |
|---|---|---|
| `src/00_download.py` | Downloads all public data (no host names, licence numbers or addresses are requested) | `data/raw/` |
| `src/01_clean_listings.py` | Parses prices/dates, data-quality checks, point-in-polygon join to the City's 22 local areas, builds the 1,809-listing comparable set | `outputs/data_quality.csv`, `outputs/cleaning_waterfall.csv` |
| `src/02_seasonality.py` | Review-based demand seasonality; same-listing March vs June price ratio; FIFA World Cup match-night premium; annual ADR factor | `outputs/seasonality_params.csv`, `outputs/seasonality_monthly.csv` |
| `src/03_property_values.py` | 2026 assessments → parcels → local areas; median condo (strata) and detached (R1-1) values; GVR roll-forward; check vs GVR benchmarks | `outputs/acquisition_cost_by_area.csv`, `outputs/value_validation.csv` |
| `src/04_economics.py` | Per-comparable 2027 revenue, costs, taxes and yield under nightly-only vs seasonal hybrid; area ranking with bootstrap CIs | `outputs/area_ranking.csv`, `outputs/segment_summary.csv`, `outputs/revenue_bridge.csv` |
| `src/05_portfolio.py` | Monte Carlo (10,000 runs) of four portfolios: few high-value vs many modest | `outputs/portfolio_options.csv` |
| `src/06_validation.py` | Occupancy vs calendar, split-half stability, World Cup check for Downtown, long-term-rental benchmark, compliance estimate, CMHC opt-out test, sensitivity | `outputs/validation_summary.csv`, `outputs/sensitivity.csv` |
| `src/07_charts.py` | Static PNG figures (for the README / backup) | `outputs/figures/` |
| `src/08_key_numbers.py` | **Every number quoted in the pitch, with the script that produced it** | `outputs/key_numbers.csv` |
| `src/09_deck_data.py` | Exports what the deck displays | `outputs/deck_data.json` |
| `src/10_report.py` | Readable summary of every pitch number, with headings explaining each group (reads 01-09 outputs only) | `outputs/report.txt` |

All cost and tax assumptions live in `data/manual/assumptions.yaml`. The six GVR benchmark figures (transcribed from the public June 2026 stats package PDF, whose site blocks scripted download) are in `data/manual/gvr_hpi_june2026.csv`.

## Tracing a number from the pitch

| Pitch claim | Key in `outputs/key_numbers.csv` | Produced in |
|---|---|---|
| 12 condos, $9.0M deployed | `B_units`, `B_capital` | `05_portfolio.py` (`build`) |
| NOI ≈ $370k ($280k–$480k) | `B_noi_p50`, `B_noi_p10`, `B_noi_p90` | `05_portfolio.py` (`simulate`) |
| 4.1% yield (3.1%–5.3%) | `B_p50`, `B_p10`, `B_p90` | `05_portfolio.py` |
| Nightly all year −1.4% vs hybrid 4.2% (condos) | `condo_yield_str`, `condo_yield_hybrid` | `04_economics.py` |
| Long-term rental 2.5% (condo, $2,614/mo) / 2.3% (house, $4,860/mo) | `ltr_benchmark_yield`, `ltr_benchmark_yield_house`, `ltr_rent_*` | `06_validation.py` |
| Naive revenue would show 4.6% instead of 4.2% (D2) | `condo_yield_hybrid_naive_revenue` | `04_economics.py` |
| May–Oct = 73% of nightly revenue | `may_oct_revenue_share` | `02_seasonality.py` |
| World Cup match-night premium 5.8% (95% CI 3.0–9.0%) | `match_night_premium`, `match_premium_ci` | `02_seasonality.py` |
| Revenue $64.8k → $57.0k → $67.0k | `rev_bridge_*` | `04_economics.py` |
| Downtown 4.6% (n=475), $707k purchase | `downtown_yield_hybrid`, `downtown_n`, `downtown_price` | `03`, `04` |
| Houses P50 2.7%, 16% chance < 2% | `A_p50`, `A_prob_below_2` | `05_portfolio.py` |
| Fail 6-month test → −0.8% | `fail6_yield` | `06_validation.py` (sensitivity) |
| City vacancy 0.8% (2023), 1.5% (2024), 2.7% (2025); Burnaby 5.9%, New Westminster 5.8%, Surrey 4.3%, Richmond 3.1% (2025) | `city_vacancy_*`, `*_vacancy_2025` | `06_validation.py` (CMHC published city rates) |
| City STR licence $1,108 (2026 median fee paid) | `city_str_licence_fee` | `06_validation.py` (checks `assumptions.yaml`) |
| Furnished months listed on Airbnb: −0.5 pt | `furnished_on_airbnb_yield_cost` | `06_validation.py` |
| Price proxy within −2.0% to +4.5% of GVR | `value_check_range` | `03_property_values.py` |

## Data sources (all public, free, no login)

- Inside Airbnb, Vancouver detailed listings, calendar, reviews, 15 June 2026; listings, 21 March 2026 and 14 December 2025 (the December file has no prices). CC BY 4.0. The 17 September 2026 snapshot was deliberately **not** used (after the case date), nor was the 18-column summary `listings.csv`.
- City of Vancouver Open Data: property tax report (2026), property parcel polygons, local area boundaries, business licences (short-term rental operators; only status, year, local area and fee fields).
- CMHC Rental Market Survey, HMIP table 2.1.31.2, published city (census subdivision) vacancy rates for Vancouver, Burnaby, New Westminster, Surrey and Richmond, October 2023–2025 (used for the opt-out test); and table 2.1.31.3, Vancouver CMA by zone (cross-check).
- Statistics Canada, Quarterly Rent Statistics, table 46-10-0092-01 (average asking rent by unit type and bedrooms, Vancouver CMA, experimental estimates with CMHC). Q1 2026, released 9 June 2026, is used for the long-term-rental benchmark; later quarters in the file are ignored.
- Greater Vancouver REALTORS, MLS HPI, June 2026 stats package.
- Rules and rates: City of Vancouver Vacancy Tax By-law 11674 (3%); BC Speculation and Vacancy Tax (1% Canadian owners from 2026); BC Property Transfer Tax; BC STR registry fees; City of Vancouver 2026 residential tax rate; BC Government news release, 17 April 2026 (opt-out rules).

## Limitations

Occupancy and revenue are Inside Airbnb estimates built from reviews (capped at 255 nights). Purchase prices are area medians, not bedroom-specific. Furnished monthly rents are asking prices, assumed fully let for 6 months and leased directly (listing them on Airbnb would cost about 0.5 pt). Strata fees and which buildings allow short stays are not in any dataset used. Whether furnished stays of 30+ nights satisfy the Empty Homes Tax, the SVT and tenancy law needs a legal opinion.

## AI use

Built with help from Claude (Anthropic) for code, regulatory research and slide drafting. Every figure is regenerated by `run_all.py`; regulatory facts were checked against primary sources; the price proxy was checked against GVR's independent benchmark.
