import os
from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename

from .db import conn
from .embeddings import get_embedding
from .chunking import chunker, doc_converter

main = Blueprint('main', __name__)
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@main.route('/')
def index():
    return render_template('upload.html')

@main.route('/upload', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    title = request.form.get('title', 'Unknown Title')

    if not uploaded_file or not uploaded_file.filename.endswith('.pdf'):
        return "Please upload a valid PDF file.", 400

    filename = secure_filename(uploaded_file.filename)
    saved_path = os.path.join(UPLOAD_FOLDER, filename)
    uploaded_file.save(saved_path)

    try:
        dl_doc = doc_converter.convert(saved_path).document
    finally:
        os.remove(saved_path)

    data = []
    chunk_id = 0
    cur = conn.cursor()
    for chunk in chunker.chunk(dl_doc=dl_doc):
        chunk_dict = chunk.model_dump()
        heading = chunk_dict['meta']['headings'][0] if chunk_dict['meta']['headings'] else None
        page_num = chunk_dict['meta']['doc_items'][0]['prov'][0]['page_no']
        text = chunk.text
        embedding = get_embedding(text)

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

