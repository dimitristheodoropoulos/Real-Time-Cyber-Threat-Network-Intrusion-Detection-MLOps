from .config import OLLAMA_URL, OLLAMA_MODEL
import requests
import json
from typing import Optional
from .insights import generate_insight


def generate_llm_insight(entry: dict) -> dict:
    """
    Προσπαθεί να χρησιμοποιήσει τοπικό LLM μέσω Ollama.
    Αν αποτύχει, επιστρέφει το rule-based insight.
    """
    # Πρώτα δοκιμάζουμε το rule-based (για γρήγορη απάντηση και σταθερότητα)
    base_insight = generate_insight(entry)

    # Δημιουργούμε prompt για το LLM
    prompt = f"""
    You are a financial controller assistant.
    Given the following journal entry approval request, provide a concise recommendation (Approve/Reject/Hold) and a brief explanation.
    Entry: {json.dumps(entry, indent=2, default=str)}
    Base rule-based insight: {json.dumps(base_insight, indent=2)}
    """

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=5
        )
        if resp.status_code == 200:
            llm_response = resp.json().get("response", "").strip()
            if llm_response:
                # Επιστρέφουμε το LLM response μαζί με το fallback για διαφάνεια
                return {
                    "entry_id": entry.get("id"),
                    "risk_level": base_insight["risk_level"],
                    "recommendation": base_insight["recommendation"],
                    "reasoning": llm_response,
                    "source": "llm"
                }
    except Exception:
        pass

    # Fallback σε rule-based αν κάτι αποτύχει
    return {
        **base_insight,
        "source": "rule_based"
    }