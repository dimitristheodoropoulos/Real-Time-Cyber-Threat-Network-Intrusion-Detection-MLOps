from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class ProposedJournalEntry(BaseModel):
    entry_id: str
    date: date
    description: str
    debit_account: str
    credit_account: str
    amount: float
    source: str   # π.χ. "unmatched_bank", "unmatched_gl", "mismatch"
    source_id: Optional[str] = None   # id της αρχικής συναλλαγής

class JournalEntryRequest(BaseModel):
    # Μπορεί να δεχθεί λίστες από unmatched transactions ή mismatched pairs
    unmatched_bank: List[dict] = []   # περιέχει id, date, amount, description
    unmatched_gl: List[dict] = []
    mismatches: List[dict] = []       # περιέχει two transactions και difference
    date: date                        # ημερομηνία εγγραφών

class JournalEntryResponse(BaseModel):
    entries: List[ProposedJournalEntry]

def generate_entries(request: JournalEntryRequest) -> JournalEntryResponse:
    entries = []
    counter = 1

    # Unmatched bank transactions: τράπεζα έχει κίνηση, GL δεν έχει -> πρέπει να μπει στο GL
    for item in request.unmatched_bank:
        entries.append(ProposedJournalEntry(
            entry_id=f"JE-{counter:04d}",
            date=request.date,
            description=f"Reconciliation adjustment for bank transaction {item.get('id')}: {item.get('description', '')}",
            debit_account="GL Clearing Account",   # Θα μπορούσε να είναι π.χ. "Cash"
            credit_account="Suspense Account",
            amount=float(item.get('amount', 0)),
            source="unmatched_bank",
            source_id=item.get('id')
        ))
        counter += 1

    # Unmatched GL transactions: GL έχει εγγραφή, τράπεζα δεν έχει -> πρέπει να μπει στην τράπεζα
    for item in request.unmatched_gl:
        entries.append(ProposedJournalEntry(
            entry_id=f"JE-{counter:04d}",
            date=request.date,
            description=f"Reconciliation adjustment for GL transaction {item.get('id')}: {item.get('description', '')}",
            debit_account="Suspense Account",
            credit_account="Bank Clearing Account",
            amount=float(item.get('amount', 0)),
            source="unmatched_gl",
            source_id=item.get('id')
        ))
        counter += 1

    # Mismatches: διαφορά ποσού ή ημερομηνίας -> γράφουμε τη διαφορά
    for mm in request.mismatches:
        # Εδώ υποθέτουμε ότι το mismatch έχει πεδίο amount_difference ή difference
        diff = mm.get('amount_difference') or mm.get('difference')
        if diff is None:
            # Αν έχουμε δύο transactions με διαφορετικά ποσά, υπολογίζουμε
            t1 = mm.get('A_transaction', {})
            t2 = mm.get('B_transaction', {})
            try:
                diff = float(t1.get('amount', 0)) - float(t2.get('amount', 0))
            except:
                continue
        if diff == 0:
            continue
        entries.append(ProposedJournalEntry(
            entry_id=f"JE-{counter:04d}",
            date=request.date,
            description=f"Adjustment for mismatch: {mm.get('issue', 'Unknown')}",
            debit_account="Write-off Account" if diff > 0 else "Intercompany Clearing",
            credit_account="Intercompany Clearing" if diff > 0 else "Write-off Account",
            amount=abs(diff),
            source="mismatch",
            source_id=mm.get('A_transaction', {}).get('id') or mm.get('B_transaction', {}).get('id')
        ))
        counter += 1

    return JournalEntryResponse(entries=entries)