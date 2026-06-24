# 🛡️ Real-Time Cyber Threat & Network Intrusion Detection MLOps Platform

Μια ολοκληρωμένη παραγωγική πλατφόρμα ανίχνευσης κυβερνοαπειλών και εισβολών δικτύου (Network Intrusion Detection) σχεδιασμένη για περιβάλλοντα υψηλής διαθεσιμότητας και αυστηρής ασφάλειας (Mission-Critical / Defense environments). Καλύπτει πλήρως όλο τον κύκλο ζωής (End-to-End Lifecycle) ενός μοντέλου Μηχανικής Μάθησης: από το distributed ingestion και το tracking, μέχρι το production deployment, το continuous observability και το Air-Gapped Explainable AI (XAI).

---

## 🚀 Key Features

* **Distributed Big Data Layer (Spark & Parquet):** Feature engineering και ingestion pipelines αναπτυγμένα σε **PySpark**, βελτιστοποιημένα για αποθήκευση σε **Parquet format** με Snappy compression. Σχεδιασμένο για scale-out διαχείριση δισεκατομμυρίων network logs (NetFlow/PCAP telemetry) και βέλτιστο analytical query performance.
* **Mission-Ready Hybrid Inference Engine:** Ενσωματωμένος μηχανισμός ανθεκτικότητας (Graceful Degradation). Σε περίπτωση αστοχίας ή αποσύνδεσης από το MLflow registry, το API μεταπίπτει αυτόματα σε ντετερμινιστικούς κανόνες ασφαλείας (Rule-based fallback mode) για διασφάλιση 100% uptime του δικτύου.
* **Air-Gapped & Secure Explainable AI (XAI):** On-premise ενοποίηση με Local LLM (Phi-3 μέσω Ollama). Παρέχει επεξηγήσεις σε φυσική γλώσσα για κάθε "Malicious" alert, εξασφαλίζοντας **μηδενική διαρροή δεδομένων** εκτός του απομονωμένου αμυντικού δικτύου (Data Security & Sovereignty compliance).
* **Revision-Compliant CI/CD Workflows:** Πλήρως αυτοματοποιημένα pipelines μέσω GitHub Actions:
    * **CI:** Αυτοματοποιημένο linting (Flake8) και unit testing (Pytest) με προεγκατεστημένο Java environment για την επικύρωση των PySpark workloads.
    * **CD:** Docker image building και automated versioning/tagging στο Docker Hub με βάση τα Git Tags (`v*`), εξασφαλίζοντας revision-compliant provisioning.
* **Canary & Staging Traffic Splitting:** Ενσωματωμένη δυνατότητα A/B testing και σταδιακής διοχέτευσης της real-time κίνησης (Production vs Staging μοντέλο) με βάση το MD5 hashing του `source_ip_hash`.
* **Observability & SOC Metrics:** Έκθεση native metrics σε μορφή Prometheus. Περιλαμβάνει metrics για τον υπολογισμό του **SOC Triage Overhead** (εκτίμηση ανθρωποωρών που εξοικονομούνται στο Security Operations Center από τη μείωση των False Positives).

---

## 🛠️ Architecture Overview

* **Data & Storage Layer:** Distributed Ingestion μέσω PySpark. Αποθήκευση σε Columnar Parquet αρχεία για ελαχιστοποίηση του storage footprint στο Edge.
* **Model Management Layer:** MLflow Tracking & Model Registry για την παρακολούθηση πειραμάτων, αρχιτεκτονικών (XGBoost) και αυστηρό version control των μοντέλων.
* **Serving Layer:** Containerized FastAPI Web Service (Uvicorn) βελτιστοποιημένο για low-latency real-time inference.
* **Security & XAI Layer:** Local Ollama Service (Air-Gapped deployment).
* **Automation Layer:** GitHub Actions (CI/CD) & Prometheus Telemetry.

---

## 📦 Installation & Setup

### 1. Clone the Repository

git clone [https://github.com/your-username/network-intrusion-detection-mlops.git](https://github.com/your-username/network-intrusion-detection-mlops.git)
cd network-intrusion-detection-mlops

2. Build and Run the Mission Service
Η πλατφόρμα υποστηρίζει πλήρες containerized deployment. Για να σηκώσετε το API endpoint τοπικά:

# Build the revision-compliant image
sudo docker build -t network-intrusion-api -f Dockerfile .

# Run the mission-ready service
sudo docker run -d \
  --name intrusion-api-service \
  -p 8000:8000 \
  -e PYTHONPATH=/app \
  network-intrusion-api

  📡 API Usage
Health & Failover Mode Status
curl http://localhost:8000/health

Real-Time Network Log Evaluation (Inference)
curl -X POST http://localhost:8000/predict \
     -H "Content-Type: application/json" \
     -d '{
       "source_ip_hash": "a1b2c3d4e5f67890",
       "packet_size": 65535.0,
       "protocol_type_enc": 1,
       "timestamp": "2026-06-23T18:15:00"
     }'

📈 Monitoring & Mission Observability
Το API εκθέτει live τηλεμετρία στη διεύθυνση http://localhost:8000/metrics. Τα metrics είναι πλήρως συμβατά με Prometheus και έτοιμα για σύνδεση με Grafana Dashboards, επιτρέποντας στους Cyber Security Analysts να παρακολουθούν:

Το πλήθος των απειλών ανά variant (Staging vs Prod).

Το ποσοστό ενεργοποίησης του Failover Logic.

Τα στατιστικά κατανομής μεγέθους πακέτων (DDoS/Exfiltration indicators).

🛡️ Resilience & Engineering Excellence
Το project υλοποιεί την αρχή του Graceful Degradation. Σε αμυντικά συστήματα (C2/Cyber Defense), η διαθεσιμότητα είναι εξίσου κρίσιμη με την ακρίβεια. Αν το MLflow artifact store καταστεί μη διαθέσιμο (π.χ. network partition), το σύστημα ενεργοποιεί ένα εσωτερικό DummyModel βασισμένο σε heuristics και κανόνες ορίων (π.χ. Packet Size Validation για Ping of Death attacks), εξασφαλίζοντας ότι η ροή ελέγχου δεν θα διακοπεί ποτέ.

Developed by Dimitris Theodoropoulos | MLOps Engineer 🚀