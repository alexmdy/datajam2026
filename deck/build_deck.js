// Builds the pitch deck from outputs/deck_data.json (produced by src/09_deck_data.py).
const pptxgen = require("pptxgenjs");
const path = require("path");
const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");
const D = require(path.join(__dirname, "..", "outputs", "deck_data.json"));
const K = D.k;
const pct = (v, d = 1) => (v * 100).toFixed(d) + "%";
const k$ = (v) => "$" + Math.round(v / 1000).toLocaleString("en-US") + "k";
const r10k = (v) => "$" + (Math.round(v / 10000) * 10).toLocaleString("en-US") + "k";
const m$ = (v) => "$" + (v / 1e6).toFixed(1) + "M";

const THEME = { name: "DDD Vancouver", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "0B1B2B", lt1: "FFFFFF", dk2: "0E2A47", lt2: "EEF3F8", accent1: "2A78D6", accent2: "EB6834",
            accent3: "75746F", accent4: "1BAF7A", accent5: "E34948", accent6: "6250D6", hlink: "2A78D6", folHlink: "6250D6" } };
const HEX = { blue: "2A78D6", lblue: "9EC5F4", grey: "75746F", lgrey: "C9C8C3", red: "E34948", white: "FFFFFF", ink2: "52514E", grid: "E6E5E1" };

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "DDD Vancouver STR recommendation - DataJam 2026";
const C = pres.SchemeColor;
const CREDIT = "Data: Inside Airbnb, Vancouver, 15 June 2026, CC BY 4.0. Other sources: City of Vancouver Open Data, CMHC, GVR (see appendix).";

pres.defineSlideMaster({ title: "DARK", background: { color: C.text2 },
  objects: [{ text: { text: CREDIT, options: { x: 0.5, y: 5.22, w: 8.6, h: 0.3, fontSize: 9, color: C.background2, isTextBox: true } } }],
  placeholders: [] ,
});
pres.defineSlideMaster({ title: "CONTENT", background: { color: C.background1 },
  margin: [0.3, 0.5, 0.45, 0.5],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.28, w: 8.35, h: 0.8, fontFace: "Cambria", fontSize: 22, bold: true, color: C.text2, valign: "top", align: "left", margin: 0 }, text: "" } },
    { text: { text: CREDIT, options: { x: 0.5, y: 5.25, w: 8.4, h: 0.25, fontSize: 8, color: C.accent3, isTextBox: true, margin: 0 } } },
  ],
  slideNumber: { x: 9.1, y: 5.22, w: 0.4, h: 0.28, fontSize: 9, color: C.accent3, align: "right" },
});

const AX = { catAxisLabelColor: HEX.ink2, valAxisLabelColor: HEX.ink2, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 10, valAxisLabelFontSize: 9, valGridLine: { color: HEX.grid, size: 0.5 }, catGridLine: { style: "none" },
  dataLabelFontFace: "+mn-lt", dataLabelFontSize: 10, legendFontFace: "+mn-lt", legendFontSize: 10, titleFontFace: "+mn-lt",
  catAxisLineColor: HEX.lgrey, valAxisLineShow: false, catAxisLabelPos: "low" };

function title(s, t) { s.addText(t, { placeholder: "title" }); }
function badge(s, label) {
  s.addShape(pres.shapes.OVAL, { x: 8.95, y: 0.3, w: 0.55, h: 0.55, fill: { color: C.accent2 }, line: { color: C.accent2 }, objectName: "decision badge " + label });
  s.addText(label, { x: 8.95, y: 0.3, w: 0.55, h: 0.55, fontSize: 13, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true });
}
function para(s, runs, o) { s.addText(runs, Object.assign({ isTextBox: true, fontSize: 12, color: C.text1, valign: "top", margin: 0, paraSpaceAfter: 6 }, o)); }
function head(t) { return { text: t, options: { bold: true, color: C.text2, fontSize: 13, breakLine: true } }; }
function line(t, extra = {}) { return { text: t, options: Object.assign({ breakLine: true }, extra) }; }
function bullets(items, size = 12) { return items.map((t, i) => ({ text: t, options: { bullet: { indent: 12 }, fontSize: size, breakLine: i < items.length - 1, paraSpaceAfter: 5 } })); }
function caption(s, t, x, y, w) { s.addText(t, { x, y, w, h: 0.25, fontSize: 9, color: C.accent3, italic: true, margin: 0, isTextBox: true }); }
function card(s, x, y, w, h, big, small, opts = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: opts.fill || C.background2 }, line: { color: opts.fill || C.background2 }, objectName: "stat card" });
  s.addText([{ text: big, options: { fontFace: "Cambria", fontSize: opts.bigSize || 26, bold: true, color: opts.bigColor || C.accent1, breakLine: true } },
             { text: small, options: { fontSize: opts.smallSize || 11, color: opts.smallColor || C.text1 } }],
            { x: x + 0.15, y: y + 0.12, w: w - 0.3, h: h - 0.24, valign: "top", margin: 0, isTextBox: true });
}
const NOTES = [];

// ---------- 1. Recommendation ----------
pres.addSection({ title: "Pitch" });
let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Pitch" });
s.addText("Recommendation to Data-Driven Developments' investment committee", { x: 0.6, y: 0.45, w: 8.8, h: 0.35, fontSize: 13, color: C.background2, margin: 0, isTextBox: true });
s.addText("Buy 12 Downtown Vancouver condos and run them seasonally", { x: 0.6, y: 0.85, w: 8.8, h: 1.1, fontFace: "Cambria", fontSize: 32, bold: true, color: C.background1, margin: 0, valign: "top", isTextBox: true });
const cards1 = [["12", "1-2 bedroom condos, Downtown, about 60% one-bedroom"],
  [m$(K.B_capital), `deployed, plus ${m$(10e6 - K.B_capital)} held in reserve`],
  [r10k(K.B_noi_p50), `expected 2027 net operating income (P10-P90: ${r10k(K.B_noi_p10)}-${r10k(K.B_noi_p90)})`],
  [pct(K.B_p50), `2027 net yield on capital deployed (P10-P90: ${pct(K.B_p10)}-${pct(K.B_p90)})`]];
