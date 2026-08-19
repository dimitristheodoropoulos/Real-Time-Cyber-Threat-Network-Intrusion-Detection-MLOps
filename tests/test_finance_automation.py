import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from finance_automation.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "finance-automation"

def test_reconcile_endpoint():
    payload = {
        "bank_transactions": [
            {"id": "B1", "date": "2026-03-01", "amount": 1000.0, "description": "Payment", "reference": "INV-1"},
            {"id": "B2", "date": "2026-03-02", "amount": 250.5, "description": "Office", "reference": None}
        ],
        "gl_transactions": [
            {"id": "GL1", "date": "2026-03-01", "amount": 1000.0, "description": "Payment", "reference": "INV-1"},
            {"id": "GL2", "date": "2026-03-10", "amount": 250.5, "description": "Office", "reference": None}
        ],
        "amount_tolerance": 0.01,
        "date_tolerance_days": 3
    }
    response = client.post("/reconcile", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["matched"]) == 1
    assert len(data["unmatched_bank"]) == 1
    assert len(data["unmatched_gl"]) == 1
    assert len(data["suggested_matches"]) == 1

def test_intercompany_match():
    payload = {
        "transactions_A": [
            {"id": "A1", "company": "A", "date": "2026-03-01", "amount": 5000.0, "reference": "INV-5001", "description": "Services"},
        ],
        "transactions_B": [
            {"id": "B1", "company": "B", "date": "2026-03-02", "amount": 5000.0, "reference": "INV-5001", "description": "Services"},
        ],
        "amount_tolerance": 0.01,
        "date_tolerance_days": 5
    }
    response = client.post("/intercompany/match", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["matched"]) == 1

def test_anomalies_endpoint():
    payload = [
        {"id": "J1", "date": "2026-03-05", "amount": 5000.0, "description": "Consulting fees", "posted_at": "2026-03-05T23:30:00"},
        {"id": "J2", "date": "2026-03-06", "amount": 5000.0, "description": "Consulting fees", "posted_at": "2026-03-06T09:00:00"},
    ]
    response = client.post("/anomalies", json=payload)
    assert response.status_code == 200
    data = response.json()
    types = [flag["type"] for flag in data["flags"]]
    assert "duplicate_payment" in types
    assert "round_amount" in types
