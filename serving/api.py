import os
import sys
import logging
import hashlib
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import uvicorn
import requests
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter

# --- 1. CONFIGURATION & LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mlops_api")

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
TRAFFIC_RATIO = float(os.getenv("STAGING_TRAFFIC_RATIO", 0.1))

# --- 2. MOCK MODEL FOR MISSION SAFETY (Graceful Degradation) ---
class DummyModel:
    def predict(self, df):
        # Αν το packet_size είναι ύποπτα μεγάλο (> 65000 bytes - Ping of Death), σήμανε απειλή
        packet_size = df['packet_size'].iloc[0]
        return [1] if packet_size > 65000 else [0]

# --- 3. LOAD MODELS (MLflow Registry & Smart Fallbacks) ---
model_prod = DummyModel()
model_staging = DummyModel()
is_using_dummy = True

try:
    import mlflow.pyfunc
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    # Χρήση του επίσημου Model Registry URI ως default παραγωγική επιλογή
    prod_uri = os.getenv("PROD_MODEL_URI", "models:/network-intrusion-model/1")
    
    # Έλεγχος αν πρόκειται για native MLflow URI ή αν το path υπάρχει φυσικά στο δίσκο
    if prod_uri.startswith("models:/") or prod_uri.startswith("runs:/") or os.path.exists(prod_uri):
        model_prod = mlflow.pyfunc.load_model(prod_uri)
        model_staging = model_prod 
        is_using_dummy = False
        logger.info(f"✅ Cyber Threat Inference model loaded successfully from Registry ({prod_uri})!")
    else:
        # Έξυπνο fallback για τοπική εκτέλεση στο laptop (εκτός Docker) χρησιμοποιώντας το πρόσφατο επιτυχές Run ID
        local_fallback = "mlruns/0/c1096785c82e4077962c929534bbac70/artifacts/model"
        if os.path.exists(local_fallback):
            model_prod = mlflow.pyfunc.load_model(local_fallback)
            model_staging = model_prod
            is_using_dummy = False
            logger.info(f"✅ Loaded successfully from local fallback path: {local_fallback}")
        else:
            logger.warning(f"⚠️ Model URI/Path {prod_uri} not found. Operating in Backup Rule-Based Mode.")
except Exception as e:
    logger.warning(f"⚠️ Could not initialize MLflow Registry: {e}. Falling back to DummyModel.")

# --- 4. API SETUP ---
app = FastAPI(title="Network Intrusion Detection API - Mission Ready Deployment")
Instrumentator().instrument(app).expose(app)

PREDICTIONS_TOTAL = Counter('predictions_total', 'Total network traffic evaluations', ['variant', 'label'])

# Το σωστό Cyber-Security Schema
class NetworkLogRequest(BaseModel):
    source_ip_hash: str
    packet_size: float
    protocol_type_enc: int
    timestamp: str

# --- 5. HELPERS ---
def get_model_variant(source_ip_hash: str) -> str:
    hash_val = hashlib.md5(source_ip_hash.encode()).hexdigest()
    index = int(hash_val, 16) % 100
    return "staging" if index < (TRAFFIC_RATIO * 100) else "production"

def get_phi3_explanation(packet_size, protocol_enc, label):
    """Τοπικό Air-Gapped XAI για μέγιστη ασφάλεια δεδομένων."""
    try:
        prompt = (f"Analyze this network anomaly log: Packet Size is {packet_size} bytes, "
                  f"Protocol Encoded ID is {protocol_enc}. Explain briefly why this traffic "
                  f"pattern is flagged as an '{label}' alert.")
        resp = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": "phi3:mini", "prompt": prompt, "stream": False},
            timeout=2
        )
        return resp.json().get("response", "High-risk payload or traffic anomaly detected.")
    except:
        return "Network anomaly packet exceeds standard operational security thresholds."

# --- 6. ENDPOINTS ---
@app.post("/predict")
async def predict(request: NetworkLogRequest):
    try:
        dt = pd.to_datetime(request.timestamp)
        feature_vector = {
            "packet_size": request.packet_size,
            "hour": dt.hour,
            "day_of_week": dt.dayofweek,
            "protocol_type_enc": request.protocol_type_enc
        }
        
        variant = get_model_variant(request.source_ip_hash)
        selected_model = model_staging if variant == "staging" else model_prod
        
        input_df = pd.DataFrame([feature_vector])
        prediction = selected_model.predict(input_df)
        
        is_intrusion = int(prediction[0])
        label = "MALICIOUS" if is_intrusion == 1 else "BENIGN"
        
        PREDICTIONS_TOTAL.labels(variant=variant, label=label).inc()
        
        explanation = "Normal network activity pattern."
        if is_intrusion:
            explanation = get_phi3_explanation(request.packet_size, request.protocol_type_enc, label)

        return {
            "variant_used": variant,
            "is_intrusion": is_intrusion,
            "label": label,
            "llm_explanation": explanation,
            "mode": "Failover (Deterministic Rules)" if is_using_dummy else "Active MLflow (XGBoost)"
        }
    except Exception as e:
        logger.error(f"Inference Engine error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "operational", "failover_mode_active": is_using_dummy}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)