cards1.forEach(([b, t], i) => card(s, 0.6 + i * 2.25, 2.15, 2.05, 1.55, b, t, { fill: "1B3F66", bigColor: C.background1, smallColor: C.background2, bigSize: 30 }));
s.addText([{ text: "How: ", options: { bold: true } },
  { text: "nightly guests May-Oct; furnished stays of 30+ nights Jan-Apr and Nov-Dec. That keeps every unit out of the City's 3% Empty Homes Tax and the 1% provincial Speculation and Vacancy Tax." }],
  { x: 0.6, y: 3.95, w: 8.8, h: 0.75, fontSize: 14, color: C.background1, margin: 0, valign: "top", isTextBox: true });
NOTES.push(`Our recommendation: DDD should buy twelve one- and two-bedroom condos in Downtown Vancouver, about ${m$(K.B_capital)} all-in, and keep roughly ${m$(10e6 - K.B_capital)} in reserve. We expect about ${r10k(K.B_noi_p50)} of net operating income in 2027, a ${pct(K.B_p50)} yield on the capital deployed, with a P10 to P90 range of ${pct(K.B_p10)} to ${pct(K.B_p90)}. The key is how they are run: nightly guests from May to October, and furnished stays of 30 nights or more for the other six months. That operating model is what turns this from a money-losing plan into a positive one, and the next slides show why.`);

// ---------- 2. Problem, metric, data ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Pitch" });
title(s, "The decision, our return metric, and the 1,809 listings we trust");
const wfLabels = ["All listings", "Entire homes only", "Nightly (under 30-night min.)", "Reviewed in last 12 mo", "Operating a full year", "Shows a City licence", "Usable nightly price", "Price $60-$1,500"];
const wfVals = D.waterfall.slice(0, wfLabels.length).map((r) => r[1]);  // last step (inside a local-area polygon) removes 0 rows
s.addChart(pres.charts.BAR, [
  { name: "Steps", labels: wfLabels, values: wfVals.map((v, i) => (i < wfVals.length - 1 ? v : 0)) },
  { name: "Comparable set", labels: wfLabels, values: wfVals.map((v, i) => (i === wfVals.length - 1 ? v : 0)) }],
  Object.assign({}, AX, { x: 0.5, y: 1.15, w: 4.6, h: 3.75, barDir: "bar", barGrouping: "stacked", chartColors: [HEX.grey, HEX.blue],
    catAxisOrientation: "maxMin", valAxisHidden: true, valGridLine: { style: "none" }, showValue: true, dataLabelPosition: "inEnd",
    dataLabelColor: "FFFFFF", dataLabelFormatCode: "#,##0;;;", showLegend: false, barGapWidthPct: 40,
    showTitle: true, title: "Cleaning: 6,509 listings to 1,809 comparables", titleFontSize: 11, titleColor: "0E2A47" }));
para(s, [head("Return metric"),
  line("2027 net yield = net operating income / all-in capital (price, transfer tax, closing, furnishing). Unlevered, because the mandate is $10M of equity judged on 2027 alone. Appreciation is excluded: Vancouver apartment and detached benchmark prices fell 5.6-9.6% over the year to June 2026 (GVR).", { fontSize: 12, paraSpaceAfter: 10 }),
  head("Data we joined to the Inside Airbnb snapshot")], { x: 5.4, y: 1.15, w: 4.1, h: 2.1 });
s.addText(bullets(["City of Vancouver 2026 assessments, joined to parcels and the 22 local areas: purchase prices",
  "GVR MLS HPI, June 2026: rolls July 2025 assessments forward; independent price check",
  "CMHC Rental Market Survey 2023-25: vacancy test and long-term rents",
  "Inside Airbnb March 2026 snapshot: same-listing seasonal prices"], 11.5), { x: 5.4, y: 3.05, w: 4.1, h: 1.95, margin: 0, valign: "top", color: C.text1, isTextBox: true });
NOTES.push(`DDD has ten million dollars of equity, properties live on January 1, 2027, and it will be judged on 2027. So our return metric is the 2027 net operating yield on all-in capital: income after every operating cost and tax, divided by price plus transfer tax, closing and furnishing. We leave out appreciation because Vancouver prices are falling. From 6,509 listings we kept 1,809 comparables a compliant, professionally run unit would compete with: entire homes, true nightly rentals, active, operating a full year, licensed, with a usable price. Purchase prices come from the City's 2026 assessment roll, joined to parcels and local areas, and rolled forward with the GVR price index.`);

// ---------- 3. D1 operating model ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Pitch" });
title(s, "Nightly rental all year loses money once vacancy taxes apply; a seasonal hybrid earns over 4%");
badge(s, "D1");
const om = D.opmodel;
s.addChart(pres.charts.BAR, [
  { name: "1-2BR condo", labels: ["Nightly all year", "Seasonal hybrid"], values: om.condo.slice(0, 2).map((v) => +(v * 100).toFixed(1)) },
  { name: "3BR+ detached house", labels: ["Nightly all year", "Seasonal hybrid"], values: om.house.map((v) => +(v * 100).toFixed(1)) }],
  Object.assign({}, AX, { x: 0.5, y: 1.15, w: 4.55, h: 3.2, barDir: "col", chartColors: [HEX.blue, HEX.grey], showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: '0.0"%";-0.0"%";;', dataLabelColor: "0B1B2B", valAxisLabelFormatCode: '0"%"', valAxisMinVal: -4, valAxisMaxVal: 5, valAxisMajorUnit: 1,
    showLegend: true, legendPos: "b", showTitle: true, title: "Median 2027 net yield by operating model", titleFontSize: 11, titleColor: "0E2A47", barGapWidthPct: 60 }));
