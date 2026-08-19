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

def test_journal_entries_and_approvals():
    # Δημιουργία ενός journal entry μέσω API
    payload = {
        "unmatched_bank": [
            {"id": "B2", "date": "2026-03-02", "amount": 250.5, "description": "Office supplies"}
        ],
        "unmatched_gl": [],
        "mismatches": [],
        "date": "2026-03-31"
    }
    resp = client.post("/journal-entries/generate", json=payload)
    assert resp.status_code == 200
    entries = resp.json()["entries"]
    assert len(entries) == 1
    entry_id = entries[0]["entry_id"]

    # Έλεγχος ότι είναι pending
    resp = client.get("/approvals/pending")
    assert resp.status_code == 200
    pending = resp.json()
    assert any(e["id"] == entry_id for e in pending)

    # Έγκριση
    resp = client.post(f"/approvals/{entry_id}/approve", params={"reviewer": "test_user", "comments": "OK"})
    assert resp.status_code == 200

    # Δεν είναι πλέον pending
    resp = client.get("/approvals/pending")
    pending = resp.json()
    assert all(e["id"] != entry_id for e in pending)


def test_webhook_receiver_and_events():
    payload = {
        "source": "test_source",
        "transactions": [
            {"id": "txn_1", "amount": 100.0, "currency": "EUR", "description": "Test transaction"}
        ]
    }
    resp = client.post("/webhooks/transactions", json=payload)
    assert resp.status_code == 200

    # Λήψη events με filter
    resp = client.get("/webhooks/events", params={"source": "test_source"})
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) >= 1
    assert events[-1]["source"] == "test_source"


def test_llm_insights_fallback():
    # Δημιουργία εγγραφής για να πάρουμε insights
    payload = {
        "unmatched_bank": [{"id": "B3", "date": "2026-03-03", "amount": 750.0, "description": "Test entry"}],
        "unmatched_gl": [],
        "mismatches": [],
        "date": "2026-03-31"
    }
    resp = client.post("/journal-entries/generate", json=payload)
    entry_id = resp.json()["entries"][0]["entry_id"]

    # Λήψη LLM insights (θα πέσει σε fallback)
    resp = client.get(f"/approvals/{entry_id}/llm-insights")
    assert resp.status_code == 200
    data = resp.json()
    assert "recommendation" in data
    assert "risk_level" in data
    # Εφόσον Ollama δεν είναι διαθέσιμο, περιμένουμε rule_based
    assert data.get("source") == "rule_based"