import csv
from io import StringIO
from flask import request, render_template, jsonify
from ..db import get_db_conn
from ..embeddings import get_embedding

def upload_csv():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        original_filename = uploaded_file.filename
        title = request.form.get('title', 'Unknown Title')

        csv_data = uploaded_file.read().decode('utf-8')
        reader = csv.reader(StringIO(csv_data))

        conn = get_db_conn()
        cur = conn.cursor()
        for row in reader:
            text = ', '.join(row)
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

        return jsonify({"status": f"{original_filename} CSV uploaded and embedded."})
    return render_template('upload_csv.html')

