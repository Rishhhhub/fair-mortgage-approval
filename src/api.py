"""Step 4: a small API that scores a mortgage application (the 'Recommendation' in BADIR).

Run:   uvicorn src.api:app --reload          (from the project root)
Docs:  http://127.0.0.1:8000/docs             (interactive page where you can try it)

What it does
  POST /score   -> probability the application would be denied, a recommendation, and the 3
                   factors that pushed the score most (SHAP values from the model itself).
  GET  /health  -> model version info.
  GET  /dashboard (also /) -> a web page where you type an application and see the result.

What it deliberately does NOT accept: race, ethnicity, sex or age. The model was trained without
them (fair-lending law), so the API has no field for them either.
"""
import json
from pathlib import Path
from typing import Optional

import lightgbm as lgb
import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parents[1]
CARD = json.loads((ROOT / "models" / "model_card.json").read_text())
MODEL = lgb.Booster(model_file=str(ROOT / "models" / "lgbm_denial.txt"))
FEATURES, CATEG, THRESHOLD = CARD["features"], CARD["categorical"], CARD["threshold"]

app = FastAPI(title="Fair Mortgage Approval - scoring API",
              description="Scores how likely a home-purchase application is to be denied. "
                          "Trained on HMDA 2018-2022; decision support only, not a final decision.")


class Application(BaseModel):
    """One mortgage application. Money in US dollars. Leave a field out if unknown (the model handles gaps)."""
    model_config = ConfigDict(extra="forbid")      # any unknown field (e.g. 'race') is rejected with an error
    dti_mid: Optional[float] = Field(None, description="Debt-to-income ratio in %, e.g. 38")
    loan_to_value_ratio: Optional[float] = Field(None, description="Loan-to-value ratio in %, e.g. 90")
    income_w: Optional[float] = Field(None, gt=0, description="Annual applicant income, $")
    loan_amount_w: float = Field(..., gt=0, description="Loan amount, $")
    property_value_w: Optional[float] = Field(None, gt=0, description="Property value, $")
    loan_term: Optional[float] = Field(360, description="Loan term in months")
    total_units: Optional[float] = Field(1, description="Number of units in the property")
    tract_to_msa_income_percentage: Optional[float] = Field(None, description="Tract median income as % of metro median")
    acs_median_hh_income_real: Optional[float] = Field(None, description="Tract median household income, 2023 $")
    acs_poverty_rate: Optional[float] = Field(None, description="Tract poverty rate, 0-1")
    acs_unemployment_rate: Optional[float] = Field(None, description="Tract unemployment rate, 0-1")
    loan_type: str = Field("1", description="1 conventional, 2 FHA, 3 VA, 4 USDA")
    derived_loan_product_type: str = Field("Conventional:First Lien")
    derived_dwelling_category: str = Field("Single Family (1-4 Units):Site-Built")
    construction_method: str = Field("1", description="1 site-built, 2 manufactured")
    preapproval: str = Field("2", description="1 = a pre-approval request, 2 = not")


def to_frame(app_in: Application) -> pd.DataFrame:
    row = app_in.model_dump()
    if row["income_w"] and row["loan_amount_w"]:
        row["loan_to_income"] = row["loan_amount_w"] / row["income_w"]      # derived exactly as in the build script
    else:
        row["loan_to_income"] = None
    X = pd.DataFrame([row])[FEATURES]
    for c in CATEG:                                                          # same categories as in training
        X[c] = pd.Categorical(X[c], categories=CARD["categories"][c])
    for c in set(FEATURES) - set(CATEG):
        X[c] = pd.to_numeric(X[c], errors="coerce")
    return X


@app.get("/", include_in_schema=False)
@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(ROOT / "src" / "dashboard.html")


@app.get("/health")
def health():
    return {"status": "ok", "trained_on": CARD["trained_on"], "tested_on": CARD["tested_on"],
            "threshold": THRESHOLD, "auc_complete_cases_2023": round(CARD["auc_complete_cases"], 3),
            "inputs_excluded_on_purpose": CARD["excluded_on_purpose"]}


@app.post("/score")
def score(application: Application):
    X = to_frame(application)
    p = float(MODEL.predict(X)[0])
    contrib = MODEL.predict(X, pred_contrib=True)[0][:-1]                     # SHAP values, last entry is the baseline
    top = sorted(zip(FEATURES, contrib), key=lambda t: -abs(t[1]))[:3]
    return {
        "denial_probability": round(p, 4),
        "recommendation": "REFER FOR MANUAL REVIEW (high denial risk)" if p >= THRESHOLD else "LOW DENIAL RISK",
        "threshold_used": THRESHOLD,
        "top_factors": [{"feature": f, "shap_log_odds": round(float(v), 3),
                         "direction": "raises denial risk" if v > 0 else "lowers denial risk"} for f, v in top],
        "note": "Decision support only. The model has no credit score and cannot see everything an underwriter sees.",
    }
