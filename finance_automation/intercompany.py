from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import math

class IntercompanyTransaction(BaseModel):
    id: str
    company: str          # π.χ. "A" ή "B"
    date: date
    amount: float
    reference: Optional[str] = None   # π.χ. invoice number
    description: str = ""

class IntercompanyMatchRequest(BaseModel):
    transactions_A: List[IntercompanyTransaction]
    transactions_B: List[IntercompanyTransaction]
    amount_tolerance: float = 0.01
    date_tolerance_days: int = 30     # συνήθως πιο χαλαρό για intercompany

class IntercompanyMatchResult(BaseModel):
    matched: List[dict]
    mismatched: List[dict]
    unmatched_A: List[IntercompanyTransaction]
    unmatched_B: List[IntercompanyTransaction]
    suggested_matches: List[dict]

def amount_matches(a: float, b: float, tol: float) -> bool:
    return math.isclose(a, b, abs_tol=tol)

def days_between(d1: date, d2: date) -> int:
    return abs((d1 - d2).days)

def reference_match(ref_a: Optional[str], ref_b: Optional[str]) -> bool:
    if ref_a and ref_b:
        return ref_a.strip().lower() == ref_b.strip().lower()
    return False

def match_intercompany(request: IntercompanyMatchRequest) -> IntercompanyMatchResult:
    matched = []
    mismatched = []
    used_A = set()
    used_B = set()

    # Πρώτα βρίσκουμε matches με βάση reference
    for a in request.transactions_A:
        if a.id in used_A:
            continue
        for b in request.transactions_B:
            if b.id in used_B:
                continue
            if reference_match(a.reference, b.reference):
                if amount_matches(a.amount, b.amount, request.amount_tolerance):
                    if days_between(a.date, b.date) <= request.date_tolerance_days:
                        matched.append({
                            "A_transaction": a.model_dump(),
                            "B_transaction": b.model_dump(),
                            "confidence": 1.0,
                            "reason": "Reference + amount + date match"
                        })
                        used_A.add(a.id)
                        used_B.add(b.id)
                        break
                    else:
                        mismatched.append({
                            "A_transaction": a.model_dump(),
                            "B_transaction": b.model_dump(),
                            "issue": "Same reference and amount but date outside tolerance",
                            "difference_days": days_between(a.date, b.date)
                        })
                        used_A.add(a.id)
                        used_B.add(b.id)
                        break
                else:
                    mismatched.append({
                        "A_transaction": a.model_dump(),
                        "B_transaction": b.model_dump(),
                        "issue": "Same reference but different amount",
                        "amount_difference": round(a.amount - b.amount, 2)
                    })
                    used_A.add(a.id)
                    used_B.add(b.id)
                    break

    # Υπόλοιπα unmatched
    unmatched_A = [a for a in request.transactions_A if a.id not in used_A]
    unmatched_B = [b for b in request.transactions_B if b.id not in used_B]

    # Προτεινόμενα matches με βάση ποσό και ημερομηνία (χωρίς reference)
    suggested = []
    for a in unmatched_A:
        best_b = None
        best_conf = 0.0
        for b in unmatched_B:
            if b.id in used_B:
                continue
            if amount_matches(a.amount, b.amount, request.amount_tolerance):
                date_diff = days_between(a.date, b.date)
                if date_diff <= request.date_tolerance_days:
                    conf = 0.7
                    # Ενίσχυση αν οι περιγραφές μοιάζουν
                    desc_a = a.description.lower().strip()
                    desc_b = b.description.lower().strip()
                    if desc_a and desc_b and (desc_a in desc_b or desc_b in desc_a):
                        conf = 0.9
                    if conf > best_conf:
                        best_conf = conf
                        best_b = b
        if best_b:
            suggested.append({
                "A_id": a.id,
                "B_id": best_b.id,
                "confidence": best_conf,
                "reason": "Amount match, no common reference"
            })

    return IntercompanyMatchResult(
        matched=matched,
        mismatched=mismatched,
        unmatched_A=unmatched_A,
        unmatched_B=unmatched_B,
        suggested_matches=suggested
    )