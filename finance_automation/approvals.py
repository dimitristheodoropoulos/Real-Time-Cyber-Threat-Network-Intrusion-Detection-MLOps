from .config import APPROVALS_DB_PATH
import sqlite3
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

DB_PATH = APPROVALS_DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS approvals (
            id TEXT PRIMARY KEY,
            journal_entry_id TEXT NOT NULL,
            description TEXT,
            debit_account TEXT,
            credit_account TEXT,
            amount REAL,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            reviewed_at TEXT,
            reviewer TEXT,
            comments TEXT
        )
    """)
    conn.commit()
    conn.close()

# Κλήση κατά την εκκίνηση
init_db()


class ApprovalRecord(BaseModel):
    id: str
    journal_entry_id: str
    description: str
    debit_account: str
    credit_account: str
    amount: float
    status: str = "pending"
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewer: Optional[str] = None
    comments: Optional[str] = None


def store_pending_entries(entries):
    """Αποθηκεύει λίστα ProposedJournalEntry ως pending approvals."""
    conn = get_connection()
    for entry in entries:
        conn.execute(
            """
            INSERT OR REPLACE INTO approvals 
            (id, journal_entry_id, description, debit_account, credit_account, amount, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
            """,
            (
                entry.entry_id,
                entry.entry_id,
                entry.description,
                entry.debit_account,
                entry.credit_account,
                entry.amount,
                datetime.now().isoformat()
            )
        )
    conn.commit()
    conn.close()


def list_pending():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM approvals WHERE status = 'pending'").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_approval(entry_id: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM approvals WHERE id = ?", (entry_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def approve_entry(entry_id: str, reviewer: str, comments: str = ""):
    conn = get_connection()
    conn.execute(
        """
        UPDATE approvals 
        SET status = 'approved', reviewed_at = ?, reviewer = ?, comments = ?
        WHERE id = ? AND status = 'pending'
        """,
        (datetime.now().isoformat(), reviewer, comments, entry_id)
    )
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


def reject_entry(entry_id: str, reviewer: str, comments: str = ""):
    conn = get_connection()
    conn.execute(
        """
        UPDATE approvals 
        SET status = 'rejected', reviewed_at = ?, reviewer = ?, comments = ?
        WHERE id = ? AND status = 'pending'
        """,
        (datetime.now().isoformat(), reviewer, comments, entry_id)
    )
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0