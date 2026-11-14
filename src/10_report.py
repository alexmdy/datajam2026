"""Every number shown in the pitch deck, slide by slide, with what kind of number it is and how it was made.
Prints to the screen and writes outputs/report.txt. It only READS files written by steps 01-09; it computes
nothing new except simple arithmetic shown on the line (e.g. price x tax rate), so every number traces back.

How to read a line:
    Label ..................................... value          (as rounded on the slide)
        WHAT: the kind of number (count, median, P50 of a simulation, lower quartile, assumption, ...)
        HOW:  how it was calculated
        FROM: script -> output file
"""
import json, io, contextlib
import pandas as pd, numpy as np
from common import *

r = lambda f: os.path.join(OUT, f)
K = pd.read_csv(r("key_numbers.csv")).set_index('key')['value']
def k(name): return float(K[name])
A = load_assumptions(); op, cap, lt, vt, rv = A['operating'], A['capital'], A['long_term_rental'], A['taxes_if_not_rented_6_months_30day'], A['revenue']
D = json.load(open(r("deck_data.json")))
csv = lambda f, **kw: pd.read_csv(r(f), **kw)
DQ = csv("data_quality.csv", index_col=0)['value']; SP = csv("seasonality_params.csv", index_col=0)['value']
VS = csv("validation_summary.csv", index_col=0)['value']; PO = csv("portfolio_options.csv"); PO.index = PO.option.str[0]
OM = csv("portfolio_operating_models.csv"); SE = csv("sensitivity.csv"); AR = csv("area_ranking.csv")
BR = csv("revenue_bridge.csv", index_col=0).iloc[:, 0]; MT = csv("mtr_rent_by_bedrooms.csv").set_index('br')['monthly_rent_q']
W = 96

# ---------- formatting ----------
def pct(v, d=1): return f"{v * 100:.{d}f}%"
def usd(v): return f"${v:,.0f}"
def r10k(v): return f"${round(v, -4) / 1000:,.0f}k"
def wrap(text, width):
    out, line = [], ""
    for w in str(text).split():
        if len(line) + len(w) + 1 > width: out.append(line); line = w
        else: line = (line + " " + w).strip()
    return out + [line] if line else out
def slide(n, title, who=""):
    print("\n" + "#" * W); print(f" SLIDE {n}  |  {title}"); print("#" * W)
def chart(title):
    print(f"\n  >> {title}"); print("  " + "-" * (W - 2))
def num(label, value, what, how="", src="", slide_shows=""):
    v = f"{value}" + (f"   (slide: {slide_shows})" if slide_shows else "")
    print(f"    {label + ' ':.<56} {v}")
    for tag, txt in (("WHAT", what), ("HOW ", how), ("FROM", src)):
        if txt:
            lines = wrap(txt, W - 16)
            print(f"        {tag}: {lines[0]}")
            for l in lines[1:]: print(" " * 14 + l)
def table(df, note="", left=False):
    cols = list(df.columns); cells = [[str(v) for v in df[c]] for c in cols]
    wid = [max(len(c), *(len(v) for v in col)) for c, col in zip(cols, cells)]
    fmt = lambda vals: "  ".join(v.ljust(w) if (i == 0 or left) else v.rjust(w) for i, (v, w) in enumerate(zip(vals, wid)))
    print("      " + fmt(cols)); print("      " + "  ".join("-" * w for w in wid))
    for i in range(len(df)): print("      " + fmt([col[i] for col in cells]))
    for line in wrap(note, W - 8): print("      " + line)

SIM = "P50 (median) of 10,000 simulated versions of 2027 for the 12 Downtown condos"
YIELD_HOW = "portfolio NOI / all-in capital (price + transfer tax + closing + furnishing), unlevered, no appreciation"
dt = AR[(AR.segment == 'condo_1-2br') & (AR.local_area == 'Downtown')].iloc[0]
price, capital = dt.price, dt.capital
taxes = price * (vt['empty_homes_tax_pct'] + vt['svt_pct'])
B = PO.loc['B']

buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    print("=" * W)
    print(" DDD x DataJam 2026  --  EVERY NUMBER IN THE PITCH, SLIDE BY SLIDE")
    print(" Yield = 2027 net operating income / all-in capital. P10/P50/P90 = 10th/50th/90th percentile of 10,000")
    print(" simulated 2027s (P10 = a bad year, P50 = the median year, P90 = a good year). Full data: outputs/*.csv")
    print("=" * W)

    # ================================================================================== SLIDE 1
    slide(1, "Recommendation: buy 12 Downtown Vancouver condos and run them seasonally")
    num("Condos to buy (Downtown, 1-2 bedroom)", f"{B.units:.0f}",
        "count chosen by the budget rule", "as many Downtown condos as fit in $9.7M (the $10M mandate minus a 3% cash buffer) "
        f"at {usd(capital)} all-in each", "05_portfolio.py -> portfolio_options.csv")
    num("Share 1-bedroom", pct(k('downtown_1br_share'), 0), "share of the 475 Downtown comparables that are 1-bedroom (rest 2-bedroom)",
        "count of 1BR / count of all Downtown 1-2BR comparables", "06_validation.py -> downtown_by_bedrooms.csv", "about 60%")
    num("Capital deployed", usd(B.capital_deployed), "sum over the 12 units", f"12 x {usd(capital)} all-in (price {usd(price)} + "
        f"BC property transfer tax + {cap['closing_costs_pct']:.1%} closing + {usd(cap['furnishing_condo'])} furnishing)",
        "05 -> portfolio_options.csv", "$9.0M")
    num("Reserve", usd(cap['mandate_cad'] - B.capital_deployed), "arithmetic", "$10,000,000 - capital deployed", "", "$1.0M")
    num("2027 net operating income", usd(B.noi_p50), SIM, "nightly revenue May-Oct + 6 months furnished rent, minus Airbnb fee, "
        "management, maintenance, strata, utilities, insurance, property tax and licences", "05 -> portfolio_options.csv", r10k(B.noi_p50))
    num("  NOI range", f"{usd(B.noi_p10)} - {usd(B.noi_p90)}", "P10 and P90 of the same 10,000 simulated years", "", "05",
        f"{r10k(B.noi_p10)}-{r10k(B.noi_p90)}")
    num("2027 net yield on capital deployed", pct(B.yield_p50), SIM, YIELD_HOW, "05 -> portfolio_options.csv")
    num("  Yield range", f"{pct(B.yield_p10)} - {pct(B.yield_p90)}", "P10 and P90 of the same simulation", "", "05")
    num("Empty Homes Tax / Speculation and Vacancy Tax", f"{vt['empty_homes_tax_pct']:.0%} / {vt['svt_pct']:.0%}",
        "published tax rates (assumptions.yaml)", "City of Vancouver Vacancy Tax By-law (3% for 2026); BC SVT 1% for Canadian owners", "data/manual/assumptions.yaml")

    # ================================================================================== SLIDE 2
    slide(2, "The decision, our return metric, and the 1,809 listings selected for comparison")
    chart("Chart: Cleaning, 6,509 listings to 1,809 comparables")
    wf = csv("cleaning_waterfall.csv"); wf['removed'] = (-wf.listings.diff()).fillna(0).astype(int)
    table(wf.rename(columns={'step': 'filter', 'listings': 'left'}), "WHAT: counts of listings left after each filter, applied in this "
          "order. FROM: 01_clean_listings.py -> cleaning_waterfall.csv")
    num("Benchmark price fall, year to June 2026", "{} to {}%".format(*[x.strip().lstrip('-') for x in K['gvr_one_year_change_range'].split('to')]), "published GVR MLS Home Price Index one-year change "
        "(Vancouver West/East, apartment and detached), transcribed", "the reason appreciation is left out of the return metric",
        "data/manual/gvr_hpi_june2026.csv", "5.6-9.6%")

    # ================================================================================== SLIDE 3
    slide(3, "Where and what: Downtown 1-2 bedroom condos lead on yield")
    chart("Chart: Median 2027 net yield, seasonal hybrid (bar = 90% bootstrap CI), areas with 20+ comparables")
    t = AR.sort_values('yield_hybrid', ascending=False)
    table(pd.DataFrame({"area": t.local_area, "type": np.where(t.segment.str.startswith('condo'), "condo 1-2BR", "house 3BR+"), "n": t.n,
                        "price": [f"${v/1000:,.0f}k" for v in t.price], "median yield": [pct(v) for v in t.yield_hybrid],
                        "90% CI": [f"{pct(a)}-{pct(b)}" for a, b in zip(t.yield_hybrid_ci90_lo, t.yield_hybrid_ci90_hi)]}),
          "WHAT: median of each area's comparables' single-unit 2027 yields (no simulation shocks), with a 90% bootstrap confidence "
          "interval (2,000 resamples) on that median. Used to RANK areas; the portfolio number (4.1%) is lower because the "
          "simulation adds a launch ramp-up and winter rent at 70-100% of ask. FROM: 04_economics.py -> area_ranking.csv")
    num("Downtown comparables", f"{dt.n:.0f}", "count of Downtown 1-2BR condo comparables", "", "04 -> area_ranking.csv")
    num("Downtown nightly rate x nights", f"${dt.adr_2027:,.0f} x {dt.nights:.0f}", "medians across the 475 comparables",
        "rate = June quote, World Cup premium removed, x 0.91 seasonal factor; nights = Inside Airbnb review-based estimate, last 12 months",
        "04 -> area_ranking.csv", "$417 x 156")
    num("Downtown purchase price", usd(price), "median 2026 assessed value of Downtown strata units x GVR one-year change",
        f"{usd(csv('acquisition_cost_by_area.csv').set_index(['local_area','segment']).loc[('Downtown','condo_1-2br'),'assessed_median'])} x 0.944",
        "03_property_values.py -> acquisition_cost_by_area.csv", "about $707k")
    hs = AR[(AR.local_area == 'Hastings-Sunrise')].iloc[0]
    num("Houses vs condos (same chart)", f"best house area {pct(hs.yield_hybrid)} vs Downtown condo {pct(dt.yield_hybrid)}",
        "area medians from the chart above", f"a house costs {hs.price/price:.1f}-{AR[AR.local_area=='Kensington-Cedar Cottage'].price.iloc[0]/price:.1f}x a "
        "Downtown condo but does not earn 2-3x the nightly revenue", "04 -> area_ranking.csv")
    ev = csv("validation_downtown_event_check.csv", index_col=0)
    num("World Cup test: June/March price, Downtown", f"{ev.loc['Downtown','june_over_march_price']:.2f}",
        "median ratio of each listing's June quote to its own March quote", "", "06_validation.py -> validation_downtown_event_check.csv")
    oth = ev.drop('Downtown').june_over_march_price
    num("  same ratio, other areas", f"{oth.min():.2f}-{oth.max():.2f}", "same median ratio, other condo areas", "", "06")
    num("  Downtown rank on June / March prices", f"{ev.loc['Downtown','rank_june']:.0f} / {ev.loc['Downtown','rank_march']:.0f}",
        "rank of median nightly revenue, re-computed with March prices", "", "06", "top two")

    # ================================================================================== SLIDE 4
    slide(4, "Operating model (Decision 1): nightly all year loses money; the seasonal hybrid earns over 4%")
    chart("Chart (left): 2027 net yield by operating model -- 12 Downtown condos")
    for i, (lab, how) in enumerate([("Nightly all year", "nightly revenue all 12 months after fees and costs, MINUS the vacancy taxes "
                                     "(3% EHT + 1% SVT), because a unit rented under 30 days counts as vacant"),
                                    ("Seasonal hybrid (our plan)", "nightly May-Oct + furnished 30+ night stays Jan-Apr and Nov-Dec; no "
                                     "vacancy taxes. Same number as slide 1"),
                                    ("Long-term rental", f"12-month lease at {usd(OM.ltr_rent_month.iloc[0])}/month (StatCan Q1 2026 "
                                     f"average asking rent, Downtown 1BR/2BR mix), {lt['management_pct']:.0%} management, "
                                     f"{op['maintenance_pct']:.0%} maintenance, strata, landlord insurance, property tax; unfurnished")]):
        num(lab, pct(OM.yield_p50.iloc[i]), SIM + " (the same simulated years for all three bars)", how,
            "05_portfolio.py -> portfolio_operating_models.csv")
    print()
    num("Vacancy taxes per condo if nightly all year", usd(taxes), "arithmetic on the Downtown purchase price",
        f"{usd(price)} x ({vt['empty_homes_tax_pct']:.0%} EHT + {vt['svt_pct']:.0%} SVT) = {usd(taxes)}", "08 -> key_numbers.csv", "about $28k")
    num("Share of nightly revenue in Nov-Apr", pct(1 - SP['peak_may_oct_revenue_share'], 0), "share of a year's nightly revenue",
        "monthly night share (2024-25 reviews, as a proxy for stays) x monthly price index, summed over Nov-Apr", "02_seasonality.py -> seasonality_params.csv")
    chart("Chart (right): Median Downtown condo, net income per month after fees")
    mc = D['month_compare']; mo = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    plan = ["furnished"] * 4 + ["nightly"] * 6 + ["furnished"] * 2
    table(pd.DataFrame({"month": mo, "nightly": [usd(v) for v in mc['nightly']], "furnished": [usd(v) for v in mc['furnished']],
                        "higher": ["furnished" if f > n else "nightly" for n, f in zip(mc['nightly'], mc['furnished'])], "plan": plan}),
          f"NIGHTLY = median over the {mc['n']} Downtown comparables of (annual nightly revenue x that month's revenue share x "
          f"(1 - {op['platform_fee_pct']:.1%} Airbnb - {op['management_pct_str']:.0%} management - {op['maintenance_pct']:.0%} maintenance)). "
          f"FURNISHED = median Downtown comparable's furnished monthly rent x (1 - {op['management_pct_mtr']:.0%} - {op['maintenance_pct']:.0%}); "
          f"for the median (1-bedroom) unit that is {usd(MT.loc[1.0])} x 0.85. Flat: one snapshot has no month-by-month furnished rents. "
          "October: furnished is higher but rests on an asking rent, so October stays nightly. FROM: 09_deck_data.py -> deck_data.json")
    num("Furnished monthly ask, 1BR / 2BR", f"{usd(MT.loc[1.0])} / {usd(MT.loc[2.0])}",
        "LOWER QUARTILE (25th percentile) of Airbnb monthly-stay asking prices, entire homes with a 30+ night minimum, city-wide",
        "the conservative end of what monthly guests are asked; the simulation then assumes only 70-100% of it is achieved",
        "04_economics.py -> mtr_rent_by_bedrooms.csv")

    # ================================================================================== SLIDE 5
    slide(5, "Clean revenue (Decision 2): June 2026 quotes overstate a normal year by about 12%")
    num("Prices that are long-stay quotes (28+ nights)", f"{DQ['price_from_90night_quote_pct']}%", "share of all 6,509 listings",
        "price quote check-out minus check-in >= 28 nights (mostly 90)", "01 -> data_quality.csv", "22%")
    num("  lowest 'nightly' price among them", f"${float(DQ['long_stay_quote_min_price']):.2f}", "minimum", "why only quotes of 7 nights or fewer are kept",
        "01 -> data_quality.csv", "as low as $6")
    num("World Cup match-night premium", pct(SP['match_night_premium']), "difference in MEAN log(June price / March price) between stays "
        "touching a BC Place match night and the same listings' other stays, converted to %",
        f"{SP['matched_listings']:.0f} listings priced in both March and June; {SP['match_stays']:.0f} match stays vs {SP['nonmatch_stays']:.0f} others; "
        "March price is the control", "02_seasonality.py -> seasonality_params.csv", "5.8%")
    num("  95% confidence interval", f"{pct(SP['match_premium_ci_lo'])} - {pct(SP['match_premium_ci_hi'])}", "bootstrap, 2,000 resamples", "", "02")
    num("Late-March price as a share of June", pct(SP['mar_over_jun_price'], 0), "geometric mean of each listing's March/June price ratio "
        "(non-match stays only)", "same listings in both snapshots, so it is seasonality, not a different mix", "02", "72%")
    num("Seasonal average rate = this x June price", f"{SP['annual_adr_factor']:.2f}", "night-weighted average of a monthly price index (June = 1)",
        f"index = (month's demand / June demand) ^ {SP['beta']:.2f}; demand = 2024-25 review counts by month; the exponent is fitted so "
        "late March = 72% of June", "02 -> seasonality_monthly.csv, seasonality_params.csv", "0.91")
    chart("Chart: Median 1-2BR condo comparable (city-wide, n=706), annual gross revenue")
    num("Inside Airbnb method (June quote x nights)", usd(BR.iloc[0]), "median across the 706 condo comparables", "", "04 -> revenue_bridge.csv", "$64.8k")
    num("Remove World Cup premium", usd(BR.iloc[1]), "median", "", "04", "$62.3k")
    num("Seasonal average rate (nightly all year)", usd(BR.iloc[2]), "median", "June quote / 1.058 if a match stay, x 0.91, x nights", "04", "$57.0k")
    num("Seasonal hybrid (our plan)", usd(BR.iloc[3]), "median", "73% of nightly revenue (May-Oct) + 6 x furnished monthly rent", "04", "$67.0k")
    num("Change, Inside Airbnb method -> corrected", pct(BR.iloc[2] / BR.iloc[0] - 1, 0), "arithmetic", "$57.0k / $64.8k - 1", "", "-12%")

    # ================================================================================== SLIDE 6
    slide(6, "Expected 2027 and risks")
    num("2027 net yield on capital deployed", pct(B.yield_p50), SIM, "", "05", "4.1%")
    num("  range", f"{pct(B.yield_p10)} - {pct(B.yield_p90)}", "P10 - P90", "", "05", "3.1%-5.3%")
    num("Yield on the full $10M", pct(B.yield_on_10m_p50), "P50 NOI / $10,000,000 (the reserve earns nothing)", "", "05", "3.7%")
    num("NOI", f"{usd(B.noi_p50)} ({usd(B.noi_p10)} - {usd(B.noi_p90)})", "P50 (P10 - P90)", "", "05", "$370k ($280k-$470k)")
    chart("Chart: Change in portfolio yield vs the 4.1% base -- one assumption changed at a time")
    se = SE.copy(); se['change'] = [f"{(lo - b) * 100:+.2f} / {(hi - b) * 100:+.2f} pts" for lo, hi, b in zip(se.low, se.high, se.base)]
    table(pd.DataFrame({"what changes": se.driver, "low": [pct(v) for v in se.low], "high": [pct(v) for v in se.high],
                        "base": [pct(v) for v in se.base], "vs base": se.change}),
          "WHAT: each cell is the P50 of the SAME 10,000 simulated years with one assumption changed, so the base is exactly "
          "the slide 1 number. The FAILED row = nightly all year plus both vacancy taxes (the slide 4 left bar). "
          "FROM: 05_portfolio.py -> sensitivity.csv")
    num("Yield if the 6-month furnished-stay test fails", pct(k('fail6_yield')), SIM + ", nightly all year + 3% EHT + 1% SVT", "", "05 -> sensitivity.csv")
    num("Reserve covers this many years of the tax", f"{k('reserve_years_of_vacancy_tax'):.1f}", "arithmetic",
        f"{usd(cap['mandate_cad'] - B.capital_deployed)} / (12 x {usd(taxes)})", "08 -> key_numbers.csv", "about 3 years")
    num("City of Vancouver rental vacancy, 2025", f"{k('city_vacancy_2025'):.1f}%", "CMHC published city rate, October survey (HMIP 2.1.31.2)",
        "under the 3% opt-out test, so no Vancouver opt-out in 2027", "06 -> validation_summary.csv")

    # ================================================================================== SLIDE 7
    slide(7, "How many (Decision 3): 12 modest condos beat 5 high-value houses")
    chart("Chart: 2027 net yield on capital deployed, P10 / P50 / P90 of 10,000 simulations")
    table(pd.DataFrame({"portfolio": [o.split(':')[0] + ':' + o.split(':')[1][:24] for o in PO.option], "units": PO.units,
                        "capital": [f"${v/1e6:.2f}M" for v in PO.capital_deployed], "P10": [pct(v) for v in PO.yield_p10],
                        "P50": [pct(v) for v in PO.yield_p50], "P90": [pct(v) for v in PO.yield_p90],
                        "P90-P10": [f"{v*100:.1f} pts" for v in PO.spread_p90_p10], "P(<2%)": [pct(v) for v in PO.prob_yield_below_2pct]}),
          "WHAT: percentiles of 10,000 simulated 2027 portfolio yields. HOW: each unit draws a random real comparable from its area "
          "(unit-level luck); every unit shares the same market shocks: nightly rate (normal, sd 7%), occupancy (normal, sd 8%), "
          "furnished rent (uniform 70-100% of ask), launch ramp-up (uniform 85-100%), price paid (normal, sd 3%). "
          "FROM: 05_portfolio.py -> portfolio_options.csv")
    for o in PO.option: print("      " + o + "  ->  " + PO.set_index('option').loc[o, 'mix'])
    num("3 areas vs Downtown only: change in median", f"{(PO.loc['C'].yield_p50 - B.yield_p50) * 100:+.1f} pts", "difference of P50s", "", "05", "-0.3 pts")

    # ================================================================================== SLIDE 8
    slide(8, "Next steps, and how DDD will know the plan is working")
    num("Units / mix", f"{B.units:.0f} units, {pct(k('downtown_1br_share'), 0)} 1BR", "see slide 1", "", "05, 06")
    num("NOI plan / P10 trigger", f"{r10k(B.noi_p50)} / {r10k(B.noi_p10)}", "P50 / P10 of the simulation", "", "05")
    num("Furnished months needed per unit", f"{rv['mtr_months']}", "rule: 6 months of 30+ day rentals in the calendar year", "", "assumptions.yaml")
    print("      (6+ buildings, 'Sep 30 trigger' and the dates are plan choices, not computed numbers.)")

    # ================================================================================== SLIDES 9-10
    slide("9-10", "Decision log (appendix) -- every number repeats one shown above")
    num("D1 nightly / hybrid / long-term", " / ".join(pct(v) for v in OM.yield_p50), SIM, "", "05 -> portfolio_operating_models.csv")
    num("D1 vacancy taxes per condo", usd(taxes), "see slide 4", "", "08", "about $28k")
    num("D2 hybrid yield: naive revenue vs corrected", f"{pct(k('B_yield_hybrid_naive_revenue'))} vs {pct(B.yield_p50)}", SIM +
        "; the naive run swaps in Inside Airbnb's revenue (June quote x nights)", "", "05 -> validation_furnished_fee.csv", "about 0.5 pt")
    num("D3 houses P50 / P(<2%)", f"{pct(PO.loc['A'].yield_p50)} / {pct(PO.loc['A'].prob_yield_below_2pct, 0)}", "see slide 7", "", "05")
    num("D3 Downtown condos P50 / P10", f"{pct(B.yield_p50)} / {pct(B.yield_p10)}", "see slide 7", "", "05")
    num("D3 3-area mix P50, spread vs Downtown spread", f"{pct(PO.loc['C'].yield_p50)}, {PO.loc['C'].spread_p90_p10*100:.1f} vs {B.spread_p90_p10*100:.1f} pts", "see slide 7", "", "05")
    print("    D4 (scope): the vacancy rates are on slide 14 below.")

    # ================================================================================== SLIDE 11
    slide(11, "Key assumptions (all in data/manual/assumptions.yaml unless a script is named)")
    rows = [("Purchase price, Downtown condo", usd(price), "median 2026 assessment x GVR change (slide 3)"),
            ("Transfer tax brackets", "1% / 2% / 3% / +2%", "BC PTT (gov.bc.ca)"),
            ("Closing / furnishing per condo", f"{cap['closing_costs_pct']:.1%} / {usd(cap['furnishing_condo'])}", "assumption"),
            ("Airbnb host-only fee", f"{op['platform_fee_pct']:.1%}", "Airbnb standard for Canadian hosts"),
            ("Management nightly / furnished; maintenance", f"{op['management_pct_str']:.0%} / {op['management_pct_mtr']:.0%}; {op['maintenance_pct']:.0%}", "assumption, % of revenue"),
            ("Strata / utilities (per month); insurance (per year)", f"{usd(op['strata_fee_condo_month'])} / {usd(op['utilities_internet_condo_month'])}; {usd(op['insurance_condo_year'])}", "assumption"),
            ("Property tax rate", f"{op['property_tax_rate']*100:.3f}% of value", "City of Vancouver 2026"),
            ("City STR licence / provincial registration", f"{usd(op['city_str_licence_year'])} / {usd(op['provincial_registration_year'])}", "licence = MEDIAN fee paid on 2026 City licences (06 checks it)"),
            ("Vacancy taxes if the 6-month test fails", f"{vt['empty_homes_tax_pct']:.0%} EHT + {vt['svt_pct']:.0%} SVT", "of assessed value"),
            ("Furnished rent, 1BR / 2BR", f"{usd(MT.loc[1.0])} / {usd(MT.loc[2.0])}", "LOWER QUARTILE of monthly asks; simulated at 70-100%; 6 months, leased directly"),
            ("Occupancy", f"capped at {DQ['est_occupancy_cap_nights']} nights", "Inside Airbnb review-based estimate, last 12 months"),
            ("Long-term rent, condo / house", f"{usd(k('ltr_rent_condo_month'))} / {usd(k('ltr_rent_house_month'))}", f"StatCan Q1 2026 AVERAGE asking rent; {lt['management_pct']:.0%} mgmt, {op['maintenance_pct']:.0%} maint."),
            ("Simulation shocks", "rate sd 7%, occupancy sd 8%", "ramp-up 85-100%, price paid sd 3% (05_portfolio.py)"),
            ("Reserve", usd(cap['mandate_cad'] - B.capital_deployed), f"a 13th unit would bring capital to {usd(B.capital_deployed + capital)}, "
             f"over the {usd(cap['mandate_cad'] * (1 - cap['cash_reserve_pct']))} limit (3% cash buffer)")]
    table(pd.DataFrame(rows, columns=["assumption", "value", "source / note"]), left=True)

    # ================================================================================== SLIDE 12
    slide(12, "Validation, what didn't hold, and limitations")
    vv = csv("value_validation.csv")
    table(pd.DataFrame({"type": vv.type, "area": vv.area, "ours": [usd(v) for v in vv.our_median_mid2026],
                        "GVR": [usd(v) for v in vv.gvr_benchmark_jun2026], "difference": [f"{v*100:+.1f}%" for v in vv.pct_diff]}),
          "WHAT: our purchase-price proxy (median assessed value x GVR change) vs GVR's independent June 2026 benchmark price. "
          "FROM: 03_property_values.py -> value_validation.csv")
    num("Area ranking stability", f"{VS['split_half_spearman_median']:.2f}", "MEDIAN Spearman rank correlation between area rankings built "
        "from two random halves of the comparables, over 300 random splits (1 = identical ranking)", "", "06 -> validation_summary.csv")
    num("Assessment folios joined to a parcel and local area", f"{k('assessment_join_pct'):.0f}%", "share of 2026 assessment records",
        "", "03 -> assessment_join.csv")
    num("Listings inside a City local area", f"{100 - float(DQ['outside_city_polygons']) / float(DQ['rows']) * 100:.0f}%", "share, by point-in-polygon", "", "01 -> data_quality.csv")
    num("Review-based occupancy vs forward calendar", f"{VS['occ_vs_calendar_spearman']:.2f}", f"Spearman rank correlation, "
        f"{VS['occ_vs_calendar_n']:.0f} listings: estimated nights vs share of the next 90 days marked unavailable",
        "near zero: 'unavailable' mixes bookings and owner blocks, so the calendar cannot validate occupancy (tested, did not hold)", "06")
    num("Comparables at the 255-night cap", pct(VS['share_at_255_night_cap'], 0), "share of comparables", "", "06", "17%")
    num("Cost of listing the furnished months on Airbnb", f"-{k('furnished_on_airbnb_yield_cost')*100:.1f} pts",
        "change in P50 yield if the 15.5% Airbnb fee also hits the furnished rent", "", "05 -> validation_furnished_fee.csv", "-0.5 pt")

    # ================================================================================== SLIDE 13
    slide(13, "Data-quality checks on the 15 June 2026 snapshot (all counts / shares)")
    rows = [("Rows / unique ids", f"{DQ['rows']} / {DQ['unique_ids']}"), ("Columns in the download / kept", f"{DQ['columns_in_download']} / {DQ['columns_kept_after_sanitizing']} (16 identifying columns removed)"),
            ("Scrape days (listings per day)", DQ['scrape_dates']), ("Price missing", f"{DQ['price_missing_pct']}%"),
            ("Price from 28+ night quotes", f"{DQ['price_from_90night_quote_pct']}%"), ("Price under $30 / over $3,000", f"{DQ['price_lt_30_count']} / {DQ['price_gt_3000_count']}"),
            ("Entire homes requiring 30+ nights", f"{DQ['entire_min30plus_pct']}%"), ("Occupancy cap / listings at the cap", f"{DQ['est_occupancy_cap_nights']} / {DQ['listings_at_occ_cap']}"),
            ("Neighbourhood labels: Inside Airbnb vs City", f"{DQ['ia_neighbourhood_labels']} vs 22"), ("Licence field blank", f"{DQ['no_licence_text_pct']}%"),
            ("Active nightly listings showing a City licence", pct(VS['citywide_share_active_nightly_showing_licence'], 0) + " (ESTIMATE)"),
            ("March 2026 snapshot: listings matched to June", f"{SP['matched_listings']:.0f}")]
    table(pd.DataFrame(rows, columns=["check", "value"]), left=True, note="FROM: 01_clean_listings.py -> data_quality.csv; 02 -> seasonality_params.csv; 06 -> validation_summary.csv")

    # ================================================================================== SLIDE 14
    slide(14, "Decision 4 evidence: Vancouver is below the 3% opt-out test; several suburbs are above it")
    chart("Chart: Purpose-built rental vacancy, October (CMHC published city rates)")
    table(pd.DataFrame(D['vacancy'], columns=["city / year", "vacancy %"]),
          "WHAT: CMHC Rental Market Survey published city rates (HMIP table 2.1.31.2); New Westminster is CMHC reliability grade d. "
          "FROM: 06_validation.py -> validation_summary.csv")

    # ================================================================================== SLIDE 15
    slide(15, "AI use and reproducibility")
    print("    No numbers. Every number above is regenerated by:  python run_all.py   (add --download on a fresh clone)")
    print("    Each number with the script that made it: outputs/key_numbers.csv")
    print("\n" + "=" * W)

text = buf.getvalue()
print(text, end="")
open(r("report.txt"), "w", encoding="utf-8").write(text)
