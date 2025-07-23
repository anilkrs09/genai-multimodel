from flask import Blueprint
from . import pdf, image, csv, text
from app.query import bp as query_bp

bp = Blueprint('routes', __name__)
bp.add_url_rule('/upload/pdf', view_func=pdf.upload_pdf, methods=['GET', 'POST'])
bp.add_url_rule('/upload/image', view_func=image.upload_image, methods=['GET', 'POST'])
bp.add_url_rule('/upload/csv', view_func=csv.upload_csv, methods=['GET', 'POST'])
bp.add_url_rule('/upload/text', view_func=text.upload_text, methods=['GET', 'POST'])
bp.register_blueprint(query_bp)
bp.add_url_rule('/', view_func=pdf.index)