s.addChart(pres.charts.BAR, [
  { name: "Nightly (May-Oct)", labels: "JFMAMJJASOND".split(""), values: D.season.map((v, i) => (i >= 4 && i <= 9 ? +(v * 100).toFixed(1) : 0)) },
  { name: "Furnished 30+ nights", labels: "JFMAMJJASOND".split(""), values: D.season.map((v, i) => (i >= 4 && i <= 9 ? 0 : +(v * 100).toFixed(1))) }],
  Object.assign({}, AX, { x: 5.25, y: 1.15, w: 4.25, h: 3.2, barDir: "col", barGrouping: "stacked", chartColors: [HEX.blue, HEX.grey], valAxisLabelFormatCode: '0"%"',
    showLegend: true, legendPos: "b", showTitle: true, title: "Share of a year's nightly revenue by month", titleFontSize: 11, titleColor: "0E2A47", barGapWidthPct: 35 }));
para(s, [{ text: `An investor-owned nightly rental counts as vacant: 3% Empty Homes Tax + 1% SVT, about ${k$(K.condo_vacancy_taxes_median)} a year on a median condo. Long-term rental of the same Downtown unit: ${pct(K.ltr_benchmark_yield)}.` }], { x: 0.5, y: 4.45, w: 4.55, h: 0.7, fontSize: 11.5 });
para(s, [{ text: `Nov-Apr earns only ${pct(1 - K.may_oct_revenue_share, 0)} of nightly revenue, so it is the cheap half of the year to hand to 30+ night stays, which exempts the unit from both taxes.` }], { x: 5.25, y: 4.45, w: 4.25, h: 0.7, fontSize: 11.5 });
NOTES.push(`Decision one, the operating model. The simulation lets DDD skip the principal-residence rule, but not the taxes. A unit that is not lived in or rented for six months in stays of 30 days or more is "vacant" for the City's 3% Empty Homes Tax and the province's 1% Speculation and Vacancy Tax, about ${k$(K.condo_vacancy_taxes_median)} a year on a median condo. Run nightly all year, the median condo yields ${pct(K.condo_yield_str)}. The fix comes from seasonality: November to April is only ${pct(1 - K.may_oct_revenue_share, 0)} of nightly revenue. Rent those months as furnished 30-plus-night stays and the unit is exempt. The hybrid yields ${pct(K.condo_yield_hybrid)} on condos, more than double a plain long-term rental at ${pct(K.ltr_benchmark_yield)}.`);

// ---------- 4. D2 revenue base ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Pitch" });
title(s, "We rebuilt revenue from clean prices: June 2026 quotes overstate a normal year by about 12%");
badge(s, "D2");
const bl = ["Inside Airbnb method (June quote x nights)", "Remove World Cup match-night premium", "Seasonal average rate (nightly all year)", "Seasonal hybrid (our plan)"];
s.addChart(pres.charts.BAR, [
  { name: "Steps", labels: bl, values: D.bridge.map((v, i) => (i < 3 ? Math.round(v) : 0)) },
  { name: "Plan", labels: bl, values: D.bridge.map((v, i) => (i === 3 ? Math.round(v) : 0)) }],
  Object.assign({}, AX, { x: 0.5, y: 1.15, w: 4.9, h: 3.3, barDir: "bar", barGrouping: "stacked", chartColors: [HEX.grey, HEX.blue], catAxisOrientation: "maxMin",
    valAxisHidden: true, valGridLine: { style: "none" }, showValue: true, dataLabelPosition: "inEnd", dataLabelColor: "FFFFFF", dataLabelFontSize: 12,
    dataLabelFormatCode: '$#,##0.0,"k";;;', showLegend: false, barGapWidthPct: 45, catAxisLabelFontSize: 10.5,
    showTitle: true, title: "Median 1-2BR condo comparable, annual gross revenue", titleFontSize: 11, titleColor: "0E2A47" }));
const steps4 = [[`${K.pct_prices_from_90night_quotes.toFixed(0)}% of prices are 90-night quotes`, "giving nightly 'prices' as low as $6. We keep only quotes of 7 nights or fewer."],
  ["June quotes fall in the FIFA World Cup window", `Match-night stays cost ${pct(K.match_night_premium)} more than the same listings' other nights (95% CI ${K.match_premium_ci.split("-").map((x) => pct(+x)).join("-")}). Removed.`],
  ["June is peak season", `The same listing costs ${pct(K.mar_over_jun_price, 0)} of its June price in late March. Seasonal average rate = ${K.annual_adr_factor.toFixed(2)} x June.`]];
steps4.forEach(([h, t], i) => {
  const y = 1.2 + i * 1.12;
  s.addShape(pres.shapes.OVAL, { x: 5.65, y, w: 0.42, h: 0.42, fill: { color: C.text2 }, line: { color: C.text2 }, objectName: "step marker" });
  s.addText(String(i + 1), { x: 5.65, y, w: 0.42, h: 0.42, fontSize: 13, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true });
  para(s, [{ text: h, options: { bold: true, breakLine: true, color: C.text2 } }, { text: t }], { x: 6.2, y: y - 0.02, w: 3.3, h: 1.0, fontSize: 11.5 });
});
caption(s, `Result: ${k$(K.rev_bridge_ia)} to ${k$(K.rev_bridge_str)} for nightly-only (-12%); ${k$(K.rev_bridge_hybrid)} as a hybrid with furnished winter stays.`, 0.5, 4.6, 9.0);
NOTES.push(`Decision two: we did not trust Inside Airbnb's revenue estimate, which multiplies one price quote by estimated nights. Three problems. ${K.pct_prices_from_90night_quotes.toFixed(0)} percent of prices are quotes for 90-night stays, which give nightly prices as low as six dollars, so we dropped those. The June scrape priced stays during the World Cup: by comparing each listing's price on a match night with its March price, match nights carried a ${pct(K.match_night_premium)} premium, which won't recur in 2027. And June is peak season: the same listing charges ${pct(K.mar_over_jun_price, 0)} of that in late March. Correcting for all three cuts the median condo's revenue from ${k$(K.rev_bridge_ia)} to ${k$(K.rev_bridge_str)}, about 12 percent, and every yield we show uses the corrected figure.`);

