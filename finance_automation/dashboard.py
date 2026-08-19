import streamlit as st
import requests
import pandas as pd
import json

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Finance Automation Dashboard", layout="wide")
st.title("💼 Finance Automation Dashboard")

menu = st.sidebar.selectbox(
    "Επιλέξτε λειτουργία",
    ["Pending Approvals", "Reconciliation Upload", "Intercompany Matching", "Health"]
)

if menu == "Health":
    st.subheader("Service Health")
    try:
        resp = requests.get(f"{API_URL}/health")
        st.json(resp.json())
    except Exception as e:
        st.error(f"API not reachable: {e}")

elif menu == "Pending Approvals":
    st.subheader("Εκκρεμείς Εγκρίσεις")
    try:
        resp = requests.get(f"{API_URL}/approvals/pending")
        if resp.status_code == 200:
            pending = resp.json()
            if not pending:
                st.info("Δεν υπάρχουν εκκρεμείς εγγραφές.")
            else:
                df = pd.DataFrame(pending)
                st.dataframe(df)

                # Ενέργειες έγκρισης/απόρριψης
                for _, row in df.iterrows():
                    col1, col2, col3 = st.columns([3,1,1])
                    col1.write(f"**{row['id']}** – {row['description']} ({row['amount']})")
                    if col2.button(f"✅ Approve {row['id']}"):
                        apr_resp = requests.post(
                            f"{API_URL}/approvals/{row['id']}/approve",
                            params={"reviewer": "streamlit_user", "comments": "Approved via dashboard"}
                        )
                        if apr_resp.status_code == 200:
                            st.success(f"Approved {row['id']}")
                            st.rerun()
                    if col3.button(f"❌ Reject {row['id']}"):
                        rej_resp = requests.post(
                            f"{API_URL}/approvals/{row['id']}/reject",
                            params={"reviewer": "streamlit_user", "comments": "Rejected via dashboard"}
                        )
                        if rej_resp.status_code == 200:
                            st.warning(f"Rejected {row['id']}")
                            st.rerun()
        else:
            st.error("Failed to fetch pending approvals.")
    except Exception as e:
        st.error(f"Error: {e}")

elif menu == "Reconciliation Upload":
    st.subheader("Bank vs GL Reconciliation")
    col1, col2 = st.columns(2)
    with col1:
        bank_file = st.file_uploader("Bank CSV", type=['csv'])
    with col2:
        gl_file = st.file_uploader("GL CSV", type=['csv'])

    amount_tol = st.number_input("Amount tolerance", value=0.01, format="%.2f")
    date_tol = st.number_input("Date tolerance (days)", value=3, min_value=0)

    if st.button("Run Reconciliation") and bank_file and gl_file:
        files = {
            "bank_file": (bank_file.name, bank_file, "text/csv"),
            "gl_file": (gl_file.name, gl_file, "text/csv")
        }
        data = {"amount_tolerance": amount_tol, "date_tolerance_days": date_tol}
        try:
            resp = requests.post(f"{API_URL}/reconcile/upload", files=files, data=data)
            if resp.status_code == 200:
                result = resp.json()
                st.subheader("Matched")
                st.dataframe(pd.DataFrame(result['matched']))
                st.subheader("Unmatched Bank")
                st.dataframe(pd.DataFrame(result['unmatched_bank']))
                st.subheader("Unmatched GL")
                st.dataframe(pd.DataFrame(result['unmatched_gl']))
                st.subheader("Suggested Matches")
                st.dataframe(pd.DataFrame(result['suggested_matches']))
            else:
                st.error(f"Error: {resp.text}")
        except Exception as e:
            st.error(f"Error: {e}")

elif menu == "Intercompany Matching":
    st.subheader("Intercompany Matching")
    st.info("Πληκτρολογήστε JSON με transactions_A και transactions_B.")
    json_input = st.text_area("JSON Input", height=250, value='''{
  "transactions_A": [],
  "transactions_B": [],
  "amount_tolerance": 0.01,
  "date_tolerance_days": 5
}''')

    if st.button("Run Intercompany Match"):
        try:
            payload = json.loads(json_input)
            resp = requests.post(f"{API_URL}/intercompany/match", json=payload)
            if resp.status_code == 200:
                result = resp.json()
                st.subheader("Matched")
                st.json(result.get('matched', []))
                st.subheader("Mismatched")
                st.json(result.get('mismatched', []))
                st.subheader("Unmatched A")
                st.json(result.get('unmatched_A', []))
                st.subheader("Unmatched B")
                st.json(result.get('unmatched_B', []))
                st.subheader("Suggested Matches")
                st.json(result.get('suggested_matches', []))
            else:
                st.error(f"Error: {resp.text}")
        except Exception as e:
            st.error(f"Error: {e}")