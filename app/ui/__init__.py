from flask import Blueprint

ui_bp = Blueprint('home', __name__)

from app.ui import routes