// ---------- 5. Where ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Pitch" });
title(s, "Where and what: Downtown 1-2 bedroom condos lead on yield, and the lead is not a World Cup effect");
const A = D.areas;
const albl = A.map((a) => `${a[1]} ${a[0].startsWith("condo") ? "condo" : "house"} (n=${a[2]})  ${pct(a[4])}`);
const isRec = (a) => a[1] === "Downtown" && a[0].startsWith("condo");
s.addChart(pres.charts.BAR, [
  { name: "base", labels: albl, values: A.map((a) => +(a[5] * 100).toFixed(2)) },
  { name: "Other areas (90% CI)", labels: albl, values: A.map((a) => (isRec(a) ? 0 : +((a[6] - a[5]) * 100).toFixed(2))) },
  { name: "Recommended (90% CI)", labels: albl, values: A.map((a) => (isRec(a) ? +((a[6] - a[5]) * 100).toFixed(2) : 0)) }],
  Object.assign({}, AX, { x: 0.5, y: 1.15, w: 5.4, h: 3.55, barDir: "bar", barGrouping: "stacked", chartColors: ["FFFFFF", HEX.lgrey, HEX.blue], catAxisOrientation: "maxMin",
    valAxisMinVal: 0, valAxisMaxVal: 5, valAxisMajorUnit: 1, valAxisLabelFormatCode: '0"%"', showLegend: false, barGapWidthPct: 45, catAxisLabelFontSize: 10,
    showTitle: true, title: "Median 2027 net yield, seasonal hybrid (bar = 90% bootstrap CI)", titleFontSize: 11, titleColor: "0E2A47" }));
para(s, [head("Downtown condos"),
  line(`${K.downtown_n} comparables; median $${Math.round(K.downtown_adr)} a night (seasonal average) x ${K.downtown_nights} nights. Purchase about ${k$(K.downtown_price)} from 2026 assessments, GVR-adjusted.`, { paraSpaceAfter: 8 }),
  head("Houses lose on yield"),
  line(`3BR+ houses yield ${pct(K.house_yield_hybrid)} vs ${pct(K.condo_yield_hybrid)} for condos: land adds cost, not nightly revenue.`, { paraSpaceAfter: 8 }),
  head("Tested: World Cup effect"),
  line("BC Place is Downtown. Downtown's June/March price ratio (1.33) is no higher than elsewhere (1.35-1.39), and it stays in the top two on March prices.")],
  { x: 6.15, y: 1.15, w: 3.35, h: 3.9, fontSize: 11.5 });
NOTES.push(`Where. For each local area with at least 20 comparables, we computed every comparable's 2027 hybrid yield against that area's purchase price, and bootstrapped a confidence interval on the median. Downtown condos lead at ${pct(K.downtown_yield_hybrid)}, with ${K.downtown_n} comparables and the tightest interval. Houses trail: a detached lot costs two to three times a condo but doesn't earn two to three times the nightly revenue. We worried Downtown was flattered by World Cup matches at BC Place, so we tested it. Downtown's June-to-March price jump is no bigger than other areas', and it stays top two using March prices only. That concern did not hold.`);

// ---------- 6. D3 How many ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Pitch" });
title(s, "How many: 12 modest condos beat 5 high-value houses on both return and downside");
badge(s, "D3");
const P = D.portfolio;
const short = { A: "A. 5 detached houses", B: "B. 12 condos, Downtown", C: "C. 12 condos, 3 areas", D: "D. 1 house + 10 condos" };
const plbl = P.map((p) => `${short[p[0][0]]}   P50 ${pct(p[5])}`);
const rec = (p) => p[0].startsWith("B");
s.addChart(pres.charts.BAR, [
  { name: "base", labels: plbl, values: P.map((p) => +(p[4] * 100).toFixed(2)) },
  { name: "Other P10-P50", labels: plbl, values: P.map((p) => (rec(p) ? 0 : +((p[5] - p[4]) * 100).toFixed(2))) },
  { name: "Other P50-P90", labels: plbl, values: P.map((p) => (rec(p) ? 0 : +((p[6] - p[5]) * 100).toFixed(2))) },
  { name: "Recommended P10-P50", labels: plbl, values: P.map((p) => (rec(p) ? +((p[5] - p[4]) * 100).toFixed(2) : 0)) },
  { name: "Recommended P50-P90", labels: plbl, values: P.map((p) => (rec(p) ? +((p[6] - p[5]) * 100).toFixed(2) : 0)) }],
  Object.assign({}, AX, { x: 0.5, y: 1.15, w: 5.4, h: 3.2, barDir: "bar", barGrouping: "stacked", chartColors: ["FFFFFF", HEX.grey, HEX.lgrey, HEX.blue, HEX.lblue],
    catAxisOrientation: "maxMin", valAxisMinVal: 0, valAxisMaxVal: 6, valAxisMajorUnit: 1, valAxisLabelFormatCode: '0"%"', showLegend: false, barGapWidthPct: 50, catAxisLabelFontSize: 10.5,
    showTitle: true, title: "2027 net yield on capital deployed: P10 to P50 (dark) to P90 (light)", titleFontSize: 11, titleColor: "0E2A47" }));
