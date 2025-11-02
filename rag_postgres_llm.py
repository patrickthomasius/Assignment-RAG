# rag_postgres_llm.py
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from sentence_transformers import SentenceTransformer

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import numpy as np
import faiss
import psycopg
from psycopg import sql


#import psycopg2
#from psycopg2.extras import execute_values
# TODO check SKLEARN for pipelines ... 


import uvicorn
from dotenv import load_dotenv

load_dotenv()
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "start"
POSTGRES_HOST = "postgres"
POSTGRES_PORT = 5432
POSTGRES_DB = "postgres"
# -----------------------------
# 1. Database connection
# -----------------------------
DB_PARAMS = {
    "dbname": os.getenv("PG_DB", "rag_db"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASSWORD", ""),
    "host": os.getenv("PG_HOST", "localhost"),
    "port": os.getenv("PG_PORT", 5432)
}
print("Connecting to:", os.getenv("POSTGRES_HOST"))

conn = psycopg.connect(
    dbname=os.getenv("POSTGRES_DB", "postgres"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "start"),
    host=os.getenv("POSTGRES_HOST", "postgres"),  #
    port="5432",
)



#########
DB_NAME = "vectors"
cur = conn.cursor()
# Check if database exists
cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
exists = cur.fetchone()

if not exists:
    print(f"Database '{DB_NAME}' not found — creating it...")
    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DB_NAME)))
else:
    print(f"Database '{DB_NAME}' already exists — skipping creation.")

#cur.close()
#conn.close()



cursor = conn.cursor()

# -----------------------------
# 2. Create tables if missing
# -----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL
);
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS embeddings (
    doc_id INT PRIMARY KEY REFERENCES documents(id) ON DELETE CASCADE,
    vector FLOAT8[]
);
""")
conn.commit()

# -----------------------------
# 3. Embedding model
# -----------------------------
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
EMBED_DIM = 384
embed_model = SentenceTransformer(EMBED_MODEL_NAME)

# -----------------------------
# 4. FAISS index
# -----------------------------
faiss_index = faiss.IndexFlatL2(EMBED_DIM)
id_map = []

# Load existing embeddings
cursor.execute("SELECT doc_id, vector FROM embeddings")
rows = cursor.fetchall()
if rows:
    vectors = np.array([r[1] for r in rows]).astype("float32")
    faiss_index.add(vectors)
    id_map = [r[0] for r in rows]

# -----------------------------
# 5. LLM model (Flan-T5 small)
# -----------------------------

#TODO switch with API 
LLM_MODEL_NAME = "google/flan-t5-small"
tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)
llm_model = AutoModelForSeq2SeqLM.from_pretrained(LLM_MODEL_NAME)

def generate_answer(query: str, context: str, max_length=200):
    prompt = f"Answer the question based on the context below:\n\nContext:\n{context}\n\nQuestion: {query}"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = llm_model.generate(**inputs, max_length=max_length)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# -----------------------------
# 6. FastAPI app
# -----------------------------
app = FastAPI(title="RAG with LLM API")

class IngestRequest(BaseModel):
    documents: list[str]

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

# -----------------------------
# 7. Helper functions
# -----------------------------
def embed_texts(texts):
    return embed_model.encode(texts, convert_to_numpy=True).astype("float32")


def add_docs_to_db_and_index(texts):
    # Insert documents and get their IDs
    doc_ids = []
    with conn.cursor() as cur:
        for text in texts:
            cur.execute(
                "INSERT INTO documents (text) VALUES (%s) RETURNING id",
                (text,)
            )
            doc_ids.append(cur.fetchone()[0])

        # Generate embeddings
        embeddings = embed_texts(texts)

        # Insert embeddings
        cur.executemany(
            "INSERT INTO embeddings (doc_id, vector) VALUES (%s, %s)",
            [(doc_id, emb.tolist()) for doc_id, emb in zip(doc_ids, embeddings)]
        )

    # Commit after all operations
    conn.commit()

    # Add to FAISS index
    faiss_index.add(embeddings)
    id_map.extend(doc_ids)

    return len(doc_ids)

def add_docs_to_db_and_index_deprecated(texts):
    # Insert documents
    execute_values(cursor,
        "INSERT INTO documents (text) VALUES %s RETURNING id",
        [(t,) for t in texts]
    )
    doc_ids = [r[0] for r in cursor.fetchall()]
    conn.commit()
    
    # Generate embeddings
    embeddings = embed_texts(texts)
    
    # Insert embeddings
    execute_values(cursor,
        "INSERT INTO embeddings (doc_id, vector) VALUES %s",
        [(doc_id, emb.tolist()) for doc_id, emb in zip(doc_ids, embeddings)]
    )
    conn.commit()
    
    # Add to FAISS
    faiss_index.add(embeddings)
    id_map.extend(doc_ids)
    
    return len(doc_ids)

def get_relevant_docs(query, top_k=3):
    if not id_map:
        return []
    
    q_vec = embed_texts([query])
    distances, indices = faiss_index.search(q_vec, top_k)
    docs = []
    for idx in indices[0]:
        if idx < len(id_map):
            doc_id = id_map[idx]
            cursor.execute("SELECT text FROM documents WHERE id=%s", (doc_id,))
            row = cursor.fetchone()
            if row:
                docs.append(row[0])
    return docs

# -----------------------------
# 8. API endpoints
# -----------------------------
@app.post("/ingest")
def ingest(req: IngestRequest):
    if not req.documents:
        raise HTTPException(status_code=400, detail="No documents provided")
    n = add_docs_to_db_and_index(req.documents)
    return {"message": f"Ingested {n} documents into Postgres and FAISS!"}

@app.post("/query")
def query(req: QueryRequest):
    docs = get_relevant_docs(req.query, top_k=req.top_k)
    if not docs:
        return {"answer": "No documents ingested yet!"}
    
    context = "\n".join(docs)
    answer = generate_answer(req.query, context)
    
    return {"query": req.query, "retrieved_docs": docs, "answer": answer}

# -----------------------------
# 9. Run
# -----------------------------
if __name__ == "__main__":
    uvicorn.run("rag_postgres_llm:app", host="0.0.0.0", port=8000, reload=True)
