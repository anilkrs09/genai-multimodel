import os
import tempfile
from flask import Flask, request, jsonify, render_template_string
from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

app = Flask(__name__)

# Initialize once
pdf_pipeline_options = PdfPipelineOptions(do_ocr=False, do_table_structure=False)
doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pdf_pipeline_options
        )
    }
)
chunker = HybridChunker()


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


@app.route('/upload', methods=['POST'])
def upload_file():
    uploaded_file = request.files['file']
    title = request.form.get('title', 'Unknown Title')

    if not uploaded_file or not uploaded_file.filename.endswith('.pdf'):
        return "Please upload a valid PDF file.", 400

    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        uploaded_file.save(temp_file)
        temp_file_path = temp_file.name

    try:
        dl_doc = doc_converter.convert(temp_file_path).document
    finally:
        os.remove(temp_file_path)  # Clean up temp file

    data = []
    chunk_id = 0
    for chunk in chunker.chunk(dl_doc=dl_doc):
        chunk_dict = chunk.model_dump()
        filename = chunk_dict['meta']['origin']['filename']
        heading = chunk_dict['meta']['headings'][0] if chunk_dict['meta']['headings'] else None
        page_num = chunk_dict['meta']['doc_items'][0]['prov'][0]['page_no']
        data.append({
            "id": chunk_id,
            "text": chunk.text,
            "title": title,
            "filename": filename,
            "heading": heading,
            "page_num": page_num
        })
        chunk_id += 1

    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)

