from pathlib import Path
import requests

URL = "http://127.0.0.1:8000"

# Load dummy documents from files
folder = Path("dummy_docs")
docs = [f.read_text() for f in folder.glob("*.txt")]

# Ingest documents
resp = requests.post(f"{URL}/ingest", json={"documents": docs})
print("Ingest response:", resp.json())

# Query test
query_payload = {"query": "What is the capital of France?", "top_k": 2}
resp = requests.post(f"{URL}/query", json=query_payload)
print("Query response:", resp.json())