caption(s, "10,000 simulations. Each unit draws a real comparable; shared shocks to nightly rate, occupancy, furnished rent, launch ramp-up and price paid.", 0.5, 4.45, 5.4);
para(s, [head("Few high-value lose"),
  line(`5 houses: P50 ${pct(K.A_p50)}, and a ${pct(K.A_prob_below_2, 0)} chance of earning under 2%.`, { paraSpaceAfter: 8 }),
  head("Many modest win"),
  line(`12 Downtown condos: P50 ${pct(K.B_p50)}, and even the P10 (${pct(K.B_p10)}) beats the houses' median.`, { paraSpaceAfter: 8 }),
  head("Tested: spread across 3 areas?"),
  line(`It cut the median by ${((K.B_p50 - K.C_p50) * 100).toFixed(1)} pts and barely narrowed the range (${(K.C_spread * 100).toFixed(1)} vs ${(K.B_spread * 100).toFixed(1)} pts): the risk is market-wide. So we diversify by building, not neighbourhood.`)],
  { x: 6.15, y: 1.15, w: 3.35, h: 3.9, fontSize: 11.5 });
NOTES.push(`Decision three, the central trade-off. We simulated four portfolios 10,000 times. Each unit draws a real comparable's performance, and all units share market shocks to rate, occupancy and furnished rents. Five houses give a median of ${pct(K.A_p50)} with a ${pct(K.A_prob_below_2, 0)} chance of falling under two percent. Twelve Downtown condos give ${pct(K.B_p50)}, and their bad case beats the houses' typical case. We expected spreading the condos across three neighbourhoods to reduce risk. It didn't: the range barely changed and the median fell, because 2027 risk is market-wide. So we concentrate in Downtown but spread across buildings, which protects against the risk that does vary by building: strata bylaws.`);

// ---------- 7. Expected performance + risks ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Pitch" });
title(s, `Expected 2027: about ${r10k(K.B_noi_p50)} of income; the six-month furnished-stay test is the risk that matters`);
const T = D.tornado.slice().sort((a, b) => Math.abs(b[2] - b[1]) - Math.abs(a[2] - a[1]));
const base = T[0][3];
const SHORT = { "Nightly rate (ADR) -10% / +10%": "Nightly rate -/+10%", "Occupancy -10% / +10%": "Occupancy -/+10%",
  "Furnished monthly rent: 70% / 100% of lower-quartile ask": "Furnished rent 70/100% of ask", "Purchase price +5% / -5%": "Price paid +/-5%",
  "Management 25% / 15%": "Management fee 25/15%", "Strata fee $650 / $400 per month": "Strata fee $650/$400" };
const tl = T.map((t) => (t[0].startsWith("6-month") ? `Fail 6-month test: ${pct(t[1])}` : `${SHORT[t[0]] || t[0]}: ${pct(t[1])} / ${pct(t[2])}`));
const fail = (t) => t[0].startsWith("6-month");
s.addChart(pres.charts.BAR, [
  { name: "Downside", labels: tl, values: T.map((t) => (fail(t) ? 0 : +((t[1] - base) * 100).toFixed(2))) },
  { name: "Fails tax test", labels: tl, values: T.map((t) => (fail(t) ? +((t[1] - base) * 100).toFixed(2) : 0)) },
  { name: "Upside", labels: tl, values: T.map((t) => +((t[2] - base) * 100).toFixed(2)) }],
  Object.assign({}, AX, { x: 0.5, y: 1.15, w: 5.1, h: 3.45, barDir: "bar", barGrouping: "stacked", chartColors: [HEX.blue, HEX.red, HEX.lgrey], catAxisOrientation: "maxMin",
    valAxisMinVal: -5.5, valAxisMaxVal: 1, valAxisMajorUnit: 1, valAxisLabelFormatCode: '+0;-0;0', showLegend: false, barGapWidthPct: 45, catAxisLabelFontSize: 9.5,
    showTitle: true, title: `Change in portfolio yield vs ${pct(base)} base (percentage points)`, titleFontSize: 11, titleColor: "0E2A47" }));
card(s, 5.85, 1.15, 3.65, 1.05, `${pct(K.B_p50)}  (${pct(K.B_p10)}-${pct(K.B_p90)})`, `on ${m$(K.B_capital)} deployed; ${pct(K.B_yield_on_10m)} on the full $10M. NOI ${r10k(K.B_noi_p50)} (${r10k(K.B_noi_p10)}-${r10k(K.B_noi_p90)}).`, { bigSize: 20 });
para(s, [head("Risks and mitigation"),
  { text: "Fail the 6-month test: ", options: { bold: true } }, line(`yield falls to ${pct(K.fail6_yield)}. Get a legal opinion before closing; pre-sign Jan-Apr furnished stays; the ${m$(10e6 - K.B_capital)} reserve covers about 3 years of the tax.`),
  { text: "Strata bylaws ban short stays: ", options: { bold: true } }, line("buy only where bylaws allow; spread over 6+ buildings."),
  { text: "Weaker rates or rents: ", options: { bold: true } }, line("each -10% costs under 0.5 pts; furnished stays set a winter floor."),
  { text: "Opt-out supply surge: ", options: { bold: true } }, { text: `low for 2027. City vacancy ${K.city_vacancy_2025.toFixed(1)}% (2025) is under the 3% test.` }],
  { x: 5.85, y: 2.35, w: 3.65, h: 2.8, fontSize: 10.5, paraSpaceAfter: 4 });
