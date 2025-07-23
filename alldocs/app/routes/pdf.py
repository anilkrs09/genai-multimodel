import os
import tempfile
from flask import request, render_template, jsonify
from ..db import get_db_conn
from ..embeddings import get_embedding
from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

chunker = HybridChunker()
pdf_pipeline_options = PdfPipelineOptions(do_ocr=False, do_table_structure=False)
doc_converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_pipeline_options)}
)

def index():
    return "Upload endpoints: /upload/pdf, /upload/image, /upload/csv, /upload/text"

def upload_pdf():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        original_filename = uploaded_file.filename
        title = request.form.get('title', 'Unknown Title')

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            uploaded_file.save(temp_file)
            temp_file_path = temp_file.name
        
        try:
            dl_doc = doc_converter.convert(temp_file_path).document
        finally:
            os.remove(temp_file_path)

        conn = get_db_conn()
        cur = conn.cursor()
        for chunk in chunker.chunk(dl_doc=dl_doc):
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

    return render_template('upload_pdf.html')

