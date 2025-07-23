from flask import Blueprint, request, render_template, jsonify
from .query_handler import query_chunks_with_ollama

bp = Blueprint('query', __name__)

@bp.route('/query', methods=['GET', 'POST'])
def query():
    if request.method == 'POST':
        user_query = request.form['query']
        answer = query_chunks_with_ollama(user_query)
        return jsonify({'response': answer})
    return render_template('query.html')

