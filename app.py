import base64
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import threading
import webview
import os
import sys
from modules.API import API
from modules.helpers import get_db_connection
import sqlite3
import re

# SETUP FLASK
app = Flask(__name__)
app.secret_key = '0g4Ty9YfjicKKQgRexLMJMroCSZ0CTni'

api = API() # pywebview api object

# html_file = os.path.abspath("static/upload.html")

# webview.create_window("My App", html_file, js_api=api)
# webview.start(debug=True)

@app.route('/')
def index():
    return redirect(url_for('upload'))
    
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
    
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        filename = secure_filename(file.filename)  # Secure the filename
        save_path = os.path.join('uploads', filename)
        file.save(save_path)

        # Process file
        results = api.process_file(save_path)
        if results:
            session['failed_rows'] = results['failed_rows']
            session['filename'] = results['filename']
            return redirect(url_for('fix_errors'))

        flash('File uploaded successfully', 'success')
        return redirect(url_for('upload'))
    
    return jsonify({"error": "Invalid request"})
 
@app.route('/fix_errors', methods=['GET', 'POST'])
def fix_errors():
    if request.method == 'GET':
        if 'failed_rows' not in session:
            return redirect(url_for('upload'))
        
        failed_rows = session.get('failed_rows', [])
        filename = session.get('filename', '')
    
        return render_template('fix_errors.html', failed_rows=failed_rows, filename=filename)

    elif request.method == 'POST':
        # Get the corrections data from the form
        corrections_json = request.form.get('corrections')
        corrections = json.loads(corrections_json)
        
        return corrections_json


def start_server():
    app.run(host='0.0.0.0', port=80)

if __name__ == '__main__':

    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()

    webview.create_window("PyWebView & Flask", "http://localhost/")
    webview.start(debug=True) # debug=True
    sys.exit()