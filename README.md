# Finance Automation & AI Platform

An end-to-end finance automation platform built with **FastAPI**, **SQLite**, **Pandas**, and **Streamlit**, designed to transform manual month‑end close processes into autonomous, data‑driven workflows. The platform automates reconciliations, intercompany matching, anomaly detection, journal entry generation, and human‑in‑the‑loop approvals, while providing AI‑powered insights through local LLMs with rule‑based fallback.

> **Note:** This repository focuses on **Finance Automation**. An older secondary project (Cyber Threat Detection) is briefly mentioned at the end for completeness and is not part of the main application.

---

## ✨ Key Features

### 1. Bank vs GL Reconciliation
- JSON and CSV/Excel upload.
- Fuzzy matching on amount, date, reference, and description.
- Outputs: matched, unmatched_bank, unmatched_gl, suggested_matches.
- Configurable tolerance for amount and date.

### 2. Intercompany Matching
- Transaction matching between group companies.
- Detects matched, mismatched, unmatched_A, unmatched_B.
- Suggests matches based on amount when references are missing.

### 3. Anomaly Detection
- Duplicate payments.
- Large round‑dollar amounts.
- Benford's Law deviations.
- Unusual posting times (weekend/night).
- Missing descriptions.

### 4. Journal Entry Generation
- Automatically generates proposed journal entries for:
  - Unmatched bank/GL transactions.
  - Mismatches between intercompany entities.
- Uses clearing, suspense, and write‑off accounts.

### 5. Human‑in‑the‑loop Approvals
- SQLite‑backed workflow with statuses: `pending`, `approved`, `rejected`.
- Audit trail: reviewer, reviewed_at, comments.
- API endpoints for approve/reject actions.

### 6. Insights & AI Recommendations
- Rule‑based insights for each approval entry (risk level, recommendation, reasoning).
- Optional LLM‑powered insights via Ollama (default `llama3`), with automatic fallback to rule‑based if Ollama is unavailable.

### 7. Webhook Receiver
- Accepts transaction payloads from external systems (ERP, payment gateways).
- Stores events in SQLite with source and received timestamp.

### 8. Streamlit Dashboard
- User‑friendly UI for:
  - Viewing and approving/rejecting pending entries.
  - Uploading CSV files for reconciliation.
  - Running intercompany matching.
  - Checking service health.

---

## 🛠️ Architecture Overview

| Layer | Technology |
|-------|------------|
| API | FastAPI (Uvicorn) |
| Database | SQLite (approvals, webhook events) |
| Data processing | Pandas, Python standard library |
| Dashboard | Streamlit |
| AI/LLM | Ollama (optional), rule‑based fallback |
| Testing | pytest, FastAPI TestClient |

---

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| POST | `/reconcile` | Bank vs GL reconciliation (JSON) |
| POST | `/reconcile/upload` | Upload CSV/Excel bank & GL files |
| POST | `/intercompany/match` | Intercompany transaction matching |
| POST | `/journal-entries/generate` | Generate proposed journal entries |
| GET | `/approvals/pending` | List pending approvals |
| POST | `/approvals/{entry_id}/approve` | Approve entry |
| POST | `/approvals/{entry_id}/reject` | Reject entry |
| GET | `/approvals/{entry_id}/insights` | Rule‑based approval insights |
| GET | `/approvals/{entry_id}/llm-insights` | LLM‑based insights (fallback to rules) |
| POST | `/anomalies` | Detect anomalies in GL transactions |
| POST | `/webhooks/transactions` | Receive external transactions |
| GET | `/webhooks/events` | List webhook events |

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/dimitristheodoropoulos/finance-automation-ai-platform.git
cd finance-automation-ai-platform
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements_finance.txt
```
If you plan to use LLM insights, install Ollama and pull a model (e.g., `llama3`). If Ollama is not running, the API automatically falls back to rule‑based insights.

### 4. Run the API
```bash
uvicorn finance_automation.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

### 5. Run the dashboard (optional)
In another terminal:
```bash
streamlit run finance_automation/dashboard.py
```

### 6. Run tests
```bash
pytest tests/
```

---

## 📦 Example Usage

### Reconciliation (JSON)
```bash
curl -X POST http://127.0.0.1:8000/reconcile \
  -H "Content-Type: application/json" \
  -d '{
    "bank_transactions": [
      {"id": "B1", "date": "2026-03-01", "amount": 1000.00, "description": "Payment to supplier", "reference": "INV-1001"}
    ],
    "gl_transactions": [
      {"id": "GL1", "date": "2026-03-01", "amount": 1000.00, "description": "Supplier invoice", "reference": "INV-1001"}
    ],
    "amount_tolerance": 0.01,
    "date_tolerance_days": 3
  }'
```

### Anomaly Detection
```bash
curl -X POST http://127.0.0.1:8000/anomalies \
  -H "Content-Type: application/json" \
  -d '[
    {"id": "J1", "date": "2026-03-05", "amount": 5000.00, "description": "Consulting fees", "posted_at": "2026-03-05T23:30:00"},
    {"id": "J2", "date": "2026-03-06", "amount": 5000.00, "description": "Consulting fees", "posted_at": "2026-03-06T09:00:00"}
  ]'
```

### Webhook
```bash
curl -X POST http://127.0.0.1:8000/webhooks/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "source": "stripe",
    "transactions": [
      {"id": "txn_001", "amount": 1000.00, "currency": "EUR", "description": "Payment for invoice 123"}
    ]
  }'
```

---

## 🧠 LLM Integration (Optional)
The platform can use a local LLM (e.g., Ollama with `llama3`) to generate richer approval insights. If Ollama is not available, it falls back to deterministic rule‑based recommendations, ensuring the system remains functional in any environment.

---

## 🧪 Tests
All core endpoints are covered by pytest tests:
```bash
pytest tests/
```

---

## 🛡️ Resilience & Engineering
The platform follows the principle of **graceful degradation**:
- LLM features automatically fall back to rule‑based logic if the local model is unavailable.
- SQLite databases are local and can be recreated automatically.
- API errors return structured JSON with HTTP status codes.

---

## 📂 Project Structure
```
finance_automation/
├── main.py               # FastAPI app & endpoints
├── reconciliation.py     # Bank vs GL matching logic
├── intercompany.py       # Intercompany matching
├── journal_entries.py    # Proposed journal entries
├── approvals.py          # Human‑in‑the‑loop approvals (SQLite)
├── anomaly.py            # Anomaly detection rules
├── insights.py           # Rule‑based approval insights
├── llm_helper.py         # LLM integration with fallback
├── webhooks.py           # Webhook receiver & event store
├── config.py             # Environment configuration
└── dashboard.py          # Streamlit dashboard
```

---

## 📎 Secondary Project (archived)
This repository also contains an older **Cyber Threat & Network Intrusion Detection MLOps platform** – a separate project that demonstrates additional MLOps capabilities (PySpark, MLflow, Prometheus, air‑gapped XAI). It is kept here for reference but is **not** part of the Finance Automation application.

---

Developed by Dimitris Theodoropoulos | Finance Automation & MLOps Engineer 🚀