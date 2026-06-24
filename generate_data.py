import os
import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timedelta

def generate_mock_network_logs(num_rows=2000, output_path="data/raw_network_logs.csv"):
    """Παράγει mock δεδομένα δικτύου (NetFlow/PCAP telemetry) για δοκιμές."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    np.random.seed(42)
    protocols = ["TCP", "UDP", "ICMP"]
    
    data = []
    start_time = datetime.now() - timedelta(days=1)
    
    print(f"⏳ Generating {num_rows} secure network traffic logs...")
    
    for _ in range(num_rows):
        packet_id = str(uuid.uuid4())[:8]
        # Τυχαίο timestamp μέσα στο τελευταίο 24ωρο
        timestamp = (start_time + timedelta(minutes=int(np.random.randint(1, 1440)))).strftime("%Y-%m-%d %H:%M:%S")
        
        # Παραγωγή mock IP hashes (π.χ. hash_192_168_1_X)
        ip_last_octet = np.random.randint(1, 255)
        source_ip_hash = f"ip_hash_10_0_1_{ip_last_octet}"
        
        # 95% κανονική κίνηση, 5% επιθέσεις (Intrusions)
        is_intrusion = np.random.choice([0, 1], p=[0.95, 0.05])
        
        if is_intrusion:
            # Αν είναι επίθεση, προσομοιώνουμε DDoS ή Data Exfiltration (τεράστια πακέτα κοντά στο MTU limit / Ping of Death)
            packet_size = float(np.random.randint(60000, 65535))
            protocol = np.random.choice(protocols, p=[0.4, 0.2, 0.4]) # Συχνά ICMP floods
        else:
            # Κανονική κίνηση (μικρά ή μεσαία πακέτα)
            packet_size = float(np.random.randint(40, 1500))
            protocol = np.random.choice(protocols, p=[0.7, 0.2, 0.1])
            
        data.append([packet_id, timestamp, source_ip_hash, packet_size, protocol, is_intrusion])
        
    df = pd.DataFrame(data, columns=["packet_id", "timestamp", "source_ip_hash", "packet_size", "protocol_type", "is_intrusion"])
    df.to_csv(output_path, index=False)
    print(f"✅ Successfully generated mock logs at: {output_path}")

if __name__ == "__main__":
    generate_mock_network_logs()