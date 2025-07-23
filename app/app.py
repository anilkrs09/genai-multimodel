from flask import Flask, request, jsonify, send_from_directory
from utils.doc import pdf_pipeline_options 
from utils.image_caption import image_to_caption
from utils.embedding import embed_text_with_ollama, insert_into_pgvector, query_similar_vectors
import requests
import os

app = Flask(__name__, static_folder='static')

@app.route('/')
def serve_ui():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/upload-text', methods=['POST'])
def upload_text():
    text = request.json['text']
    embedding = embed_text_with_ollama(text)
    insert_into_pgvector(text, 'text', embedding)
    return {'status': 'inserted'}

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    file = request.files['file']
    path = '/tmp/' + file.filename
    file.save(path)
    doc_converter.convert(path).document
    #chunks = extract_text_chunks_from_pdf(path)
    for chunk in chunks:
        embedding = embed_text_with_ollama(chunk)
        insert_into_pgvector(chunk, 'pdf', embedding)
    os.remove(path)
    return {'status': 'inserted'}

@app.route('/upload-txt', methods=['POST'])
def upload_txt():
    file = request.files['file']
    path = '/tmp/' + file.filename
    file.save(path)
    chunks = extract_text_chunks_from_txt(path)
    for chunk in chunks:
        embedding = embed_text_with_ollama(chunk)
        insert_into_pgvector(chunk, 'txt', embedding)
    os.remove(path)
    return {'status': 'inserted'}

@app.route('/upload-image', methods=['POST'])
def upload_image():
    file = request.files['file']
    path = '/tmp/' + file.filename
    file.save(path)
    caption = image_to_caption(path)
    embedding = embed_text_with_ollama(caption)
    insert_into_pgvector(caption, 'image', embedding)
    os.remove(path)
    return {'status': 'inserted', 'caption': caption}

@app.route('/query', methods=['POST'])
def query():
    user_query = request.json['text']
    query_embedding = embed_text_with_ollama(user_query)
    top_chunks = query_similar_vectors(query_embedding, limit=5)

    results = [{'id': row[0], 'content': row[1], 'source_type': row[2]} for row in top_chunks]
    return jsonify(results)

@app.route('/chat', methods=['POST'])
def chat():
    user_query = request.json['query']
    query_embedding = embed_text_with_ollama(user_query)
    top_chunks = query_similar_vectors(query_embedding, limit=5)

    context = "\n\n".join(row[1] for row in top_chunks)

    prompt = f"You are a helpful AI assistant. You have access to the following information from previous files:\n\n{context}\n\nAnswer the user's question based on this information:\n\n{user_query}"

    response = requests.post(
        "http://ollama:11434/api/chat",
        json={
            "model": "llama3",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )
    return jsonify({"response": response.json()["message"]["content"]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
