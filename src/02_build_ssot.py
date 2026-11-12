"""Step 2: build the Single Source of Truth (SSOT) table.

One row = one mortgage application (home purchase, first lien, owner-occupied,
originated or denied). Sources joined:

    HMDA  (sampled parts from 01_download.py)    -- the base table
    ACS   5-year tract data   -- joined on census tract (11-digit GEOID) + year
    FRED  30-yr mortgage rate -- joined on year (yearly mean of the weekly series)
    FRED  CPI                 -- joined on year (used to put dollar amounts in 2023 dollars)

Every step prints row counts / match rates and the same facts are saved to
reports/data_quality_report.md so they can go straight into the final report.

Run:  python src/02_build_ssot.py
"""
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
REPORT = ROOT / "reports" / "data_quality_report.md"
BASE_YEAR = 2023            # all dollar values are expressed in 2023 dollars

report = []                 # lines of the markdown data-quality report


def log(msg):
    """Print and remember a line for the data-quality report."""
    print(msg)
    report.append(msg)


# --------------------------------------------------------------------------
# 1. HMDA: load, clean, derive
# --------------------------------------------------------------------------
def load_hmda():
    files = sorted(glob.glob(str(RAW / "hmda" / "parts" / "hmda_*.csv")))
    # dtype=str: read everything as text first so nothing is silently mis-typed
    df = pd.concat((pd.read_csv(f, dtype=str) for f in files), ignore_index=True)
    log(f"- HMDA: {len(files)} state-year files loaded -> {len(df):,} rows, {df.shape[1]} columns")
    return df


