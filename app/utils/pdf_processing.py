from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from pathlib import Path
from io import BufferedReader

def extract_text_chunks_from_pdf(file_path):
    pdf_pipeline_options = PdfPipelineOptions(do_ocr=False, do_table_structure=False)
    doc_converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_pipeline_options)}
    )
    chunker = HybridChunker()

    conversion_result = doc_converter.convert(Path(file_path), InputFormat.PDF)

    docling_document = conversion_result.document
    chunks = chunker.chunk(docling_document)
    return [chunk.text for chunk in chunks]


