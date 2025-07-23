# app/query.py
import requests
import psycopg2
import json
from .embeddings import get_embedding  # make sure this is correct

def query_chunks_with_ollama(user_question: str):
    query_embedding = get_embedding(user_question)
    if hasattr(query_embedding, "tolist"):
        query_embedding = query_embedding.tolist()

    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()

    embedding_str = str(query_embedding)
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
    except Exception as e:
        rows = []
        print(f"[ERROR] DB error: {e}")
    finally:
        cur.close()
        conn.close()

    context_text = "\n".join(r[2] for r in rows if r[2])
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

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        try:
            result = response.json()
            answer = result.get("text", "").strip()
        except json.JSONDecodeError:
            lines = response.text.strip().split("\n")
            texts = []
            for line in lines:
                part = json.loads(line)
                if "text" in part:
                    texts.append(part["text"])
                elif "message" in part and "content" in part["message"]:
                    texts.append(part["message"]["content"])
            answer = "".join(texts).strip()
    except Exception as e:
        answer = f"[ERROR] Ollama call failed: {e}"

    return {
        "question": user_question,
        "answer": answer,
        "chunks": rows
    }

