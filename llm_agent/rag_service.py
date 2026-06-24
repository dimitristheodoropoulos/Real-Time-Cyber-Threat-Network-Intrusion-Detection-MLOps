import chromadb
from chromadb.utils import embedding_functions
import requests
import logging

logger = logging.getLogger(__name__)

class IntrusionRAGService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.emb_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="bank_policies",
            embedding_function=self.emb_fn
        )
        self._seed_policies()

    def _seed_policies(self):
        if self.collection.count() == 0:
            policies = [
                "Policy: Transactions over 500 Euro at night (23:00-05:00) require manual review.",
                "Policy: High frequency of small transactions from the same user is a sign of card testing.",
                "Policy: Merchant category 5411 (Grocery) has low intrusion risk, while 7995 (Gambling) is high risk.",
                "Policy: International transactions on new accounts must be blocked immediately."
            ]
            ids = [f"id{i}" for i in range(len(policies))]
            self.collection.add(documents=policies, ids=ids)
            logger.info("Vector DB seeded with bank policies.")

    def get_contextual_explanation(self, amount: float, hour: int, label: str):
        # A. RETRIEVE
        query_text = f"Transaction amount {amount} at {hour}:00 flagged as {label}"
        results = self.collection.query(query_texts=[query_text], n_results=1)
        relevant_policy = results['documents'][0][0]
        
        print(f"🔍 Found Policy: {relevant_policy}") # Debug print

        # B. AUGMENT
        enriched_prompt = f"""
        CONTEXT FROM BANK POLICY: {relevant_policy}
        USER TRANSACTION: Amount {amount}, Hour {hour}, Status {label}.
        TASK: Explain why this transaction was flagged based on the policy. One short sentence.
        """

        # C. GENERATE (Αυξημένο timeout για τον i7-3520M)
        try:
            print("🧠 LLM is thinking (this may take up to 60s)...")
            response = requests.post(
                "http://127.0.0.1:11434/api/generate",
                json={"model": "tinyllama", "prompt": enriched_prompt, "stream": False},
                timeout=60 # Δώσαμε χρόνο στον επεξεργαστή
            )
            return response.json().get('response', "Policy match found but LLM failed.").strip()
        except Exception as e:
            print(f"⚠️ LLM Error: {e}")
            return f"Policy Match: {relevant_policy} (LLM Timeout)"

rag_service = IntrusionRAGService()