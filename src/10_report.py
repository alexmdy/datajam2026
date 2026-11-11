"""Readable summary of every number the pitch uses, grouped the way the pitch tells the story.
Prints to the screen and writes outputs/report.txt. It only READS files written by steps 01-09
(mostly outputs/key_numbers.csv); it computes nothing new, so every number here traces back to those steps.
"""
import json, io, contextlib
import pandas as pd
from common import *

r = lambda f: os.path.join(OUT, f)
K = pd.read_csv(r("key_numbers.csv")).set_index('key')['value']
def k(name): return float(K[name])
A = load_assumptions(); op, cap, lt = A['operating'], A['capital'], A['long_term_rental']
D = json.load(open(r("deck_data.json")))
W = 92

# ---------- formatting ----------
def pct(v, d=1): return f"{v * 100:.{d}f}%"
def usd(v): return f"${v:,.0f}"
def usdk(v): return f"${v / 1000:,.0f}k"
def usdm(v): return f"${v / 1e6:,.2f}M"
def r10k(v): return f"${round(v, -4) / 1000:,.0f}k"          # the pitch rounds income to $10k
def section(num, title, slides, why):
    print("\n" + "=" * W); print(f" {num}. {title}" + (f"   (pitch: {slides})" if slides else "")); print("=" * W)
    for line in wrap(why, W - 2): print("  " + line)
    print("  " + "-" * (W - 2))
def sub(title): print(f"\n  > {title}")
def row(label, value, note=""):
    print(f"    {label + ' ':.<52} {value}")
    if note:
        for line in wrap(note, W - 10): print(" " * 8 + line)
def wrap(text, width):
    out, line = [], ""
    for w in text.split():
        if len(line) + len(w) + 1 > width: out.append(line); line = w
        else: line = (line + " " + w).strip()
    return out + [line] if line else out
