from app import app
from app.ui import ui_bp
from flask import Flask, render_template, json, request

@ui_bp.route('/')
def index():
    return render_template('index.html')

