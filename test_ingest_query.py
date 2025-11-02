from pathlib import Path
import requests
import time
import requests

URL = "http://rag_api:8000"
# WARUM FUNKTIONIERT DAS TROTZ SELF URL?????
# Load dummy documents from files
folder = Path("dummy_docs")
docs = [f.read_text() for f in folder.glob("*.txt")]

# Ingest documents


# Wait until the API is ready
for _ in range(50):  # try 20 times
    try:
        resp = requests.get(f"{URL}/docs")  # or some lightweight endpoint
        if resp.status_code == 200:
            break
    except requests.exceptions.ConnectionError:
        time.sleep(1)
else:
    raise RuntimeError("API did not start in time")

# Now ingest documents
folder = Path("dummy_docs")
docs = [f.read_text() for f in folder.glob("*.txt")]
resp = requests.post(f"{URL}/ingest", json={"documents": docs})
print("Ingest response:", resp.json())

resp = requests.post(f"{URL}/ingest", json={"documents": docs})
print("Ingest response:", resp.json())

# Query test
query_payload = {"query": "What is the capital of France?", "top_k": 2}
resp = requests.post(f"{URL}/query", json=query_payload)
print("Query response:", resp.json())