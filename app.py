import json
from flask import Flask, render_template, request, jsonify, redirect, send_file, url_for, session, flash
from flask_session import Session
from werkzeug.utils import secure_filename
import threading
import webview
import os
import sys
from modules.api import api
from modules.database.operations import validate_and_insert_data
from modules.file_handling.excel import generate_excel_template, process_file

# SETUP FLASK
app = Flask(__name__)
app.secret_key = '0g4Ty9YfjicKKQgRexLMJMroCSZ0CTni'

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flask_session")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
Session(app)

api = api() # pywebview api object

@app.route('/')
def index():
    return redirect(url_for('upload'))

########################################################################################

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')
    
    return jsonify({"error": "Invalid request"})
 
########################################################################################

@app.route('/upload/produse', methods=['POST'])
def upload_produse():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('upload'))

    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('upload'))

    filename = secure_filename(file.filename)  # Secure the filename
    save_path = os.path.join('uploads', filename)
    file.save(save_path)

    # Process file for produse table
    results = process_file(save_path, 'produse')
    if results and results.get('status') == 'partially processed':
        session['filename'] = results['filename']
        session['table_name'] = 'produse'  # Store the table name for the fix_errors route

        if results.get('failed_rows'):
            session['failed_rows'] = results['failed_rows']

        if results.get('duplicate_rows'):
            session['duplicate_rows'] = results['duplicate_rows']
        
        if results.get('failed_rows'):
            flash(f"File uploaded successfully. {len(results['failed_rows'])} rows have issues.", 'warning')
            return redirect(url_for('fix_errors'))
        elif results.get('duplicate_rows'):
            flash(f"File uploaded successfully. {len(results['duplicate_rows'])} rows are duplicates.", 'warning')
            return redirect(url_for('confirm_duplicates'))

        
        
    elif results and results.get('status') == 'processed':
        flash('Produse file uploaded successfully', 'success')
        return redirect(url_for('upload'))
    
    elif results and results.get('status') == 'invalid file type':
        flash('Invalid file type uploaded', 'error')
        return redirect(url_for('upload'))

    flash('Produse file uploaded successfully', 'success')
    return redirect(url_for('upload'))

########################################################################################

@app.route('/upload/furnizori', methods=['POST'])
def upload_furnizori():
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('upload'))

    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('upload'))

    filename = secure_filename(file.filename)  # Secure the filename
    save_path = os.path.join('uploads', filename)
    file.save(save_path)

    # Process file for furnizori table
    results = process_file(save_path, 'furnizori')
    if results and results.get('failed_rows'):
        session['failed_rows'] = results['failed_rows']
        session['filename'] = results['filename']
        session['table_name'] = 'furnizori'  # Store the table name for the fix_errors route
        flash(f"File uploaded successfully. {len(results['failed_rows'])} rows have issues.", 'warning')
        return redirect(url_for('fix_errors'))

    flash('Furnizori file uploaded successfully', 'success')
    return redirect(url_for('upload'))

########################################################################################

@app.route('/fix_errors', methods=['GET', 'POST'])
def fix_errors():
    if request.method == 'GET':
        if 'failed_rows' not in session:
            return redirect(url_for('upload'))
        
        failed_rows = session.get('failed_rows', [])
        filename = session.get('filename', '')
        table_name = session.get('table_name', 'produse')  # Default to produse if not specified
    
        return render_template('fix_errors.html', 
                              failed_rows=failed_rows, 
                              filename=filename,
                              table_name=table_name)

    elif request.method == 'POST':
        try:
            # Get the corrections data from the form
            corrections_json = request.form.get('corrections')
            corrections = json.loads(corrections_json)
            table_name = session.get('table_name', 'produse')  # Get the table name from session
            
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
            
            # Use our validation and insertion function with the appropriate table name
            successful_rows, new_failed_rows, duplicate_rows = validate_and_insert_data(
                rows_to_insert, 
                table_name=table_name
            )
            
            # Check if all rows were successfully inserted
            if not new_failed_rows:
                flash(f"Successfully fixed and imported {len(successful_rows)} {table_name}.", "success")
                session.pop('failed_rows', None)
                session.pop('table_name', None)
                return redirect(url_for('index'))
            else:
                # Some rows still have issues
                session['failed_rows'] = new_failed_rows
                flash(f"Fixed {len(successful_rows)} {table_name}, but {len(new_failed_rows)} still have issues.", "warning")
                return redirect(url_for('fix_errors'))
                
        except json.JSONDecodeError:
            flash('Invalid data format received', 'error')
            return redirect(url_for('fix_errors'))
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            return redirect(url_for('fix_errors'))

########################################################################################

@app.route('/confirm_duplicates', methods=['GET', 'POST'])
def confirm_duplicates():
    if request.method == 'GET':
        if 'duplicate_rows' not in session:
            return redirect(url_for('upload'))
        
        duplicate_rows = session.get('duplicate_rows', [])
        filename = session.get('filename', '')
        table_name = session.get('table_name', '')
        
        return render_template('confirm_duplicates.html',
                              duplicate_rows=duplicate_rows,
                              filename=filename,
                              table_name=table_name)

#########################################################################################

@app.route('/download_template/<table_name>', methods=['GET'])
def download_template(table_name):
    if table_name not in ['produse', 'furnizori']:
        flash('Invalid template type requested', 'error')
        return redirect(url_for('upload'))
    
    try:
        template_path = generate_excel_template(table_name)
        
        # Return the file as an attachment
        return send_file(
            template_path,
            as_attachment=True,
            download_name=f"{table_name}_template.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f'Error generating template: {str(e)}', 'error')
        return redirect(url_for('upload'))

def start_server():
    app.run(host='0.0.0.0', port=80)

if __name__ == '__main__':

    t = threading.Thread(target=start_server)
    t.daemon = True
    t.start()

    webview.create_window("PyWebView & Flask", "http://localhost/")
    webview.start(debug=True) # debug=True
    sys.exit()