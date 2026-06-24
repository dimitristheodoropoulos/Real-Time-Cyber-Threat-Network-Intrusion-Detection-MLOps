"""
Network Intrusion Detection - Production Training Pipeline
Distributed Spark + XGBoost + MLflow Model Registry
"""

import os
import logging
import mlflow
import mlflow.xgboost
from mlflow.tracking import MlflowClient
import xgboost as xgb
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, roc_auc_score, precision_score, 
    recall_score, f1_score, confusion_matrix
)

# Configuration με δυναμικά fallbacks για τοπικό .venv και Docker compatibility
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
SPARK_MASTER = os.getenv("SPARK_MASTER_URL", "local[*]")
DATA_PATH = os.getenv("DATA_PATH", "data/processed_network_logs.parquet")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data_distributed():
    """Φόρτωση δεδομένων μεγάλης κλίμακας μέσω Spark (Parquet optimization)."""
    logger.info(f"Connecting to Mission Infrastructure Spark Master: {SPARK_MASTER}")
    spark = SparkSession.builder \
        .appName("NetworkIntrusionProductionTraining") \
        .master(SPARK_MASTER) \
        .config("spark.executor.memory", "1g") \
        .config("spark.driver.memory", "1g") \
        .getOrCreate()

    try:
        logger.info(f"Reading Structured Parquet from: {DATA_PATH}")
        df_spark = spark.read.parquet(DATA_PATH)
        df = df_spark.toPandas()
        return df
    finally:
        spark.stop()

def prepare_features(df):
    """Feature engineering για Network Packets."""
    # Αν το protocol_type έρχεται ως string (κατηγορική), το μετατρέπουμε σε κωδικοποιημένο ακέραιο
    if 'protocol_type' in df.columns and 'protocol_type_enc' not in df.columns:
        df["protocol_type_enc"] = pd.Categorical(df["protocol_type"]).codes
    elif 'protocol_type_enc' not in df.columns:
        df["protocol_type_enc"] = 0
    
    feature_cols = ["packet_size", "hour", "day_of_week", "protocol_type_enc"]
    X = df[feature_cols].fillna(0)
    y = df["is_intrusion"]
    
    return X, y, feature_cols

def train_production_model():
    """Main Training & Automated Model Registration."""
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment("network_intrusion_detection_prod")

    with mlflow.start_run(run_name="XGBoost_Cyber_Edge_Run") as run:
        df = load_data_distributed()
        X, y, feature_cols = prepare_features(df)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        params = {
            "n_estimators": 150,
            "max_depth": 5,
            "learning_rate": 0.05,
            "scale_pos_weight": int(y.value_counts()[0] / y.value_counts()[1]) if 1 in y.values else 1,
            "objective": "binary:logistic",
            "random_state": 42
        }
        mlflow.log_params(params)

        model = xgb.XGBClassifier(**params)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        
        cm = confusion_matrix(y_test, y_pred)
        
        # Operational Metric: Εκτίμηση ανθρωποωρών που χάνονται στο SOC για triage False Alarms
        soc_triage_overhead_mins = cm[0][1] * 15 
        
        metrics = {
            "roc_auc": roc_auc_score(y_test, y_prob) if len(np.unique(y_test)) > 1 else 1.0,
            "f1_score": f1_score(y_test, y_pred),
            "false_positives": cm[0][1],
            "soc_triage_overhead_minutes": soc_triage_overhead_mins
        }
        mlflow.log_metrics(metrics)

        # Model Registry
        mlflow.xgboost.log_model(
            model, 
            "model", 
            registered_model_name="network-intrusion-model"
        )
        
        logger.info(f"✅ Training Complete. AUC: {metrics['roc_auc']:.4f} | SOC Overhead: {soc_triage_overhead_mins} mins")
        return run.info.run_id

if __name__ == "__main__":
    run_id = train_production_model()
    print(f"\n🚀 Production Pipeline Finished Successfully!")
    print(f"Model deployed to MLflow Registry. Run ID: {run_id}")