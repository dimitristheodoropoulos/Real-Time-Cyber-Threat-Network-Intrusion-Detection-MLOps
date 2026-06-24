import requests

def explain_prediction(amount, hour, is_intrusion):
    status = "flagged as FRAUD" if is_intrusion == 1 else "cleared as NORMAL"
    
    prompt = f"""
    You are a intrusion expert. A transaction of {amount}€ at {hour}:00 was {status}.
    Explain in one short sentence why this might be suspicious or safe.
    Example: 'High amount during late night hours is a classic intrusion pattern.'
    """
    
    try:
        response = requests.post("http://localhost:11434/api/generate", 
            json={
                "model": "tinyllama",
                "prompt": prompt,
                "stream": False
            })
        return response.json()['response'].strip()
    except Exception:
        return "LLM Agent offline. Rule-based explanation: Unusual hour/amount combination."

# Δοκιμή
if __name__ == "__main__":
    print(f"🤖 Agent: {explain_prediction(5000, 3, 1)}")