def generate_insight(entry: dict) -> dict:
    """
    Παράγει rule-based insights για μια εγγραφή approval.
    """
    entry_id = entry.get("id", "")
    description = entry.get("description", "").lower()
    debit = entry.get("debit_account", "").lower()
    credit = entry.get("credit_account", "").lower()
    amount = float(entry.get("amount", 0))

    risk = "low"
    recommendation = "Approve"
    reasoning = []

    # Κατηγοριοποίηση βάσει περιγραφής
    if "unmatched_bank" in description or "unmatched_gl" in description:
        risk = "low"
        recommendation = "Approve"
        reasoning.append("Clearing entry for unmatched transaction; low risk if supporting bank/GL evidence is verified.")
    elif "mismatch" in description:
        # Ελέγχουμε αν το ποσό είναι μεγάλο
        if amount >= 1000:
            risk = "high"
            recommendation = "Reject / Investigate"
            reasoning.append("Large mismatch amount; investigate root cause and obtain counterparty confirmation before posting.")
        else:
            risk = "medium"
            recommendation = "Hold / Investigate"
            reasoning.append("Mismatch amount; verify with counterparty and supporting documentation.")

    # Επιπλέον έλεγχοι βάσει λογαριασμών
    if "write-off" in debit or "write-off" in credit:
        risk = "high"
        recommendation = "Reject / Investigate"
        reasoning.append("Direct write-off; avoid posting without investigation and approval.")

    if "suspense" in debit or "suspense" in credit or "clearing" in debit or "clearing" in credit:
        if risk == "low":
            reasoning.append("Balance sheet clearing accounts only; no P&L impact.")

    if not reasoning:
        reasoning.append("General entry; review for accuracy.")

    return {
        "entry_id": entry_id,
        "risk_level": risk,
        "recommendation": recommendation,
        "reasoning": " ".join(reasoning)
    }