NOTES.push(`Expected 2027 performance: about ${r10k(K.B_noi_p50)} of net operating income, ${pct(K.B_p50)} on the capital deployed, with a P10 to P90 range of ${pct(K.B_p10)} to ${pct(K.B_p90)}; ${pct(K.B_yield_on_10m)} if you count the reserve. The tornado shows what moves it. Rates, occupancy, management fees and strata fees each move the yield by under half a point. One risk dwarfs the rest: if the units fail the six-month furnished-stay test, the taxes return and the yield drops to ${pct(K.fail6_yield)}. So we get a legal opinion before buying, pre-sign the winter stays, and keep the reserve, which covers about three years of that tax. On the opt-out: the City's vacancy rate was ${K.city_vacancy_2025.toFixed(1)}% in 2025, below the 3% test, so no opt-out surge of competing listings can arrive in 2027.`);

// ---------- 8. Next steps ----------
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Pitch" });
title(s, "Next steps, and how DDD will know the plan is working");
const steps = [["Nov 2026", "Legal opinion: do 30+ night furnished stays satisfy the Empty Homes Tax, SVT and tenancy rules? Go/no-go gate."],
  ["Nov-Dec 2026", "Shortlist 6+ Downtown buildings whose bylaws allow short stays; buy 12 units, about 60% 1BR / 40% 2BR."],
  ["Dec 2026", "City business licences and provincial registration; pre-sign furnished stays for Jan-Apr 2027."],
  ["May / Nov 2027", "Switch to nightly guests on May 1; back to furnished 30+ night stays on Nov 1."]];
steps.forEach(([when, what], i) => {
  const x = 0.5 + i * 2.3;
  s.addShape(pres.shapes.OVAL, { x, y: 1.25, w: 0.45, h: 0.45, fill: { color: C.accent1 }, line: { color: C.accent1 }, objectName: "timeline step" });
  s.addText(String(i + 1), { x, y: 1.25, w: 0.45, h: 0.45, fontSize: 14, bold: true, color: C.background1, align: "center", valign: "middle", margin: 0, isTextBox: true });
  if (i < 3) s.addShape(pres.shapes.LINE, { x: x + 0.55, y: 1.475, w: 1.65, h: 0, line: { color: C.accent3, width: 1 }, objectName: "timeline connector" });
  para(s, [{ text: when, options: { bold: true, color: C.text2, breakLine: true, fontSize: 12.5 } }, { text: what }], { x, y: 1.85, w: 2.1, h: 1.5, fontSize: 11 });
});
const strPlan = K.downtown_nights;
const kpis = [["6+ months", "of furnished 30+ night stays per unit by Dec 31: tracked monthly"],
  [`${r10k(K.B_noi_p50)}`, `portfolio NOI plan; review quarterly against the ${r10k(K.B_noi_p10)} P10`],
  ["Sep 30 trigger", "if any unit is short of 2 furnished months for Nov-Dec, pre-book them before reopening to nightly guests"]];
kpis.forEach(([b, t], i) => card(s, 0.5 + i * 3.05, 3.6, 2.85, 1.2, b, t, { bigSize: 20, smallSize: 11 }));
NOTES.push(`Next steps. First, a legal opinion on whether furnished stays of 30 nights or more satisfy the Empty Homes Tax, the SVT and tenancy law; that is a go or no-go gate. Second, shortlist at least six Downtown buildings whose bylaws allow short stays, and buy twelve units, about 60% one-bedroom, mirroring the comparables. Third, licences, provincial registration, and pre-signed winter stays before January. DDD will know it is working by three measures: six furnished months per unit by year-end, net income tracking the ${r10k(K.B_noi_p50)} plan, and a September 30 checkpoint so the November-December stays are booked in time. Thank you, we're happy to take questions.`);

