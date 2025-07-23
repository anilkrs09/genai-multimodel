from docling.chunking import HybridChunker
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption


def process_pdfs(pdf_files: list):
    pdf_pipeline_options = PdfPipelineOptions(do_ocr=False, do_table_structure=False)
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pdf_pipeline_options
            )
        }
    )
    chunker = HybridChunker()

    data = []
    chunk_id = 0

    for pdf in pdf_files:
        print("Downloading and parsing:", pdf['title'])
        doc = doc_converter.convert(pdf['file']).document
        for chunk in chunker.chunk(dl_doc=doc):
            chunk_dict = chunk.model_dump()
            filename = chunk_dict['meta']['origin']['filename']
            heading = chunk_dict['meta']['headings'][0] if chunk_dict['meta']['headings'] else None
            page_num = chunk_dict['meta']['doc_items'][0]['prov'][0]['page_no']
            data.append({
                "id": chunk_id,
                "text": chunk.text,
                "title": pdf['title'],
                "filename": filename,
                "heading": heading,
                "page_num": page_num
            })
            chunk_id += 1

    return data


def main():
    pdf_files = [
        {'title': "Attention Is All You Need", 'file': "https://arxiv.org/pdf/1706.03762"},
        {'title': "Deep Residual Learning", 'file': "https://arxiv.org/pdf/1512.03385"},
        {'title': "BERT", 'file': "https://arxiv.org/pdf/1810.04805"},
        {'title': "GPT-3", 'file': "https://arxiv.org/pdf/2005.14165"},
        {'title': "Adam Optimizer", 'file': "https://arxiv.org/pdf/1412.6980"},
        {'title': "GANs", 'file': "https://arxiv.org/pdf/1406.2661"},
        {'title': "U-Net", 'file': "https://arxiv.org/pdf/1505.04597"},
        {'title': "DALL-E 2", 'file': "https://arxiv.org/pdf/2204.06125"},
        {'title': "Stable Diffusion", 'file': "https://arxiv.org/pdf/2112.10752"}
    ]

    data = process_pdfs(pdf_files)

    for item in data:
        print(item)


if __name__ == "__main__":
    main()

