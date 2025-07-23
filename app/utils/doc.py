from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

pdf_pipeline_options = PdfPipelineOptions(do_ocr=False, do_table_structure=False)
doc_converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(
        pipeline_options=pdf_pipeline_options
    )}
)
chunker = HybridChunker()