def table(df, note=""):
    """First column left-aligned, the rest right-aligned."""
    cols = list(df.columns); cells = [[str(v) for v in df[c]] for c in cols]
    wid = [max(len(c), *(len(v) for v in col)) for c, col in zip(cols, cells)]
    fmt = lambda vals: "  ".join(v.ljust(w) if i == 0 else v.rjust(w) for i, (v, w) in enumerate(zip(vals, wid)))
    print("      " + fmt(cols)); print("      " + "  ".join("-" * w for w in wid))
    for i in range(len(df)): print("      " + fmt([col[i] for col in cells]))
    if note:
        for line in wrap(note, W - 8): print("      " + line)

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    print("=" * W)
    print(" DDD x DataJam 2026 -- RESULTS OF run_all.py")
    print(" Every number below comes from outputs/key_numbers.csv or the output file it names.")
    print(" Yields = 2027 net operating income / all-in capital (price + transfer tax + closing + furnishing).")
    print("=" * W)

    # 1 ------------------------------------------------------------------------------------------
    section(1, "THE RECOMMENDATION", "slides 1, 6, 8",
            "What DDD should buy and what it should earn in 2027. Ranges are P10-P90 across 10,000 simulated "
            "versions of 2027 (P10 = a bad year, P90 = a good year). [portfolio_options.csv]")
    row("Condos to buy (Downtown, 1-2 bedroom)", f"{k('B_units'):.0f}", "Run nightly May-Oct, furnished 30+ night stays Nov-Apr.")
    row("Share that should be 1-bedroom", pct(k('downtown_1br_share'), 0), "Mirrors the Downtown comparables (rest are 2-bedroom).")
    row("Capital deployed (all-in)", f"{usd(k('B_capital'))}   (pitch: {usdm(round(k('B_capital'), -5))[:-2]}M)", "Price + property transfer tax + closing + furnishing for all 12 units.")
    row("Cash kept in reserve", f"{usd(10e6 - k('B_capital'))}   (pitch: $1.0M)",
        f"Covers about {k('reserve_years_of_vacancy_tax'):.1f} years of the vacancy taxes if the 6-month test fails.")
    row("Expected 2027 net operating income (P50)", f"{usd(k('B_noi_p50'))}   (pitch: {r10k(k('B_noi_p50'))})", "Median simulated year.")
    row("  NOI range (P10 - P90)", f"{usd(k('B_noi_p10'))} - {usd(k('B_noi_p90'))}   (pitch: {r10k(k('B_noi_p10'))}-{r10k(k('B_noi_p90'))})")
    row("Expected 2027 net yield on capital deployed", pct(k('B_p50')), "The headline return number.")
    row("  Yield range (P10 - P90)", f"{pct(k('B_p10'))} - {pct(k('B_p90'))}")
    row("Yield on the full $10M (reserve earns nothing)", pct(k('B_yield_on_10m')))

    # 2 ------------------------------------------------------------------------------------------
    section(2, "DATA AND CLEANING", "slides 2, 13",
            "How the 15 June 2026 Inside Airbnb snapshot was cut down to listings a compliant, professionally "
            "run DDD unit would compete with. [cleaning_waterfall.csv, data_quality.csv]")
    sub("Cleaning waterfall: listings left after each filter")
    wf = pd.read_csv(r("cleaning_waterfall.csv")); wf['removed'] = (-wf.listings.diff()).fillna(0).astype(int)
    table(wf.rename(columns={'step': 'filter', 'listings': 'left'}))
    sub("Data-quality checks")
    dq = pd.read_csv(r("data_quality.csv"), index_col=0)['value']
    row("Listings in the snapshot / unique ids", f"{dq['rows']} / {dq['unique_ids']}", "Equal, so no duplicate listings.")
    row("Days the scrape ran (listings per day)", "  ".join(d.replace('2026-06-', 'Jun ').replace('2026-07-', 'Jul ').replace(':', ': ') for d in dq['scrape_dates'].split(', ')),
        "One snapshot, crawled over three days.")
    row("Prices missing", f"{dq['price_missing_pct']}%")
    row("Prices that are long-stay quotes (28+ nights)", f"{dq['price_from_90night_quote_pct']}%",
        "Mostly 90-night quotes, which make nightly 'prices' look tiny; only quotes of 7 nights or fewer are kept.")
    row("Prices under $30 / over $3,000", f"{dq['price_lt_30_count']} / {dq['price_gt_3000_count']}")
    row("Entire homes requiring 30+ nights", f"{dq['entire_min30plus_pct']}%", "Monthly rentals, not short-term rentals; dropped.")
    row("Listings at the 255-night occupancy cap", dq['listings_at_occ_cap'], "Inside Airbnb caps its occupancy estimate at 255 nights.")
    row("Listings with no licence text", f"{dq['no_licence_text_pct']}%")
    row("Bedrooms missing", f"{dq['bedrooms_missing_pct']}%", "Treated as 1 bedroom.")
    row("Inside Airbnb neighbourhood labels vs City areas", f"{dq['ia_neighbourhood_labels']} vs 22",
        "Every listing re-assigned to an official local area by its coordinates.")
    row("Listings outside every City local area", dq['outside_city_polygons'])

    # 3 ------------------------------------------------------------------------------------------
    section(3, "WHERE AND WHAT: AREA RANKING", "slide 3",
            "Median 2027 yield of each area's comparables under the seasonal hybrid, for areas with 20+ "
            "comparables, with a 90% bootstrap confidence interval. Higher and tighter is better. [area_ranking.csv]")
    ar = pd.read_csv(r("area_ranking.csv")).sort_values('yield_hybrid', ascending=False)
    t = pd.DataFrame({'area': ar.local_area, 'type': ar.segment.str.replace('condo_1-2br', 'condo 1-2BR').str.replace('house_3br+', 'house 3BR+', regex=False),
                      'n': ar.n, 'purchase': ar.price.map(usdk), 'nightly rate': ar.adr_2027.map(usd), 'nights/yr': ar.nights.map('{:.0f}'.format),
                      'yield': ar.yield_hybrid.map(pct), '90% CI': [f"{pct(a)}-{pct(b)}" for a, b in zip(ar.yield_hybrid_ci90_lo, ar.yield_hybrid_ci90_hi)]})
    table(t, "n = comparables; purchase = 2026 assessed median rolled to mid-2026 with GVR; nightly rate = 2027 "
             "seasonal average; nights = median estimated nights booked per year.")
    sub("Downtown condo, the recommended unit")
    row("Comparables", f"{k('downtown_n'):.0f}")
    row("Purchase price (2026 assessments, GVR-adjusted)", usd(k('downtown_price')))
    row("All-in capital per unit", usd(k('downtown_capital')), "Adds BC property transfer tax, 0.6% closing and $25k furnishing.")
    row("Median nightly rate x nights booked", f"{usd(k('downtown_adr'))} x {k('downtown_nights'):.0f}")
    dt = ar[(ar.segment == 'condo_1-2br') & (ar.local_area == 'Downtown')].iloc[0]
    row("Median hybrid yield (90% CI)", f"{pct(dt.yield_hybrid)} ({pct(dt.yield_hybrid_ci90_lo)}-{pct(dt.yield_hybrid_ci90_hi)})")
    sub("World Cup test: does Downtown still lead on March (pre-tournament) prices?")
    ev = pd.read_csv(r("validation_downtown_event_check.csv"))
    table(pd.DataFrame({'area': ev.local_area, 'n': ev.n, 'rank on June prices': ev.rank_june.astype(int),
                        'rank on March prices': ev.rank_march.astype(int), 'June / March price': ev.june_over_march_price.map('{:.2f}'.format)}),
          "Downtown's June/March jump is no bigger than other areas', and it stays top two on March prices: "
          "its lead is not a World Cup effect. [validation_downtown_event_check.csv]")

    # 4 ------------------------------------------------------------------------------------------
    section(4, "DECISION 1 - OPERATING MODEL", "slides 4, 9",
            "A unit not lived in or rented for 6 months in 30+ day stays is 'vacant' and pays the 3% Empty Homes "
            "Tax + 1% SVT. Compares nightly all year, the seasonal hybrid and a plain long-term rental. "
            "[segment_summary.csv, validation_summary.csv]")
    sub("Median 2027 yield by operating model")
    table(pd.DataFrame({'property': ['1-2BR condo', '3BR+ house'],
                        'nightly all year': [pct(k('condo_yield_str')), pct(k('house_yield_str'))],
                        'seasonal hybrid (plan)': [pct(k('condo_yield_hybrid')), pct(k('house_yield_hybrid'))],
                        'long-term rental': [pct(k('ltr_benchmark_yield')), pct(k('ltr_benchmark_yield_house'))]}))
    row("Vacancy taxes/yr, nightly all year (median condo)", usd(k('condo_vacancy_taxes_median')), "3% Empty Homes Tax + 1% SVT on the assessed value.")
    row("Condo nightly all year with no vacancy tax", pct(k('condo_yield_no_vacancy_tax')), "Shows the taxes are what make nightly-only lose money.")
    row("Share of nightly revenue earned May-Oct", pct(k('may_oct_revenue_share'), 0), "So Nov-Apr is only the remainder: the cheap months to give up.")
    row("Long-term rent used, condo / house (per month)", f"{usd(k('ltr_rent_condo_month'))} / {usd(k('ltr_rent_house_month'))}",
        "Statistics Canada 46-10-0092-01, average asking rent, Vancouver CMA, Q1 2026.")
    sub("Month by month, median Downtown condo: net income after fees")
    mc = D['month_compare']; months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    plan = ['furnished' if m in ('Jan', 'Feb', 'Mar', 'Apr', 'Nov', 'Dec') else 'nightly' for m in months]
    table(pd.DataFrame({'month': months, 'nightly guests': [usd(v) for v in mc['nightly']], 'furnished 30+ nights': [usd(v) for v in mc['furnished']],
                        'better': ['furnished' if f > n else 'nightly' for n, f in zip(mc['nightly'], mc['furnished'])], 'plan': plan}),
          "Furnished rent is the lower-quartile 1BR monthly ask, flat (no monthly data). October is close and the "
          "furnished figure is an asking rent, so October stays nightly. [deck_data.json]")
    mtr = pd.read_csv(r("mtr_rent_by_bedrooms.csv"))
    row("Furnished monthly ask used, 1BR / 2BR", f"{usd(mtr.monthly_rent_q[0])} / {usd(mtr.monthly_rent_q[1])}",
        "Lower quartile of Airbnb monthly-stay asks. [mtr_rent_by_bedrooms.csv]")

    # 5 ------------------------------------------------------------------------------------------
    section(5, "DECISION 2 - REVENUE BASE", "slides 5, 9",
            "Inside Airbnb's revenue estimate = one June price quote x nights. Three corrections turn it into a "
            "normal-year 2027 figure. [seasonality_params.csv, revenue_bridge.csv]")
    row("World Cup match-night premium removed", pct(k('match_night_premium')),
        f"95% CI {'-'.join(pct(float(x)) for x in K['match_premium_ci'].split('-'))}; each listing's March price is the control.")
    row("Late-March price as a share of June price", pct(k('mar_over_jun_price'), 0), "Same listings, so this is seasonality, not mix.")
    row("Annual average nightly rate = this x June price", f"{k('annual_adr_factor'):.2f}")
    sub("Revenue bridge, median condo comparable (per year)")
    br = pd.read_csv(r("revenue_bridge.csv"))
    table(pd.DataFrame({'step': br.iloc[:, 0], 'revenue': br.iloc[:, 1].map(usd)}))
    row("Inside Airbnb method -> corrected nightly-only", pct(k('rev_bridge_str') / k('rev_bridge_ia') - 1, 0))
    row("Condo hybrid yield, naive vs corrected revenue", f"{pct(k('condo_yield_hybrid_naive_revenue'))} vs {pct(k('condo_yield_hybrid'))}",
        "What D2 changed: without the corrections every yield would look about half a point better.")

    # 6 ------------------------------------------------------------------------------------------
    section(6, "DECISION 3 - FEW HIGH-VALUE VS MANY MODEST", "slides 7, 10",
            "10,000 simulated 2027s per portfolio. Each unit draws a real comparable; all units share market shocks "
            "(rate, occupancy, furnished rent, ramp-up, price paid). [portfolio_options.csv]")
    po = pd.read_csv(r("portfolio_options.csv"))
    table(pd.DataFrame({'portfolio': po.option.str.split(':').str[0].str.replace('Many modest', 'Modest').str.replace('Few high-value', 'High-value'),
                        'units': po.units, 'capital': po.capital_deployed.map(usdm), 'P10': po.yield_p10.map(pct), 'P50': po.yield_p50.map(pct),
                        'P90': po.yield_p90.map(pct), 'P90-P10 spread': po.spread_p90_p10.map(lambda v: f"{v * 100:.1f} pts"),
                        'chance < 2%': po.prob_yield_below_2pct.map(lambda v: pct(v, 1))}))
    for o, m in zip(po.option, po['mix']): print(f"      {o.split('.')[0]}: {m}")
    row("3-area mix vs Downtown only: median change", f"{(k('C_p50') - k('B_p50')) * 100:+.1f} pts",
        f"Spread {k('C_spread') * 100:.1f} vs {k('B_spread') * 100:.1f} pts: spreading across areas barely cuts risk, because 2027 risk is market-wide.")

    # 7 ------------------------------------------------------------------------------------------
    section(7, "RISKS AND SENSITIVITY", "slides 6, 11, 12",
            "What moves the recommended portfolio's expected yield, one assumption at a time (base = deterministic "
            "expected yield, slightly above the simulated P50). [sensitivity.csv]")
    se = pd.read_csv(r("sensitivity.csv"))
    table(pd.DataFrame({'what changes': se.driver, 'low case': se.low.map(pct), 'high case': se.high.map(pct), 'base': se.base.map(pct)}))
    row("Yield if the 6-month furnished-stay test fails", pct(k('fail6_yield')), "Nightly all year plus both vacancy taxes: the risk that matters most.")
    row("Cost of listing the furnished months on Airbnb", f"-{k('furnished_on_airbnb_yield_cost') * 100:.1f} pts",
        "The base case leases them directly; Airbnb's 15.5% fee would apply otherwise.")

    # 8 ------------------------------------------------------------------------------------------
    section(8, "DECISION 4 - SCOPE AND THE OPT-OUT TEST", "slides 10, 14",
            "A city can opt out of the principal-residence rule after two years at 3%+ rental vacancy. Rates are "
            "CMHC's published city rates (HMIP table 2.1.31.2). [validation_summary.csv]")
    row("City of Vancouver vacancy 2023 / 2024 / 2025",
        f"{k('city_vacancy_2023'):.1f}% / {k('city_vacancy_2024'):.1f}% / {k('city_vacancy_2025'):.1f}%",
        "Under 3%, so no Vancouver opt-out before June 2028: no surge of new competing listings in 2027.")
    row("2025 vacancy: Burnaby / New Westminster", f"{k('burnaby_vacancy_2025'):.1f}% / {k('new_westminster_vacancy_2025'):.1f}%",
        "New Westminster's estimate is CMHC grade d (use with caution).")
    row("2025 vacancy: Surrey / Richmond", f"{k('surrey_vacancy_2025'):.1f}% / {k('richmond_vacancy_2025'):.1f}%",
        "Already at 3%+; if 2026 also clears 3% they could opt out from June 1, 2027.")

    # 9 ------------------------------------------------------------------------------------------
    section(9, "VALIDATION", "slide 12",
            "Checks that the inputs and the ranking hold up. [value_validation.csv, validation_summary.csv]")
    sub("Our purchase-price proxy vs GVR's independent June 2026 benchmark")
    vv = pd.read_csv(r("value_validation.csv"))
    table(pd.DataFrame({'type': vv.type, 'area': vv.area, 'ours': vv.our_median_mid2026.map(usd), 'GVR': vv.gvr_benchmark_jun2026.map(usd),
                        'difference': vv.pct_diff.map(lambda v: f"{v * 100:+.1f}%")}))
    row("Area ranking stability (split-half Spearman)", f"{k('split_half_spearman'):.2f}", "1 = identical ranking in two random halves of the data; 300 splits.")
    row("Review-based occupancy vs forward calendar", f"{k('occ_calendar_spearman'):.2f}",
        "Near zero: the calendar mixes bookings and owner blocks, so it cannot validate occupancy (tested, did not hold).")
    row("Active nightly listings showing a City licence", pct(k('licence_share_active'), 0), "An estimate: listings and licences are not counted on the same basis.")

    # 10 -----------------------------------------------------------------------------------------
    section(10, "KEY ASSUMPTIONS", "slide 11",
            "Cost and tax inputs, all in data/manual/assumptions.yaml.")
    row("Airbnb host-only fee", pct(op['platform_fee_pct']))
    row("Management: nightly / furnished stays", f"{pct(op['management_pct_str'], 0)} / {pct(op['management_pct_mtr'], 0)} of revenue")
    row("Maintenance", f"{pct(op['maintenance_pct'], 0)} of revenue")
    row("Strata fee / utilities (per month, condo)", f"{usd(op['strata_fee_condo_month'])} / {usd(op['utilities_internet_condo_month'])}")
    row("Insurance (per year, condo)", usd(op['insurance_condo_year']))
    row("Property tax rate (Vancouver 2026)", f"{op['property_tax_rate'] * 100:.3f}% of value")
    row("City STR licence / provincial registration", f"{usd(op['city_str_licence_year'])} / {usd(op['provincial_registration_year'])}",
        "Licence = median fee paid on 2026 City licences (checked against open data in 06_validation.py).")
    row("Closing costs / furnishing per condo", f"{pct(cap['closing_costs_pct'])} / {usd(cap['furnishing_condo'])}")
    row("Long-term rental: management / maintenance", f"{pct(lt['management_pct'], 0)} / {pct(op['maintenance_pct'], 0)}")
    print("\n" + "=" * W)
    print(" Full step-by-step printout: outputs/run_log.txt     Every number with its source script: outputs/key_numbers.csv")
    print("=" * W)

text = buf.getvalue()
print(text)
open(r("report.txt"), "w", encoding="utf-8").write(text)
