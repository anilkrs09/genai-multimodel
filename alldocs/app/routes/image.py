from flask import request, render_template, jsonify
from ..db import get_db_conn
from ..embeddings import get_embedding

def upload_image():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        original_filename = uploaded_file.filename
        title = request.form.get('title', 'Unknown Title')

        text = f"Image placeholder content for {original_filename}"  # Normally OCR would extract text
        embedding = get_embedding(text)

        conn = get_db_conn()
        cur = conn.cursor()
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

        return jsonify({"status": f"{original_filename} image uploaded and embedded."})
    return render_template('upload_image.html')

