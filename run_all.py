"""Reproduce every number and figure:  python run_all.py   (add --download on a fresh clone)

Runs the pipeline steps in order, shows one progress line per step, saves each step's full printout to
outputs/run_log.txt, then prints a readable summary of every pitch number (also saved to outputs/report.txt).
  --download   first fetch all public data (only needed on a fresh clone)
  --verbose    also show each step's full printout on screen, as it runs
"""
import subprocess, sys, os, time
here = os.path.dirname(os.path.abspath(__file__))
STEPS = [("00_download.py", "Download public data (Inside Airbnb, City of Vancouver, CMHC, StatCan)"),
         ("01_clean_listings.py", "Clean listings and build the comparable set"),
         ("02_seasonality.py", "Seasonality, World Cup premium and the annual nightly-rate factor"),
         ("03_property_values.py", "Purchase prices from 2026 assessments, checked against GVR"),
         ("04_economics.py", "2027 income, costs and yield for every comparable"),
         ("05_portfolio.py", "Monte Carlo: few high-value vs many modest portfolios"),
         ("06_validation.py", "Validation checks, opt-out test and sensitivity"),
         ("07_charts.py", "Figures (outputs/figures/)"),
         ("08_key_numbers.py", "Collect every pitch number into outputs/key_numbers.csv"),
         ("09_deck_data.py", "Export what the deck shows (outputs/deck_data.json)"),
         ("10_report.py", "Readable summary (outputs/report.txt)")]
if "--download" not in sys.argv: STEPS = STEPS[1:]
verbose = "--verbose" in sys.argv
env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONWARNINGS="ignore")
log_path = os.path.join(here, "outputs", "run_log.txt"); os.makedirs(os.path.dirname(log_path), exist_ok=True)
print(f"Running {len(STEPS)} steps (full printout of each step: outputs/run_log.txt)\n", flush=True)
with open(log_path, "w", encoding="utf-8") as log:
    for i, (script, what) in enumerate(STEPS, 1):
        t0 = time.time()
        if script == "10_report.py":          # the report is the screen output, so it is not captured
            print(flush=True)
            r = subprocess.run([sys.executable, script], cwd=os.path.join(here, "src"), env=env)
            if r.returncode: sys.exit(f"\nFAILED at {script}")
            continue
        print(f"  [{i:>2}/{len(STEPS)}] {what:<72}", end="", flush=True)
        r = subprocess.run([sys.executable, script], cwd=os.path.join(here, "src"), env=env,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        log.write(f"\n===== {script} =====\n{r.stdout}{r.stderr}")
        print(f"done ({time.time() - t0:4.1f}s)" if r.returncode == 0 else "FAILED", flush=True)
        if verbose: print(r.stdout, flush=True)
        if r.returncode:
            print(r.stdout[-3000:], r.stderr[-3000:], sep="\n"); sys.exit(f"\nFAILED at {script}; see outputs/run_log.txt")
