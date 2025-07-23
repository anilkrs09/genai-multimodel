# test_pdf_processing.py

import docling
print(dir(docling))

from utils.pdf_processing import extract_text_chunks_from_pdf


pdf_path = "sample.pdf"  # Replace with actual path to a PDF
txt_path = "sample.txt"  # Replace with actual path to a TXT file

print("== PDF Output ==")
pdf_chunks = extract_text_chunks_from_pdf(pdf_path)
for i, chunk in enumerate(pdf_chunks):
    print(f"[{i}] {chunk[:100]}...")  # Print first 100 chars of each chunk


