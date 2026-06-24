from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta
import logging

# Default arguments για το DAG
default_args = {
    'owner': 'mlops_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def notify_completion():
    logging.info("Feature engineering and model training pipeline completed successfully.")

with DAG(
    'intrusion_detection_main_pipeline',
    default_args=default_args,
    description='End-to-end pipeline: Feature Engineering, Store Update & Training',
    schedule_interval='@daily', # Τρέχει κάθε βράδυ
    catchup=False
) as dag:

    # TASK 1: Spark Feature Engineering
    # Αυτό καλεί το Spark script που είδαμε στην αρχή
    extract_features = SparkSubmitOperator(
        task_id='spark_feature_engineering',
        application='/home/dimitris/Desktop/intrusion-detection-mlops/features/process_features.py',
        conn_id='spark_default',
        verbose=True
    )

    # TASK 2: Update Online Feature Store (Redis)
    # Μεταφέρει τα pre-computed features από το Parquet στη Redis για το API
    update_redis = PythonOperator(
        task_id='sync_to_redis',
        python_callable=lambda: logging.info("Syncing Parquet features to Redis Store...")
        # Εδώ θα καλούσες μια συνάρτηση που διαβάζει το Parquet και κάνει redis.set()
    )

    # TASK 3: Model Retraining (MLflow)
    train_model = PythonOperator(
        task_id='retrain_intrusion_model',
        python_callable=lambda: logging.info("Running MLflow training script...")
    )

    # Ορισμός σειράς εκτέλεσης (Dependencies)
    extract_features >> update_redis >> train_model >> PythonOperator(
        task_id='pipeline_finalized',
        python_callable=notify_completion
    )