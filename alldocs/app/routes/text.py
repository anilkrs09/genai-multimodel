import os
import tempfile
from flask import request, render_template, jsonify
from ..db import get_db_conn
from ..embeddings import get_embedding
from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from textwrap import wrap

chunker = HybridChunker()
pdf_pipeline_options = PdfPipelineOptions(do_ocr=False, do_table_structure=False)
doc_converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_pipeline_options)}
)


MAX_TOKENS = 512  # depending on your model

def extract_text_from_docling(dl_doc):
    texts = []
    for section in dl_doc.sections:
        for paragraph in section.paragraphs:
            texts.append(paragraph.text)
    return "\n\n".join(texts)

def chunk_text(text, max_tokens=MAX_TOKENS):
    # very naive; better to use a tokenizer for precise token-based splitting
    return wrap(text, width=1000)  # ~1000 chars is often < 512 tokens

def upload_text():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        original_filename = uploaded_file.filename
        title = request.form.get('title', 'Unknown Title')

        with tempfile.NamedTemporaryFile(delete=False, suffix=".text") as temp_file:
            uploaded_file.save(temp_file)
            temp_file_path = temp_file.name

        try:
            dl_doc = doc_converter.convert(temp_file_path).document
        finally:
            os.remove(temp_file_path)

        conn = get_db_conn()
        cur = conn.cursor()
       
        text = extract_text_from_docling(dl_doc)
        chunks = chunk_text(text)

        for chunk in chunks:
            text = chunk.text
            embedding = get_embedding(text)
            cur.execute(
                """
                INSERT INTO document_chunks (title, filename, heading, page_num, text, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (title, original_filename, None, 1, text, embedding)
            )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": f"{original_filename} uploaded and embedded."})

    return render_template('upload_text.html')
