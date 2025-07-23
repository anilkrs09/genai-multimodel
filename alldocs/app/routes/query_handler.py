import requests
import psycopg2
from ..embeddings import get_embedding

def query_chunks_with_ollama(user_question: str):
    # 1️⃣ Embed the user query
    query_embedding = get_embedding(user_question)

    # 2️⃣ Query pgvector for nearest embeddings
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT text FROM document_chunks
        ORDER BY embedding <-> %s
        LIMIT 5;
    """, (query_embedding,))
    rows = cur.fetchall()
    context_text = "\n".join(r[0] for r in rows)
    cur.close()
    conn.close()

    # 3️⃣ Send context + user query to Ollama 3 chat API
    ollama_payload = {
        "model": "llama3",
        "messages": [
            {"role": "system", "content": "You are answering based on the provided documents."},
            {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion:\n{user_question}"}
        ]
    }
    response = requests.post("http://localhost:11434/api/chat", json=ollama_payload)
    response.raise_for_status()
    return response.json()['message']['content']

