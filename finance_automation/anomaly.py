from typing import List, Dict, Any
from collections import Counter
from datetime import date
import math

def detect_duplicates(transactions: List[Dict], amount_tol: float = 0.01, days_window: int = 7) -> List[Dict]:
    flags = []
    for i, t1 in enumerate(transactions):
        for j, t2 in enumerate(transactions):
            if i >= j:
                continue
            if math.isclose(float(t1.get('amount', 0)), float(t2.get('amount', 0)), abs_tol=amount_tol):
                # Πιθανό duplicate: ίδιο ποσό και ίδια περιγραφή ή reference μέσα σε λίγες μέρες
                desc1 = t1.get('description', '').lower().strip()
                desc2 = t2.get('description', '').lower().strip()
                if desc1 and desc2 and desc1 == desc2:
                    date1 = t1.get('date')
                    date2 = t2.get('date')
                    if date1 and date2:
                        date_diff = abs((date1 - date2).days)
                        if date_diff <= days_window:
                            flags.append({
                                "type": "duplicate_payment",
                                "transaction_ids": [t1.get('id'), t2.get('id')],
                                "amount": float(t1.get('amount', 0)),
                                "description": t1.get('description', ''),
                                "reason": f"Same amount and description within {days_window} days"
                            })
    return flags

def detect_round_amounts(transactions: List[Dict], min_amount: float = 1000.0) -> List[Dict]:
    flags = []
    for t in transactions:
        amount = float(t.get('amount', 0))
        if amount == int(amount) and amount >= min_amount:
            flags.append({
                "type": "round_amount",
                "transaction_id": t.get('id'),
                "amount": amount,
                "reason": "Large round-dollar amount"
            })
    return flags

def detect_benford_anomalies(transactions: List[Dict]) -> List[Dict]:
    # Απλοποιημένο: ελέγχει αν η κατανομή πρώτου ψηφίου αποκλίνει σημαντικά από Benford
    first_digits = []
    for t in transactions:
        amount = float(t.get('amount', 0))
        if amount > 0:
            first_digits.append(int(str(amount).strip('0.')[0]))
    digit_counts = Counter(d for d in first_digits if d != 0)
    total = sum(digit_counts.values())
    benford = {1:0.301, 2:0.176, 3:0.125, 4:0.097, 5:0.079, 6:0.067, 7:0.058, 8:0.051, 9:0.046}
    flags = []
    for d, expected in benford.items():
        actual = digit_counts.get(d, 0) / total if total > 0 else 0
        if actual > expected * 1.5 or actual < expected * 0.5:
            flags.append({
                "type": "benford_anomaly",
                "digit": d,
                "expected_freq": expected,
                "actual_freq": round(actual, 3),
                "reason": "First digit frequency deviates from Benford's Law"
            })
    return flags

def detect_unusual_posting_times(transactions: List[Dict]) -> List[Dict]:
    flags = []
    for t in transactions:
        posted_at = t.get('posted_at')
        if posted_at:
            # Απλοποίηση: Σαββατοκύριακο ή ώρα 22:00-06:00
            if posted_at.weekday() >= 5 or posted_at.hour < 6 or posted_at.hour >= 22:
                flags.append({
                    "type": "unusual_posting_time",
                    "transaction_id": t.get('id'),
                    "posted_at": posted_at.isoformat(),
                    "reason": "Posted outside normal business hours"
                })
    return flags

def detect_missing_description(transactions: List[Dict]) -> List[Dict]:
    flags = []
    for t in transactions:
        if not t.get('description', '').strip():
            flags.append({
                "type": "missing_description",
                "transaction_id": t.get('id'),
                "amount": float(t.get('amount', 0)),
                "reason": "No description provided"
            })
    return flags

def run_anomaly_detection(transactions: List[Dict]) -> List[Dict]:
    all_flags = []
    all_flags.extend(detect_duplicates(transactions))
    all_flags.extend(detect_round_amounts(transactions))
    all_flags.extend(detect_benford_anomalies(transactions))
    all_flags.extend(detect_unusual_posting_times(transactions))
    all_flags.extend(detect_missing_description(transactions))
    return all_flags