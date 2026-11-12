"""Step 1: download raw data for the Fair Mortgage Approval project.

Sources (all free):
  HMDA      - CFPB Data Browser API, filtered at download time to the SSOT scope
              (home purchase, first lien, owner-occupied, originated or denied).
              Pulled per state per year so files stay small and restartable.
  ACS 5-yr  - Census API, tract-level income / house value / poverty / unemployment.
  FRED      - 30-yr mortgage rate (MORTGAGE30US, weekly -> yearly mean).
              State house price index is a TODO (FHFA state HPI file).

Usage:
  python src/01_download.py hmda --years 2023 --states DE        # small test
  python src/01_download.py hmda --years 2018-2023 --states all  # full pull
  python src/01_download.py acs  --years 2018-2023
  python src/01_download.py fred
"""
import argparse
import sys
import time
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

STATES = ("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO "
          "MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY").split()

HMDA_URL = "https://ffiec.cfpb.gov/v2/data-browser-api/view/csv"
# SSOT scope from the pre-submission doc (only years + actions_taken go to the server; API max 2 filters):
#   loan_purposes=1   home purchase
#   lien_statuses=1   first lien
#   occupancy_types=1 principal residence (owner-occupied)
#   actions_taken=1,3 originated or denied  (= "final decision was made")
HMDA_FILTERS = {"loan_purposes": "1", "lien_statuses": "1",
                "occupancy_types": "1", "actions_taken": "1,3"}


def parse_years(s):
    if "-" in s:
        a, b = s.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in s.split(",")]


def download(url, params, dest, retries=3):
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  skip (exists) {dest.name}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, params=params, stream=True, timeout=300) as r:
                r.raise_for_status()
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            tmp.replace(dest)
            print(f"  ok {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
            return
        except requests.RequestException as e:
            print(f"  attempt {attempt} failed for {dest.name}: {e}")
            time.sleep(5 * attempt)
    print(f"  GIVE UP {dest.name}", file=sys.stderr)


def cmd_hmda(args):
    """Per state-year: download HMDA, apply the SSOT scope, keep a random sample.

    The API takes at most TWO filter criteria (plus state/year), so the server filters on
    loan_purposes=1 and actions_taken=1,3 and the rest of the scope (first lien, owner-occupied)
    is applied locally. A fixed fraction of in-scope rows is kept per state-year, which gives a
    state-proportional random sample of about 5% (~100k rows per year nationally).
    Raw state files are not kept; only the sample parts + a sampling log (for provenance).
    """
    import io
    import pandas as pd
    states = STATES if args.states == "all" else args.states.split(",")
    parts = RAW / "hmda" / "parts"
    parts.mkdir(parents=True, exist_ok=True)
    log = RAW / "hmda" / "sampling_log.csv"
    if not log.exists():
        log.write_text("year,state,rows_downloaded,rows_in_scope,rows_kept,downloaded_on"+chr(10))
    for y in parse_years(args.years):
        for st in states:
            dest = parts / f"hmda_{y}_{st}.csv"
            if dest.exists():
                continue
            url = f"{HMDA_URL}?states={st}&years={y}&loan_purposes=1&actions_taken=1,3"
            for attempt in range(1, 4):
                try:
                    r = requests.get(url, timeout=600)
                    r.raise_for_status()
                    break
                except requests.RequestException as e:
                    print(f"  {y} {st} attempt {attempt} failed: {e}")
                    time.sleep(5 * attempt)
            else:
                continue
            df = pd.read_csv(io.BytesIO(r.content), dtype=str, low_memory=False)
            n_dl = len(df)
            df = df[(df["lien_status"] == "1") & (df["occupancy_type"] == "1")]
            keep = df.sample(frac=args.frac, random_state=42 + y)
            keep.to_csv(dest, index=False)
            with open(log, "a") as f:
                f.write(f"{y},{st},{n_dl},{len(df)},{len(keep)},{time.strftime('%Y-%m-%d')}"+chr(10))
            print(f"HMDA {y} {st}: downloaded {n_dl:,}, in scope {len(df):,}, kept {len(keep):,}")


# ACS 5-year tract variables:
#   B19013_001E median household income, B25077_001E median house value,
#   B17001_001E / B17001_002E poverty universe / below poverty,
#   B23025_003E labor force, B23025_005E unemployed.
ACS_VARS = "B19013_001E,B25077_001E,B17001_001E,B17001_002E,B23025_003E,B23025_005E"


def cmd_acs(args):
    key = args.key
    for y in parse_years(args.years):
        # ACS 5-year ends 2023 at the latest we can rely on; HMDA year y uses ACS y (or y-1 if missing)
        for st_fips in [f"{i:02d}" for i in range(1, 57)]:
            params = {"get": "NAME," + ACS_VARS, "for": "tract:*", "in": f"state:{st_fips}"}
            if key:
                params["key"] = key
            dest = RAW / "acs" / f"acs_{y}_{st_fips}.json"
            if dest.exists():
                continue
            r = requests.get(f"https://api.census.gov/data/{y}/acs/acs5", params=params, timeout=120)
            if r.status_code == 200:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(r.content)
                print(f"ACS {y} state {st_fips} ok")
            else:
                print(f"ACS {y} state {st_fips} -> HTTP {r.status_code} (unused FIPS codes are normal)")


def cmd_fred(_args):
    download("https://fred.stlouisfed.org/graph/fredgraph.csv", {"id": "MORTGAGE30US"},
             RAW / "fred" / "MORTGAGE30US.csv")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("hmda"); h.add_argument("--years", default="2023"); h.add_argument("--states", default="all"); h.add_argument("--frac", type=float, default=0.05)
    h.set_defaults(fn=cmd_hmda)
    a = sub.add_parser("acs"); a.add_argument("--years", default="2023"); a.add_argument("--key", default=None)
    a.set_defaults(fn=cmd_acs)
    f = sub.add_parser("fred"); f.set_defaults(fn=cmd_fred)
    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
