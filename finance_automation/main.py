from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import math
import pandas as pd
import io

from .intercompany import (
    IntercompanyTransaction,
    IntercompanyMatchRequest,
    IntercompanyMatchResult,
    match_intercompany
)

app = FastAPI(title="Finance Automation API", version="0.4.0")


# ---------- Pydantic Models ----------
class BankTransaction(BaseModel):
    id: str
    date: date
    amount: float
    description: str = ""
    reference: Optional[str] = None


class GLTransaction(BaseModel):
    id: str
    date: date
    amount: float
    description: str = ""
    reference: Optional[str] = None


class ReconciliationRequest(BaseModel):
    bank_transactions: List[BankTransaction]
    gl_transactions: List[GLTransaction]
    amount_tolerance: float = 0.01
    date_tolerance_days: int = 3


class ReconciliationResult(BaseModel):
    matched: List[dict]
    unmatched_bank: List[BankTransaction]
    unmatched_gl: List[GLTransaction]
    suggested_matches: List[dict]


# ---------- Reconciliation Logic ----------
def amount_matches(a: float, b: float, tol: float) -> bool:
    return math.isclose(a, b, abs_tol=tol)


def days_between(d1: date, d2: date) -> int:
    return abs((d1 - d2).days)


def description_similarity(desc1: str, desc2: str) -> float:
    if not desc1 or not desc2:
        return 0.0
    d1 = desc1.lower().strip()
    d2 = desc2.lower().strip()
    if d1 == d2:
        return 1.0
    if d1 in d2 or d2 in d1:
        return 0.7
    return 0.0


def reconcile(request: ReconciliationRequest) -> ReconciliationResult:
    bank = request.bank_transactions
    gl = request.gl_transactions

    matched = []
    used_gl_ids = set()
    used_bank_ids = set()

    for b in bank:
        for g in gl:
            if g.id in used_gl_ids or b.id in used_bank_ids:
                continue
            if amount_matches(b.amount, g.amount, request.amount_tolerance):
                if days_between(b.date, g.date) <= request.date_tolerance_days:
                    ref_match = (b.reference and g.reference and b.reference == g.reference)
                    desc_sim = description_similarity(b.description, g.description)
                    if ref_match or desc_sim >= 0.7:
                        matched.append({
                            "bank_transaction": b.dict(),
                            "gl_transaction": g.dict(),
                            "confidence": 1.0 if ref_match else 0.9,
                            "reason": "Exact amount/date + reference/description"
                        })
                        used_bank_ids.add(b.id)
                        used_gl_ids.add(g.id)
                        break

    suggested = []
    for b in bank:
        if b.id in used_bank_ids:
            continue
        best_gl = None
        best_conf = 0.0
        best_reason = ""
        for g in gl:
            if g.id in used_gl_ids:
                continue
            if amount_matches(b.amount, g.amount, request.amount_tolerance):
                conf = 0.0
                reason = ""
                date_diff = days_between(b.date, g.date)
                if date_diff <= request.date_tolerance_days:
                    conf = 0.8
                    reason = "Amount match within date tolerance"
                    if b.reference and g.reference and b.reference == g.reference:
                        conf = 0.95
                        reason += " + reference match"
                    desc_sim = description_similarity(b.description, g.description)
                    if desc_sim > 0:
                        conf = max(conf, 0.7 + desc_sim * 0.2)
                        reason += " + description similarity"
                else:
                    conf = 0.5
                    reason = "Amount match only, date out of tolerance"
                if conf > best_conf:
                    best_conf = conf
                    best_gl = g
                    best_reason = reason
        if best_gl and best_conf >= 0.5:
            suggested.append({
                "bank_id": b.id,
                "gl_id": best_gl.id,
                "confidence": round(best_conf, 2),
                "reason": best_reason
            })

    unmatched_bank = [b for b in bank if b.id not in used_bank_ids]
    unmatched_gl = [g for g in gl if g.id not in used_gl_ids]

    return ReconciliationResult(
        matched=matched,
        unmatched_bank=unmatched_bank,
        unmatched_gl=unmatched_gl,
        suggested_matches=suggested
    )


# ---------- CSV/Excel Parsing ----------
def parse_bank_file(file: UploadFile) -> List[BankTransaction]:
    content = file.file.read()
    try:
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
    except Exception:
        df = pd.read_excel(io.BytesIO(content))

    df.columns = [c.lower().strip() for c in df.columns]

    transactions = []
    for _, row in df.iterrows():
        transactions.append(BankTransaction(
            id=str(row.get('id', '')),
            date=pd.to_datetime(row['date']).date(),
            amount=float(row['amount']),
            description=str(row.get('description', '') or ''),
            reference=str(row.get('reference', '')) if pd.notna(row.get('reference')) else None
        ))
    return transactions


def parse_gl_file(file: UploadFile) -> List[GLTransaction]:
    content = file.file.read()
    try:
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
    except Exception:
        df = pd.read_excel(io.BytesIO(content))

    df.columns = [c.lower().strip() for c in df.columns]

    transactions = []
    for _, row in df.iterrows():
        transactions.append(GLTransaction(
            id=str(row.get('id', '')),
            date=pd.to_datetime(row['date']).date(),
            amount=float(row['amount']),
            description=str(row.get('description', '') or ''),
            reference=str(row.get('reference', '')) if pd.notna(row.get('reference')) else None
        ))
    return transactions


# ---------- Endpoints ----------
@app.get("/health")
def health():
    return {"status": "ok", "service": "finance-automation"}


@app.post("/reconcile", response_model=ReconciliationResult)
def reconcile_endpoint(request: ReconciliationRequest):
    try:
        return reconcile(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reconcile/upload", response_model=ReconciliationResult)
def reconcile_upload_endpoint(
    bank_file: UploadFile = File(...),
    gl_file: UploadFile = File(...),
    amount_tolerance: float = 0.01,
    date_tolerance_days: int = 3
):
    try:
        bank_transactions = parse_bank_file(bank_file)
        gl_transactions = parse_gl_file(gl_file)
        request = ReconciliationRequest(
            bank_transactions=bank_transactions,
            gl_transactions=gl_transactions,
            amount_tolerance=amount_tolerance,
            date_tolerance_days=date_tolerance_days
        )
        return reconcile(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/intercompany/match", response_model=IntercompanyMatchResult)
def intercompany_match_endpoint(request: IntercompanyMatchRequest):
    try:
        return match_intercompany(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))