// ---------- Appendix ----------
pres.addSection({ title: "Appendix" });
function apx(t) { const x = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Appendix" }); title(x, t); return x; }
const TH = (t) => ({ text: t, options: { bold: true, color: "FFFFFF", fill: { color: "0E2A47" }, fontSize: 10.5 } });
const tdo = { fontSize: 10.5, color: "0B1B2B", valign: "top" };
function dlog(rows, ttl) {
  const x = apx(ttl);
  x.addTable([[TH("#"), TH("What we decided"), TH("Why: evidence and alternatives compared"), TH("What it changed")]].concat(
    rows.map((r) => r.map((c, j) => ({ text: c, options: Object.assign({}, tdo, j === 0 ? { bold: true, color: "EB6834", fontSize: 12 } : {}) })))),
    { x: 0.5, y: 1.15, w: 9.0, colW: [0.45, 2.15, 3.75, 2.65], border: { type: "solid", pt: 0.5, color: "D9D8D3" }, fill: { color: "FFFFFF" }, margin: 0.06, autoPage: false });
  return x;
}
dlog([["D1", "Operating model: nightly May-Oct, furnished 30+ night stays Jan-Apr and Nov-Dec, instead of nightly all year.",
  `An investor-owned nightly STR is 'vacant' under Vancouver's Vacancy Tax By-law (3%) and BC SVT (1%, Canadian owners): about ${k$(K.condo_vacancy_taxes_median)} a year per median condo. Compared 3 models on the same 706 condo comparables: nightly all year ${pct(K.condo_yield_str)}, hybrid ${pct(K.condo_yield_hybrid)}, long-term rental ${pct(K.ltr_benchmark_yield)} (Downtown, CMHC rent). Nov-Apr is ${pct(1 - K.may_oct_revenue_share, 0)} of nightly revenue (reviews 2024-25 x same-listing price index).`,
  "Turned a loss-making plan into a positive one; set the operating calendar; made passing the 6-month test the top risk and the first next step (legal opinion)."],
 ["D2", "Revenue base: rebuild 2027 revenue from cleaned prices instead of Inside Airbnb's estimated revenue.",
  `${K.pct_prices_from_90night_quotes}% of prices are 90-night quotes (nightly values down to $6). June quotes fall in the World Cup window: match-night stays +${pct(K.match_night_premium)} vs the same listings' other nights (95% CI ${K.match_premium_ci.split("-").map((x) => pct(+x)).join("-")}, March price as control). Late-March price = ${pct(K.mar_over_jun_price, 0)} of June, so seasonal average = ${K.annual_adr_factor.toFixed(2)} x June (demand-weighted). Dec 2025 snapshot has no prices, so it could not be used.`,
  `Median condo revenue ${k$(K.rev_bridge_ia)} to ${k$(K.rev_bridge_str)} (-12%); all yields about 1 pt lower than the naive method. Prevents presenting a one-off event year as the 2027 base.`]],
 "Decision log (1/2)");
dlog([["D3", "How many: 12 modest Downtown condos, not 5 detached houses; diversify across buildings, not neighbourhoods.",
  `Monte Carlo, 10,000 runs, 4 portfolios. Houses: P50 ${pct(K.A_p50)}, P(yield <2%) ${pct(K.A_prob_below_2, 0)}. 12 Downtown condos: P50 ${pct(K.B_p50)}, P10 ${pct(K.B_p10)}. 3-area condo mix: P50 ${pct(K.C_p50)}, P10-P90 width ${(K.C_spread * 100).toFixed(1)} vs ${(K.B_spread * 100).toFixed(1)} pts: tested and did not reduce risk (shocks are market-wide).`,
  "Dropped houses and the multi-area plan; added a building-level rule (6+ buildings) aimed at the risk that does vary by unit: strata bylaws."],
 ["D4", "Scope: stay in the City of Vancouver (fund preference) rather than suburbs or Kelowna.",
  `The snapshot covers the City only. City rental vacancy (CMHC, zones 1-10, unit-weighted): ${K.city_vacancy_2024.toFixed(1)}% in 2024, ${K.city_vacancy_2025.toFixed(1)}% in 2025, under the 3%-for-two-years test, so no opt-out can take effect before June 2028. CMHC zones covering Burnaby, New Westminster, Surrey and Richmond were already at or above 3% in 2025; if 2026 also clears 3%, they could opt out from June 1, 2027, letting competing listings back mid-year.`,
  "Kept the recommendation in Vancouver and rated opt-out supply risk low for 2027; flagged it for 2028 if 2026-27 vacancy stays at or above 3%."]],
 "Decision log (2/2)");

// assumptions
s = apx("Key assumptions (all in data/manual/assumptions.yaml)");
const AS = [["Purchase price", `2026 assessed median by local area x GVR 1-year change (Downtown condo ${k$(K.downtown_price)})`],
  ["Transfer tax / closing / furnishing", "BC PTT brackets (1/2/3/+2%); 0.6% closing; $25k per condo"],
  ["Platform fee", "15.5% Airbnb host-only fee"], ["Management / maintenance", "20% of nightly revenue; 10% of furnished-stay rent; 5% maintenance"],
  ["Fixed costs per condo", "Strata $500/mo, utilities $300/mo, insurance $1,800/yr, property tax 0.336% of value"],
  ["Licences", "City STR licence $1,060 (2025 median fee paid); provincial registration $450"],
  ["Vacancy taxes (if 6-month test fails)", "Empty Homes Tax 3% + SVT 1% of assessed value"],
  ["Furnished 30+ night rent", `Lower-quartile Airbnb monthly ask: $${Math.round(D.mtr[0][1]).toLocaleString()} (1BR), $${Math.round(D.mtr[1][1]).toLocaleString()} (2BR); simulated at 70-100%`],
  ["Occupancy", "Inside Airbnb review-based estimate, trailing 12 months (capped at 255 nights)"],
  ["Long-term rental benchmark", "CMHC Oct 2025 Downtown average rent $2,198/mo; 8% management, 5% maintenance, no furnishing"],
  ["Simulation shocks", "Nightly rate sd 7%, occupancy sd 8%, launch ramp-up 85-100%, price paid sd 3%"],
  ["Reserve", `${m$(10e6 - K.B_capital)} left after 12 units (a 13th does not fit); covers about 3 years of vacancy tax`]];
s.addTable([[TH("Assumption"), TH("Value and source")]].concat(AS.map((r) => [{ text: r[0], options: Object.assign({}, tdo, { bold: true, fontSize: 10 }) }, { text: r[1], options: Object.assign({}, tdo, { fontSize: 10 }) }])),
  { x: 0.5, y: 1.15, w: 9.0, colW: [2.7, 6.3], border: { type: "solid", pt: 0.5, color: "D9D8D3" }, margin: 0.05, rowH: 0.3, autoPage: false });

// validation & limitations
s = apx("Validation, what didn't hold, and limitations");
const vc = D.value_check;
para(s, [head("Validation"),
  line(`Purchase-price proxy vs GVR benchmarks: within ${(Math.min(...vc.map((v) => v[4])) * 100).toFixed(1)}% to +${(Math.max(...vc.map((v) => v[4])) * 100).toFixed(1)}% across apartment/detached x West/East.`),
  line(`Area ranking is stable: split-half Spearman ${K.split_half_spearman.toFixed(2)} (300 random splits).`),
  line("World Cup check: Downtown's lead holds on March prices (rank 1 on June, 2 on March)."),
  line(`Assessment join: 100% of folios matched a parcel; 100% of listings fell in a local area.`, { paraSpaceAfter: 10 }),
  head("Tested and did not hold"),
  line(`Review-based occupancy vs the forward calendar: Spearman ${K.occ_calendar_spearman.toFixed(2)}. 'Unavailable' mixes bookings and owner blocks, so the calendar can't validate occupancy; we treat it as an upper bound only.`),
  line("Diversifying across neighbourhoods did not reduce simulated risk (slide 6).")],
  { x: 0.5, y: 1.15, w: 4.4, h: 3.95, fontSize: 10.5, paraSpaceAfter: 4 });
para(s, [head("Limitations"),
  line("Occupancy and revenue are estimates; reviews are a proxy for stays, and 17% of comparables sit at the 255-night cap (understates the best units)."),
  line("No bedroom-level purchase prices: the area's median strata value is matched to 1-2BR revenue."),
  line("Furnished monthly rents are asking prices; strata fees and which buildings allow short stays are not in any dataset used."),
  line("Whether 30+ night furnished stays count as tenancies for the Empty Homes Tax, SVT and tenancy law needs a legal opinion."),
  line("One scrape (15 Jun - 6 Jul 2026); listing coordinates are jittered by Inside Airbnb. Compliance shares are estimates.")],
  { x: 5.15, y: 1.15, w: 4.35, h: 3.95, fontSize: 10.5, paraSpaceAfter: 4 });

// data quality
s = apx("Data-quality checks on the 15 June 2026 snapshot");
const DQ = [["Rows / unique ids", `${K.raw_listings} / ${K.raw_listings} (no duplicates); 90 columns, not the ~75 in the brief`],
  ["Scrape dates", "Jun 15 (1,295), Jun 16 (3,058), Jul 6 (2,156): one snapshot, three crawl days"],
  ["Price", `Text, parsed; 10.2% missing; ${K.pct_prices_from_90night_quotes}% from 90-night quotes; 337 under $30, 21 over $3,000`],
  ["Minimum nights", `${K.pct_entire_homes_min30}% of entire homes require 30+ nights (monthly rentals, not STRs)`],
  ["Occupancy estimate", `Capped at 255 nights; ${K.listings_at_occupancy_cap} listings at the cap`],
  ["Neighbourhoods", "23 Inside Airbnb labels vs 22 City local areas: re-assigned by point-in-polygon to official boundaries"],
  ["Licence field", `17.5% blank; ${pct(K.licence_share_active, 0)} of active nightly listings show a City licence (estimate: listings and licences are not counted on the same basis)`],
  ["Earlier snapshots", "Dec 2025: price column empty (unusable). Mar 2026: usable quotes for 1,965 matched listings"],
  ["Not used", "Sep 2026 snapshot (after the case date); the 18-column summary listings file; no host names, URLs or licence numbers kept"]];
s.addTable([[TH("Check"), TH("Finding and handling")]].concat(DQ.map((r) => [{ text: r[0], options: Object.assign({}, tdo, { bold: true, fontSize: 10 }) }, { text: r[1], options: Object.assign({}, tdo, { fontSize: 10 }) }])),
  { x: 0.5, y: 1.15, w: 9.0, colW: [2.1, 6.9], border: { type: "solid", pt: 0.5, color: "D9D8D3" }, margin: 0.05, autoPage: false });

// D4 evidence chart
s = apx("D4 evidence: Vancouver is below the 3% opt-out test; several suburbs are above it");
badge(s, "D4");
const V = D.vacancy;
s.addChart(pres.charts.BAR, [
  { name: "City of Vancouver", labels: V.map((v) => v[0]), values: V.map((v, i) => (i < 3 ? +v[1].toFixed(1) : 0)) },
  { name: "Other Metro Vancouver zones", labels: V.map((v) => v[0]), values: V.map((v, i) => (i >= 3 ? +v[1].toFixed(1) : 0)) }],
  Object.assign({}, AX, { x: 0.5, y: 1.15, w: 5.6, h: 3.6, barDir: "bar", barGrouping: "stacked", chartColors: [HEX.blue, HEX.grey], catAxisOrientation: "maxMin",
    valAxisMinVal: 0, valAxisMaxVal: 7, valAxisMajorUnit: 1, valAxisLabelFormatCode: '0"%"', showValue: true, dataLabelPosition: "inEnd", dataLabelColor: "FFFFFF",
    dataLabelFormatCode: '0.0"%";;;', showLegend: false, barGapWidthPct: 40,
    showTitle: true, title: "Purpose-built rental vacancy, October (CMHC Rental Market Survey)", titleFontSize: 11, titleColor: "0E2A47" }));
para(s, [head("The rule"), line("A municipality at 3%+ vacancy two years running may opt out of the principal-residence requirement. From 2027: request by Feb 28, effective June 1.", { paraSpaceAfter: 8 }),
  head("What it means for 2027"), line(`Vancouver needs 2025 and 2026 at 3%+; 2025 was ${K.city_vacancy_2025.toFixed(1)}%. Earliest effect: June 2028.`),
  line("Suburbs already above 3% could open to new competing listings on June 1, 2027 if their 2026 rate also clears 3%: five months into DDD's measured year.")],
  { x: 6.35, y: 1.15, w: 3.15, h: 3.9, fontSize: 11 });

// AI + reproducibility
s = apx("AI use and reproducibility");
para(s, [head("Material AI assistance (disclosure)"),
  line("We used Claude (Anthropic) to help write the analysis code, research tax and regulatory rules, and draft these slides."),
  line("How we checked it: every figure is regenerated by run_all.py and listed in outputs/key_numbers.csv with the script that produced it; tax and regulatory facts were checked against primary sources (City of Vancouver, BC Government, CMHC); the purchase-price proxy was checked against GVR's independent benchmark; each decision was re-derived and stress-tested by the team.", { paraSpaceAfter: 10 }),
  head("Reproduce any number"),
  line("python run_all.py --download  (downloads all public data, then runs 01-09)"),
  line("01 clean listings, 02 seasonality and World Cup premium, 03 purchase prices, 04 unit economics, 05 portfolio simulation, 06 validation and sensitivity, 07-09 figures and deck data.")],
  { x: 0.5, y: 1.15, w: 9.0, h: 3.9, fontSize: 12, paraSpaceAfter: 5 });

// notes
const slides = pres._slides;
NOTES.forEach((n, i) => slides[i].addNotes(n));

(async () => {
  const out = path.join(__dirname, "DDD_DataJam2026_Pitch.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("wrote", out);
})();
