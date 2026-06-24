import mlflow
import mlflow.xgboost
import xgboost as xgb
import pandas as pd
import os
from sklearn.datasets import make_classification
from mlflow.tracking import MlflowClient

# Force local SQLite path
db_path = os.path.abspath("mlflow.db")
sqlite_uri = f"sqlite:///{db_path}"
mlflow.set_tracking_uri(sqlite_uri)

print(f"Using Tracking URI: {mlflow.get_tracking_uri()}")

# 1. Δημιουργία Dummy Δεδομένων (6 features)
X, y = make_classification(n_samples=100, n_features=6, n_informative=4, random_state=42)
cols = ["amount", "hour", "day_of_week", "merchant_category_enc", "avg_spend_7d", "total_trans_24h"]
X_df = pd.DataFrame(X, columns=cols)

# 2. Training
model = xgb.XGBClassifier()
model.fit(X_df, y)

# 3. Logging & Registration
with mlflow.start_run() as run:
    # Log model
    mlflow.xgboost.log_model(
        xgb_model=model, 
        artifact_path="intrusion_model",
        registered_model_name="intrusion_model"
    )
    
    # Register Alias
    client = MlflowClient()
    # Δίνουμε λίγο χρόνο στο registry να ενημερωθεί
    client.set_registered_model_alias("intrusion_model", "Production", "1")
    
    print("\n✅ ΕΠΙΤΥΧΙΑ!")
    print(f"✅ Το μοντέλο σώθηκε στο: {db_path}")
    print(f"✅ Run ID: {run.info.run_id}")