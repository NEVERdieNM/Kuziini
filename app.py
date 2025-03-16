import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import threading
import webview
import os
import sys
from modules.api import api
from modules.database.operations import validate_and_insert_data
from modules.file_handling.excel import process_file

# SETUP FLASK
app = Flask(__name__)
app.secret_key = '0g4Ty9YfjicKKQgRexLMJMroCSZ0CTni'

api = api() # pywebview api object

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
        results = process_file(save_path)
        if results:
            session['failed_rows'] = results['failed_rows']
            session['filename'] = results['filename']
            flash(f"File uploaded successfully. {len(results['failed_rows'])} rows have issues.", 'warning')
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
        try:
            # Get the corrections data from the form
            corrections_json = request.form.get('corrections')
            corrections = json.loads(corrections_json)
            
            
            # Prepare a list to collect all the updated rows for insertion
            rows_to_insert = []
            
            # Process each correction
            for correction in corrections:
                # Get the cleaned data from the correction
                rows_to_insert.append(correction['data'])

            for row in rows_to_insert:
                for key, value in row.items():
                    if value == '':
                        row[key] = None
            

            # Use our validation and insertion function
            successful_rows, new_failed_rows = validate_and_insert_data(rows_to_insert)
            
            # Check if all rows were successfully inserted
            if not new_failed_rows:
                flash(f"Successfully fixed and imported {len(successful_rows)} products.", "success")
                session.pop('failed_rows', None)
                return redirect(url_for('index'))
            else:
                # Some rows still have issues
                session['failed_rows'] = new_failed_rows
                flash(f"Fixed {len(successful_rows)} products, but {len(new_failed_rows)} still have issues.", "warning")
                return redirect(url_for('fix_errors'))
                
        except json.JSONDecodeError:
            flash('Invalid data format received', 'error')
            return redirect(url_for('fix_errors'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('fix_errors'))


def start_server():
    app.run(host='0.0.0.0', port=80)

if __name__ == '__main__':

    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()

    webview.create_window("PyWebView & Flask", "http://localhost/")
    webview.start() # debug=True
    sys.exit()