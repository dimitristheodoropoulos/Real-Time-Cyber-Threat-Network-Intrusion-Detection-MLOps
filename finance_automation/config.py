import os

# Database paths
APPROVALS_DB_PATH = os.getenv("APPROVALS_DB_PATH", "approvals.db")
WEBHOOKS_DB_PATH = os.getenv("WEBHOOKS_DB_PATH", "webhooks.db")

# LLM settings (Ollama)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# API base URL (used by dashboard)
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")