def clean_hmda(df):
    n0 = len(df)

    # Duplicates: an exact duplicate row carries no new information.
    df = df.drop_duplicates()
    log(f"- Duplicate rows removed: {n0 - len(df):,}")

    # Missing values: HMDA uses text codes for 'not applicable / not provided'.
    # We turn them into real missing values (NaN).
    df = df.replace({"NA": np.nan, "Exempt": np.nan, "": np.nan})

    # Numeric columns (text -> numbers; anything unparseable becomes NaN)
    for c in ["loan_amount", "property_value", "income", "interest_rate", "rate_spread",
              "loan_to_value_ratio", "loan_term", "total_loan_costs", "tract_population",
              "tract_minority_population_percent", "tract_to_msa_income_percentage",
              "ffiec_msa_md_median_family_income", "tract_owner_occupied_units",
              "tract_one_to_four_family_homes", "tract_median_age_of_housing_units",
              "total_units", "activity_year"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Income in HMDA is in THOUSANDS of dollars -> convert to dollars.
    df["income"] = df["income"] * 1000

    # Target variable: 1 = denied, 0 = originated (approved and funded)
    df["denied"] = (df["action_taken"] == "3").astype(int)

    # Impossible values: set to missing (counted in the report, not silently dropped)
    bad_loan = (df["loan_amount"] <= 0)
    bad_income = (df["income"] <= 0)
    bad_ltv = (df["loan_to_value_ratio"] <= 0) | (df["loan_to_value_ratio"] > 200)
    log(f"- Impossible values set to missing: loan_amount<=0: {bad_loan.sum():,}; "
        f"income<=0: {bad_income.sum():,}; LTV<=0 or >200: {bad_ltv.sum():,}")
    df.loc[bad_loan, "loan_amount"] = np.nan
    df.loc[bad_income, "income"] = np.nan
    df.loc[bad_ltv, "loan_to_value_ratio"] = np.nan

    # DTI: HMDA gives some exact values (e.g. '38') and some ranges (e.g. '30%-<36%').
    # dti_mid = the exact value, or the midpoint of the range (a transparent approximation).
    # dti_is_exact tells us which rows are exact so we can check robustness later.
    range_mid = {"<20%": 15, "20%-<30%": 25, "30%-<36%": 33, "50%-60%": 55, ">60%": 65}
    dti = df["debt_to_income_ratio"]
    exact = pd.to_numeric(dti, errors="coerce")
    df["dti_is_exact"] = exact.notna()
    df["dti_mid"] = exact.fillna(dti.map(range_mid))
    df["dti_missing"] = df["dti_mid"].isna()
    return df


# --------------------------------------------------------------------------
# 2. ACS: tract-level covariates
# --------------------------------------------------------------------------
def load_acs():
    rows = []
    for f in sorted(glob.glob(str(RAW / "acs" / "acs_*.json"))):
        year = int(Path(f).stem.split("_")[1])
        data = json.load(open(f))
        t = pd.DataFrame(data[1:], columns=data[0])
        t["acs_year"] = year
        rows.append(t)
    a = pd.concat(rows, ignore_index=True)
    a["census_tract"] = a["state"] + a["county"] + a["tract"]          # 11-digit GEOID
    a = a.rename(columns={"B19013_001E": "acs_median_hh_income", "B25077_001E": "acs_median_house_value",
                          "B17001_001E": "acs_poverty_universe", "B17001_002E": "acs_below_poverty",
                          "B23025_003E": "acs_labor_force", "B23025_005E": "acs_unemployed"})
    num = ["acs_median_hh_income", "acs_median_house_value", "acs_poverty_universe",
           "acs_below_poverty", "acs_labor_force", "acs_unemployed"]
    for c in num:
        a[c] = pd.to_numeric(a[c], errors="coerce")
        a.loc[a[c] < 0, c] = np.nan          # the Census uses large negative numbers for 'not available'
    a["acs_poverty_rate"] = a["acs_below_poverty"] / a["acs_poverty_universe"]
    a["acs_unemployment_rate"] = a["acs_unemployed"] / a["acs_labor_force"]
    log(f"- ACS: {len(a):,} tract-year rows ({a['acs_year'].nunique()} years)")
    keep = ["census_tract", "acs_year", "acs_median_hh_income", "acs_median_house_value",
            "acs_poverty_rate", "acs_unemployment_rate"]
    return a[keep]


# --------------------------------------------------------------------------
# 3. FRED: mortgage rate and CPI, by year
# --------------------------------------------------------------------------
def load_fred():
    rate = pd.read_csv(RAW / "fred" / "MORTGAGE30US.csv", parse_dates=["observation_date"])
    rate["year"] = rate["observation_date"].dt.year
    rate = rate.groupby("year", as_index=False)["MORTGAGE30US"].mean().rename(
        columns={"MORTGAGE30US": "fred_mortgage_rate_30y"})

    cpi = pd.read_csv(RAW / "fred" / "CPIAUCSL.csv", parse_dates=["observation_date"])
    cpi["year"] = cpi["observation_date"].dt.year
    cpi = cpi.groupby("year", as_index=False)["CPIAUCSL"].mean().rename(columns={"CPIAUCSL": "cpi"})
    cpi["cpi_factor_to_2023"] = cpi.loc[cpi["year"] == BASE_YEAR, "cpi"].iloc[0] / cpi["cpi"]
    return rate.merge(cpi, on="year", how="inner")


# --------------------------------------------------------------------------
# 4. Joins with checks
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# 3b. HMDA Reporter Panel: lender type (downloaded by hand from ffiec.cfpb.gov, see README)
# --------------------------------------------------------------------------
def load_panel():
    files = sorted(glob.glob(str(RAW / "panel" / "20*" / "*.csv")))
    p = pd.concat((pd.read_csv(f, dtype=str) for f in files), ignore_index=True)
    p["year"] = p["activity_year"].astype(int)
    p = p[p["year"].between(2018, 2023)].drop_duplicates(["lei", "year"])
    code = p["other_lender_code"]
    name = p["respondent_name"].fillna("").str.upper()
    # Credit union: regulated by NCUA (agency 5) OR the registered name says so (large credit unions are
    # supervised by the CFPB, agency 9, so agency code alone would miss them).
    is_cu = (p["agency_code"] == "5") | name.str.contains("CREDIT UNION|FCU|FEDERAL CREDIT")
    # other_lender_code (official definition): 0 depository institution, 1/2 mortgage-banking subsidiary of a
    # bank / bank holding company, 3 independent mortgage banking company, 5 affiliate of a depository institution
    p["lender_type"] = np.select(
        [code == "3", code.isin(["1", "2", "5"]), (code == "0") & is_cu, code == "0"],
        ["non_bank_mortgage_company", "bank_affiliate", "credit_union", "bank"], default="unknown")
    p["panel_assets"] = pd.to_numeric(p["assets"], errors="coerce").where(lambda a: a > 0)
    p = p.rename(columns={"other_lender_code": "panel_other_lender_code", "agency_code": "panel_agency_code"})
    log(f"- Reporter Panel: {len(files)} yearly files, {len(p):,} lender-year rows; "
        f"lender types: {p['lender_type'].value_counts().to_dict()}")
    return p[["lei", "year", "lender_type", "panel_assets", "panel_other_lender_code", "panel_agency_code"]]


def checked_merge(left, right, on, name):
    """Left join + the checks required by the plan: row count unchanged, match rate reported."""
    n_before = len(left)
    # validate='m:1' stops the run if the right table has duplicate keys (which would silently duplicate rows)
    out = left.merge(right, on=on, how="left", validate="m:1", indicator=True)
    assert len(out) == n_before, f"{name}: join changed the row count!"
    matched = out["_merge"] == "both"
    log(f"- Join {name}: rows {n_before:,} -> {len(out):,} (unchanged); match rate {matched.mean():.1%}")
    by_year = matched.groupby(out["year"]).mean().round(3).to_dict() if "year" in out else {}
    log(f"  match rate by year: {by_year}")
    return out.drop(columns="_merge")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    log("# Data-quality report (generated by src/02_build_ssot.py)\n")
    log("## 1. HMDA base table")
    df = clean_hmda(load_hmda())
    df["year"] = df["activity_year"].astype(int)
    # Tract boundaries changed: HMDA 2018-2021 use 2010 tracts, 2022+ use 2020 tracts. We tested
    # which ACS year matches each HMDA year's tracts (2018/2019 ACS = 2010 tracts; 2022/2023 ACS =
    # 2020 tracts), so HMDA 2020 and 2021 are joined to ACS 2019 (latest ACS with 2010 tracts).
    df["acs_year"] = df["year"].map({2018: 2018, 2019: 2019, 2020: 2019, 2021: 2019, 2022: 2022, 2023: 2023})
    log("- ACS vintage used per HMDA year: 2018->2018, 2019->2019, 2020->2019, 2021->2019, 2022->2022, 2023->2023 (matches tract-boundary vintage)")

    log("\n## 2. Joins")
    acs = load_acs()
    df = checked_merge(df, acs, on=["census_tract", "acs_year"], name="HMDA + ACS (tract, year)")
    fred = load_fred()
    df = checked_merge(df, fred, on="year", name="HMDA + FRED (year)")
    df = checked_merge(df, load_panel(), on=["lei", "year"], name="HMDA + Reporter Panel (LEI, year)")
    df["lender_type"] = df["lender_type"].fillna("unknown")      # lenders with no panel match

    log("\n## 3. Derived variables (all computed from the observed columns)")
    # Outliers: a few incomes / loan amounts are absurd (income up to ~$846M). We KEEP the original
    # columns untouched and make winsorized copies (values below the 0.5th / above the 99.5th
    # percentile are pulled in to those limits). All *_real columns and loan_to_income use the
    # winsorized copies, so extreme values cannot dominate averages or models.
    out_flag = pd.Series(False, index=df.index)
    for c in ["loan_amount", "income", "property_value"]:
        lo, hi = df[c].quantile([0.005, 0.995])
        out_flag |= (df[c] < lo) | (df[c] > hi)
        df[c + "_w"] = df[c].clip(lo, hi)
        log(f"- Winsorized {c}: limits {lo:,.0f} to {hi:,.0f}")
    df["outlier_flag"] = out_flag
    log(f"- Rows with at least one extreme value (flagged, kept): {out_flag.sum():,} ({out_flag.mean():.1%})")
    # dollar values in 2023 dollars
    for c in ["loan_amount_w", "income_w", "property_value_w", "acs_median_hh_income", "acs_median_house_value"]:
        df[c.replace("_w", "") + "_real"] = df[c] * df["cpi_factor_to_2023"]
    df["loan_to_income"] = df["loan_amount_w"] / df["income_w"]
    df["dti_above_43"] = (df["dti_mid"] > 43).astype("float").where(df["dti_mid"].notna())
    df["low_income_tract"] = (df["tract_to_msa_income_percentage"] < 80).astype("float").where(
        df["tract_to_msa_income_percentage"].notna())     # <80% of area income = 'low/moderate' (FFIEC rule)
    df["tract_matched_acs"] = df["acs_median_hh_income"].notna()
    log("- Added: *_real columns (2023 dollars), loan_to_income, dti_mid / dti_above_43, low_income_tract, denied")

    # drop columns we will not use (detailed co-applicant / multi-race slots) to keep the table readable
    drop = [c for c in df.columns if any(c.startswith(p) for p in
            ("co-applicant_ethnicity", "co-applicant_race", "applicant_ethnicity-", "applicant_race-",
             "aus-", "denial_reason-2", "denial_reason-3", "denial_reason-4"))]
    df = df.drop(columns=drop)
    log(f"- Columns after dropping unused detail columns: {df.shape[1]}")

    log("\n## 4. Final table")
    log(f"- Rows: {len(df):,}   Columns: {df.shape[1]}")
    log(f"- Denial rate overall: {df['denied'].mean():.1%}")
    log(f"- Rows per year: {df['year'].value_counts().sort_index().to_dict()}")
    miss = df.isna().mean().sort_values(ascending=False)
    log("- Columns with most missing values (share missing):")
    for c, v in miss.head(12).items():
        log(f"    {c}: {v:.1%}")

    # object columns -> category/string so Parquet stores them cleanly
    for c in df.select_dtypes(include=["object", "str"]).columns:
        df[c] = df[c].astype("string")
    df.to_parquet(OUT / "ssot.parquet", index=False)
    log(f"- Saved {OUT / 'ssot.parquet'}")
    REPORT.write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
