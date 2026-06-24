import logging
import os
from pyspark.sql import SparkSession
from pyspark.sql.types import DoubleType, IntegerType
from pyspark.sql import functions as F

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_spark_session():
    """Δημιουργεί ένα τοπικό Spark Session με απενεργοποιημένο το ANSI mode για ασφαλές parsing ημερομηνιών."""
    return SparkSession.builder \
        .appName("NetworkIntrusionIngestion") \
        .master("local[*]") \
        .config("spark.sql.parquet.compression.codec", "snappy") \
        .config("spark.sql.ansi.enabled", "false") \
        .getOrCreate()

def ingest_data(input_path, output_path):
    spark = create_spark_session()
    logger.info(f"🚀 Έναρξη Ingestion από: {input_path}")

    try:
        if not os.path.exists(input_path):
            logger.error(f"❌ Το αρχείο {input_path} δεν βρέθηκε!")
            return

        # 1. Διαβάζουμε το CSV ως String
        df_raw = spark.read.csv(input_path, header=True)
        
        raw_count = df_raw.count()
        logger.info(f"📊 Συνολικές γραμμές στο αρχικό CSV: {raw_count}")

        # 2. Ασφαλής μετατροπή τύπων (Casting & Parsing)
        # Φέρνουμε πρώτο το format με το κενό (yyyy-MM-dd HH:mm:ss) που χρησιμοποιούν τα logs σου
        df_casted = df_raw \
            .withColumn("timestamp_parsed", F.coalesce(
                F.to_timestamp(F.col("timestamp"), "yyyy-MM-dd HH:mm:ss"),
                F.to_timestamp(F.col("timestamp"), "yyyy-MM-dd'T'HH:mm:ss"),
                F.to_timestamp(F.col("timestamp"))  # Fallback
            )) \
            .withColumn("packet_size_parsed", F.col("packet_size").cast(DoubleType())) \
            .withColumn("is_intrusion_parsed", F.col("is_intrusion").cast(IntegerType()))

        # 3. Επιλογή και μετονομασία στηλών
        df_mapped = df_casted.select(
            F.col("packet_id"),
            F.col("timestamp_parsed").alias("timestamp"),
            F.col("source_ip_hash"),
            F.col("packet_size_parsed").alias("packet_size"),
            F.col("protocol_type"),
            F.col("is_intrusion_parsed").alias("is_intrusion")
        )

        # Διαγνωστικός έλεγχος για nulls πριν το dropna
        null_ts = df_mapped.filter(F.col("timestamp").isNull()).count()
        null_ps = df_mapped.filter(F.col("packet_size").isNull()).count()
        null_ins = df_mapped.filter(F.col("is_intrusion").isNull()).count()
        
        if null_ts > 0 or null_ps > 0 or null_ins > 0:
            logger.warning(f"⚠️ Προειδοποίηση Parsing: Βρέθηκαν null τιμές (Timestamps: {null_ts}, Packet Sizes: {null_ps}, Intrusions: {null_ins})")

        # 4. Καθαρισμός
        df_clean = df_mapped.dropna(subset=["timestamp", "packet_size", "is_intrusion"])
        
        final_count = df_clean.count()
        logger.info(f"📉 Γραμμές μετά το dropna: {final_count}")

        if final_count == 0:
            logger.error("❌ Όλες οι γραμμές απορρίφθηκαν! Ελέγξτε τα raw δεδομένα στο CSV.")
            return

        # 5. Feature Engineering (Hour & Day of Week)
        df_final = df_clean.withColumn("hour", F.hour("timestamp")) \
                           .withColumn("day_of_week", F.dayofweek("timestamp"))

        # 6. Αποθήκευση σε Parquet
        df_final.write.mode("overwrite").parquet(output_path)
        logger.info(f"✅ Επιτυχής αποθήκευση στο Parquet ({final_count} γραμμές): {output_path}")

    except Exception as e:
        logger.error(f"❌ Σφάλμα κατά το ingestion: {str(e)}")
    finally:
        spark.stop()

if __name__ == "__main__":
    RAW_DATA = "data/raw_network_logs.csv"
    PROCESSED_DATA = "data/processed_network_logs.parquet"
    
    ingest_data(RAW_DATA, PROCESSED_DATA)