"""Collects every number quoted in the pitch into outputs/key_numbers.csv with the file that produced it."""
import pandas as pd
from common import *
r = lambda f: os.path.join(OUT, f)
dq = pd.read_csv(r("data_quality.csv"), index_col=0)['value']
wf = pd.read_csv(r("cleaning_waterfall.csv"))
sp = pd.read_csv(r("seasonality_params.csv"), index_col=0)['value']
vs = pd.read_csv(r("validation_summary.csv"), index_col=0)['value']
seg = pd.read_csv(r("segment_summary.csv"), index_col=0)
ar = pd.read_csv(r("area_ranking.csv")).set_index(['segment', 'local_area'])
po = pd.read_csv(r("portfolio_options.csv")); po.index = po.option.str[0]
vv = pd.read_csv(r("value_validation.csv"))
br = pd.read_csv(r("revenue_bridge.csv"), index_col=0).iloc[:, 0]
se = pd.read_csv(r("sensitivity.csv")).set_index('driver')
bd = pd.read_csv(r("downtown_by_bedrooms.csv"), index_col=0)
ff = pd.read_csv(r("validation_furnished_fee.csv"), index_col=0)['value']
om = pd.read_csv(r("portfolio_operating_models.csv"))
aj = pd.read_csv(r("assessment_join.csv"), index_col=0)['value']
gvr = pd.read_csv(os.path.join(MAN, "gvr_hpi_june2026.csv"))
gvr = gvr[gvr.property_type.isin(["Apartment", "Detached"])].one_year_change_pct
dt = ar.loc[('condo_1-2br', 'Downtown')]
B = po.loc['B']
VT = load_assumptions()['taxes_if_not_rented_6_months_30day']
K = [
 ("raw_listings", dq['rows'], "01_clean_listings.py -> data_quality.csv"),
 ("comparables_final", wf.listings.iloc[-1], "01 -> cleaning_waterfall.csv"),
 ("pct_prices_from_90night_quotes", dq['price_from_90night_quote_pct'], "01 -> data_quality.csv"),
 ("pct_entire_homes_min30", dq['entire_min30plus_pct'], "01 -> data_quality.csv"),
 ("listings_at_occupancy_cap", dq['listings_at_occ_cap'], "01 -> data_quality.csv"),
 ("match_night_premium", sp['match_night_premium'], "02_seasonality.py -> seasonality_params.csv"),
 ("match_premium_ci", f"{sp['match_premium_ci_lo']:.3f}-{sp['match_premium_ci_hi']:.3f}", "02 -> seasonality_params.csv"),
 ("mar_over_jun_price", sp['mar_over_jun_price'], "02"), ("annual_adr_factor", sp['annual_adr_factor'], "02"),
 ("may_oct_revenue_share", sp['peak_may_oct_revenue_share'], "02"),
 ("rev_bridge_ia", br.iloc[0], "04_economics.py -> revenue_bridge.csv"),
 ("condo_yield_hybrid_naive_revenue", seg.loc['condo_1-2br', 'yield_hybrid_naive'], "04 -> segment_summary.csv"),
 ("house_yield_hybrid_naive_revenue", seg.loc['house_3br+', 'yield_hybrid_naive'], "04"), ("rev_bridge_str", br.iloc[2], "04"), ("rev_bridge_hybrid", br.iloc[3], "04"),
 ("condo_yield_str", seg.loc['condo_1-2br', 'yield_str'], "04 -> segment_summary.csv"),
 ("condo_yield_hybrid", seg.loc['condo_1-2br', 'yield_hybrid'], "04"),
 ("condo_yield_no_vacancy_tax", seg.loc['condo_1-2br', 'yield_str_no_vacancy_tax'], "04"),
 ("house_yield_str", seg.loc['house_3br+', 'yield_str'], "04"), ("house_yield_hybrid", seg.loc['house_3br+', 'yield_hybrid'], "04"),
 ("condo_vacancy_taxes_median", seg.loc['condo_1-2br', 'vacancy_taxes'], "04"),
 ("downtown_price", dt.price, "03_property_values.py -> acquisition_cost_by_area.csv"), ("downtown_capital", dt.capital, "04"),
 ("downtown_n", dt.n, "04 -> area_ranking.csv"), ("downtown_adr", dt.adr_2027, "04"), ("downtown_nights", dt.nights, "04"),
 ("downtown_yield_hybrid", dt.yield_hybrid, "04"), ("downtown_ci", f"{dt.yield_hybrid_ci90_lo:.3f}-{dt.yield_hybrid_ci90_hi:.3f}", "04"),
 ("ltr_benchmark_yield", vs['ltr_benchmark_yield'], "06_validation.py -> validation_summary.csv"),
 ("ltr_benchmark_yield_house", vs['ltr_benchmark_yield_house'], "06_validation.py -> validation_summary.csv"),
 ("ltr_rent_condo_month", vs['ltr_rent_condo_month'], "06_validation.py (StatCan 46-10-0092-01, Q1 2026 asking rent)"),
 ("ltr_rent_house_month", vs['ltr_rent_house_month'], "06_validation.py (StatCan 46-10-0092-01, Q1 2026 asking rent)"),
 ("B_units", B.units, "05_portfolio.py -> portfolio_options.csv"), ("B_capital", B.capital_deployed, "05"),
 ("B_noi_p10", B.noi_p10, "05"), ("B_noi_p50", B.noi_p50, "05"), ("B_noi_p90", B.noi_p90, "05"), ("B_p10", B.yield_p10, "05"), ("B_p50", B.yield_p50, "05"), ("B_p90", B.yield_p90, "05"),
 ("B_yield_on_10m", B.yield_on_10m_p50, "05"), ("A_p50", po.loc['A'].yield_p50, "05"), ("A_prob_below_2", po.loc['A'].prob_yield_below_2pct, "05"),
 ("C_p50", po.loc['C'].yield_p50, "05"), ("B_spread", B.spread_p90_p10, "05"), ("C_spread", po.loc['C'].spread_p90_p10, "05"),
 ("B_yield_nightly_all_year", om.yield_p50.iloc[0], "05 -> portfolio_operating_models.csv (P50, same 10,000 years)"),
 ("B_yield_hybrid", om.yield_p50.iloc[1], "05 -> portfolio_operating_models.csv (= B_p50)"),
 ("B_yield_long_term_rental", om.yield_p50.iloc[2], "05 -> portfolio_operating_models.csv"),
 ("B_yield_hybrid_naive_revenue", ff['hybrid_yield_naive_revenue_p50'], "05 -> validation_furnished_fee.csv (D2 check)"),
 ("fail6_yield", se.iloc[-1].low, "05 -> sensitivity.csv (P50, nightly all year + EHT + SVT)"),
 ("vacancy_taxes_per_downtown_condo", dt.price * (VT['empty_homes_tax_pct'] + VT['svt_pct']), "08 (Downtown price x (3% EHT + 1% SVT))"),
 ("matched_listings_mar_jun", sp['matched_listings'], "02 -> seasonality_params.csv"),
 ("long_stay_quote_min_price", dq['long_stay_quote_min_price'], "01 -> data_quality.csv"),
 ("gvr_one_year_change_range", f"{gvr.max():.1f} to {gvr.min():.1f}", "data/manual/gvr_hpi_june2026.csv (apartment + detached)"),
 ("assessment_join_pct", aj['folios_matched_to_parcel_and_local_area_pct'], "03 -> assessment_join.csv"),
 ("value_check_range", f"{vv.pct_diff.min():+.3f} to {vv.pct_diff.max():+.3f}", "03 -> value_validation.csv"),
 ("occ_calendar_spearman", vs['occ_vs_calendar_spearman'], "06"), ("split_half_spearman", vs['split_half_spearman_median'], "06"),
 ("city_vacancy_2023", vs['city_vacancy_2023'], "06 (CMHC HMIP 2.1.31.2, Vancouver CY)"),
 ("city_vacancy_2024", vs['city_vacancy_2024'], "06 (CMHC HMIP 2.1.31.2, Vancouver CY)"), ("city_vacancy_2025", vs['city_vacancy_2025'], "06 (CMHC HMIP 2.1.31.2, Vancouver CY)"),
 ("burnaby_vacancy_2025", vs['vacancy_2025_Burnaby'], "06"), ("new_westminster_vacancy_2025", vs['vacancy_2025_New Westminster'], "06 (CMHC reliability d)"),
 ("surrey_vacancy_2025", vs['vacancy_2025_Surrey'], "06"), ("richmond_vacancy_2025", vs['vacancy_2025_Richmond'], "06"),
 ("city_str_licence_fee", vs['city_str_licence_fee_2026_median'], "06 (Vancouver Open Data, 2026 median fee paid)"),
 ("furnished_on_airbnb_yield_cost", ff['furnished_on_airbnb_yield_cost'], "05 -> validation_furnished_fee.csv"),
 ("reserve_years_of_vacancy_tax", (10e6 - B.capital_deployed) / (B.units * dt.price * (VT['empty_homes_tax_pct'] + VT['svt_pct'])), "08 (reserve / 12 units x EHT+SVT on the Downtown price)"),
 ("licence_share_active", vs['citywide_share_active_nightly_showing_licence'], "06"),
 ("downtown_1br_share", bd.loc[1.0, 'n'] / bd.n.sum(), "06 -> downtown_by_bedrooms.csv"),
]
pd.DataFrame(K, columns=['key', 'value', 'produced_by']).to_csv(r("key_numbers.csv"), index=False)
print(pd.DataFrame(K, columns=['key', 'value', 'produced_by']).to_string(index=False))
