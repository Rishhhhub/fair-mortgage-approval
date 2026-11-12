"""Tests for the scoring API. Run from the project root:  python tests/test_api.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_low_risk_vs_high_risk():
    low = client.post("/score", json=dict(dti_mid=30, loan_to_value_ratio=75, income_w=150000,
                                          loan_amount_w=300000, property_value_w=400000)).json()
    high = client.post("/score", json=dict(dti_mid=62, loan_to_value_ratio=100, income_w=40000,
                                           loan_amount_w=300000, property_value_w=300000)).json()
    print("low-risk applicant :", low["denial_probability"], low["recommendation"])
    print("high-risk applicant:", high["denial_probability"], high["recommendation"])
    assert 0 <= low["denial_probability"] <= 1
    assert high["denial_probability"] > low["denial_probability"]
    assert len(high["top_factors"]) == 3


def test_missing_fields_allowed():
    r = client.post("/score", json=dict(loan_amount_w=250000))
    assert r.status_code == 200


def test_bad_input_rejected():
    assert client.post("/score", json=dict(loan_amount_w=-5)).status_code == 422


def test_protected_attributes_rejected():
    for field in ["race", "sex", "age", "ethnicity"]:
        r = client.post("/score", json={"loan_amount_w": 250000, field: "x"})
        assert r.status_code == 422, f"API accepted protected field {field}"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("PASS", name)
