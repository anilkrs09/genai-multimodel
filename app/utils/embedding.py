import requests
import psycopg2

def embed_text_with_ollama(text):
    response = requests.post(
        "http://ollama:11434/api/embeddings",
        json={"model": "mxbai-embed-large", "prompt": text}
    )
    return response.json()["embedding"]

def insert_into_pgvector(text, source_type, embedding):
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    vector_str = "[" + ",".join(map(str, embedding)) + "]"
    cur.execute(
        "INSERT INTO embeddings (content, source_type, embedding) VALUES (%s, %s, %s::vector)",
        (text, source_type, vector_str)
    )
    conn.commit()
    cur.close()
    conn.close()

def query_similar_vectors(query_embedding, limit=5):
    conn = psycopg2.connect(
        dbname="embeddings",
        user="user",
        password="password",
        host="db",
        port="5432"
    )
    cur = conn.cursor()
    vector_str = "[" + ",".join(map(str, query_embedding)) + "]"
    cur.execute(
        "SELECT id, content, source_type FROM embeddings ORDER BY embedding <-> %s::vector LIMIT %s",
        (vector_str, limit)
    )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results
