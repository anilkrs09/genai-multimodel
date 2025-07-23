import os
import tempfile
import psycopg2
import requests
from flask import Flask, request, jsonify, render_template_string
from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from werkzeug.utils import secure_filename
from utils.embedding import embed_text_with_ollama, insert_into_pgvector, query_similar_vectors
app = Flask(__name__)

# Initialize docling objects once
pdf_pipeline_options = PdfPipelineOptions(do_ocr=False, do_table_structure=False)
doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pdf_pipeline_options
        )
    }
)
chunker = HybridChunker()

# PostgreSQL connection settings — update as needed
conn = psycopg2.connect(
    host="localhost",
    database="postgres",
    user="postgres",
    password="postgres"
)
conn.autocommit = True

def get_embedding(text: str):
    """Call Ollama embedding API to get vector embedding for text."""
    url = "http://localhost:11434/api/embeddings"
    payload = {"model": "nomic-embed-text", "prompt": text}
    response = requests.post(url, json=payload)
    response.raise_for_status()
    embedding = response.json()['embedding']
    return embedding

HTML_FORM = """
<!doctype html>
<title>Upload PDF</title>
<h1>Upload a PDF for Chunking</h1>
<form method=post enctype=multipart/form-data action="/upload">
  <input type=file name=file>
  <input type=text name=title placeholder="Document Title">
  <input type=submit value=Upload>
</form>
"""

@app.route('/')
def index():
    return render_template_string(HTML_FORM)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    title = request.form.get('title', 'Unknown Title')

    if not uploaded_file or not uploaded_file.filename.endswith('.pdf'):
        return "Please upload a valid PDF file.", 400

    # Save uploaded PDF with original filename
    filename = secure_filename(uploaded_file.filename)
    saved_path = os.path.join(UPLOAD_DIR, filename)
    uploaded_file.save(saved_path)

    try:
        dl_doc = doc_converter.convert(saved_path).document
    finally:
        os.remove(saved_path)  # Clean up after parsing

    data = []
    chunk_id = 0
    cur = conn.cursor()
    for chunk in chunker.chunk(dl_doc=dl_doc):
        chunk_dict = chunk.model_dump()
        filename = chunk_dict['meta']['origin']['filename']
        heading = chunk_dict['meta']['headings'][0] if chunk_dict['meta']['headings'] else None
        page_num = chunk_dict['meta']['doc_items'][0]['prov'][0]['page_no']
        text = chunk.text

        # Get embedding vector from Ollama
        embedding = get_embedding(text)

        # Insert into PostgreSQL (embedding stored as vector)
        cur.execute(
            """
            INSERT INTO document_chunks (title, filename, heading, page_num, text, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (title, filename, heading, page_num, text, embedding)
        )

        data.append({
            "id": chunk_id,
            "text": text,
            "title": title,
            "filename": filename,
            "heading": heading,
            "page_num": page_num
        })
        chunk_id += 1

    cur.close()
    return jsonify(data)

@app.route('/chat', methods=['POST'])
def chat():
    user_query = request.json['query']
    query_embedding = embed_text_with_ollama(user_query)
    top_chunks = query_similar_vectors(query_embedding, limit=5)

    context = "\n\n".join(row[1] for row in top_chunks)

    prompt = f"You are a helpful AI assistant. You have access to the following information from previous files:\n\n{context}\n\nAnswer the user's question based on this information:\n\n{user_query}"

    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "llama3",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )
    return jsonify({"response": response.json()["message"]["content"]})


if __name__ == '__main__':
    app.run(debug=True)

