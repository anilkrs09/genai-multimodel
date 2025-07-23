import requests
import psycopg2
import json
from ..embeddings import get_embedding

def query_chunks_with_ollama(user_question: str):
    # 1️⃣ Embed the user query and ensure it's a list of floats
    query_embedding = get_embedding(user_question)
    if hasattr(query_embedding, "tolist"):
        query_embedding = query_embedding.tolist()
    print(f"[DEBUG] Query embedding (len={len(query_embedding)}): {query_embedding}")

    # 2️⃣ Connect to Postgres and query pgvector for nearest embeddings
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()

    # Convert embedding list to string for pgvector input
    embedding_str = str(query_embedding)
    print(f"[DEBUG] Passing embedding to SQL as string: {embedding_str}")

    try:
        cur.execute(
            """
            SELECT title, filename, text, embedding <-> %s::vector AS distance
            FROM document_chunks
            ORDER BY distance ASC
            LIMIT 3
            """,
            (embedding_str,)
        )
        rows = cur.fetchall()
        print(f"[DEBUG] Retrieved {len(rows)} rows from DB")
        for i, row in enumerate(rows):
            print(f"[DEBUG] Row {i}: title={row[0]}, filename={row[1]}, distance={row[3]}")
    except Exception as e:
        print(f"[ERROR] Failed to execute SQL query: {e}")
        rows = []

    cur.close()
    conn.close()

    # 3️⃣ Build context from actual chunk text (index 2)
    context_text = "\n".join(r[2] for r in rows if r[2])
    print(f"[DEBUG] Context text sent to Ollama:\n{context_text}")

    # 4️⃣ Prepare Ollama API payload
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "llama3.2",
        "temperature": 0.3,
        "max_tokens": 512,
        "stream": False,
        "messages": [
            {"role": "system", "content": "You are answering based on the provided documents."},
            {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion:\n{user_question}"}
        ]
    }

    # 5️⃣ Call Ollama API and handle response
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        try:
            result = response.json()
            print(f"[DEBUG] Ollama API response JSON: {result}")
            return result.get("text", "").strip()
        except json.JSONDecodeError:
            # Handle NDJSON (if any)
            lines = response.text.strip().split("\n")
            texts = []
            for line in lines:
                if line.strip():
                    part = json.loads(line)
                    if "text" in part:
                        texts.append(part["text"])
                    elif "message" in part and "content" in part["message"]:
                        texts.append(part["message"]["content"])
            final_text = "".join(texts).strip()
            print(f"[DEBUG] Ollama NDJSON parsed text: {final_text}")
            return final_text
    except requests.RequestException as e:
        print(f"[ERROR] Ollama API request failed: {e}")
        return ""


