from app import app
from app.ui import bp
from flask import render_template

@bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')

