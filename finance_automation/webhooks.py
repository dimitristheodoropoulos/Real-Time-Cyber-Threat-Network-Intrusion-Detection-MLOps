from .config import WEBHOOKS_DB_PATH
import sqlite3
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

DB_PATH = WEBHOOKS_DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS webhook_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            payload TEXT NOT NULL,
            received_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

class WebhookPayload(BaseModel):
    source: str              # π.χ. "stripe", "sap", "bank"
    transactions: List[dict] # λίστα με transaction data

def store_webhook_event(source: str, payload: dict):
    conn = get_connection()
    conn.execute(
        "INSERT INTO webhook_events (source, payload, received_at) VALUES (?, ?, ?)",
        (source, str(payload), datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def list_webhook_events(source: Optional[str] = None):
    conn = get_connection()
    if source:
        rows = conn.execute("SELECT * FROM webhook_events WHERE source = ? ORDER BY received_at DESC", (source,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM webhook_events ORDER BY received_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]