import base64
import json
import os
import pandas as pd
import sqlite3
from modules.database.operations import get_table_schema, validate_and_insert_data

# Remove global connection
# conn = sqlite3.connect('kuziini.db')
# cur = conn.cursor()

def process_file(file_path, table_name):
        results = {}

        # Get file info
        file_data = {
            'name': os.path.basename(file_path),
            'type': os.path.splitext(file_path)[1],
            'size': os.path.getsize(file_path),
            'data': base64.b64encode(open(file_path, 'rb').read()).decode('utf-8')
        }

        # Extract file info
        name = file_data['name']
        file_type = file_data['type']
        size = file_data['size']
        data = file_data['data']
        
        # Decode base64 data
        binary_data = base64.b64decode(data)

        # Save file to disk
        save_path = os.path.join('uploads', name)
        os.makedirs('uploads', exist_ok=True)
        
        with open(save_path, 'wb') as f:
            f.write(binary_data)
        
        # Process file
        if name.endswith(('.xls', '.xlsx')):
            _, failed_rows, duplicate_rows, incorrect_table = insert_excel_data_into_db(save_path, table_name)

            if incorrect_table:
                return {
                    'incorrect_table': True
                }

            if failed_rows or duplicate_rows:
                results = {
                    'filename': name,
                    'size': size,
                    'path': save_path,
                    'status': 'partially processed',
                }

                if failed_rows:
                    results['failed_rows'] = failed_rows
                if duplicate_rows:
                    results['duplicate_rows'] = duplicate_rows

            else:
                results = {
                    'filename': name,
                    'size': size,
                    'path': save_path,
                    'status': 'processed'
                }
        else:
            results = {
                'filename': name,
                'size': size,
                'path': save_path,
                'status': 'invalid file type'
            }
        
        #DEBUGGING
        with open('uploads/results.json', 'w') as f:
            f.write(json.dumps(results, indent=4))

        return results # json.dumps(results)



def insert_excel_data_into_db(file_path, table_name):
    failed_rows = []
    duplicate_rows = []
    successful_rows = []

    try:
        # Create connection inside function
        with sqlite3.connect('kuziini.db') as conn:

            df = pd.read_excel(file_path)

            rows = df.replace({float('nan'): None}).to_dict('records')
            
            # NOTE: implementarea aceasta ar trebui imbunatatita
            incorrect_table = False
            if table_name == 'produse' and ('adaos_comercial' in rows[0] or 'adresa' in rows[0]):
                incorrect_table = True
                return None, None, None, incorrect_table
            elif table_name == 'furnizori' and (rows[0].get('cod_produs') or rows[0].get('categorie')):
                incorrect_table = True
                return None, None, None, incorrect_table


            successful_rows, failed_rows, duplicate_rows = validate_and_insert_data(rows, table_name, conn=conn)

            return successful_rows, failed_rows, duplicate_rows, incorrect_table
    except Exception as e:
        failed_rows.append({
            'row_number': 'N/A',
            'data': None,
            'error': f"Failed to read Excel file: {str(e)}"
        })
        raise e
    
    return successful_rows, failed_rows, duplicate_rows, incorrect_table



def preprocess_produse_excel(file_path):
    """Preprocess Excel file to ensure it matches the expected format."""
    df = pd.read_excel(file_path)
    
    # Get schema to compare against
    schema = get_table_schema('produse')
    
    # Check for required columns
    missing_columns = [col for col in schema if col not in df.columns and (col != 'id' or col != 'pret_raft_fara_TVA')]
    if missing_columns:
        return {
            'success': False,
            'error': f"Missing required columns: {', '.join(missing_columns)}",
            'df': None
        }
    
    # Remove any columns that don't exist in the schema
    extra_columns = [col for col in df.columns if col not in schema]
    if extra_columns:
        df = df.drop(columns=extra_columns)
    
    # Convert types where possible
    for col, details in schema.items():
        if col in df.columns:
            try:
                if details['type'] == 'REAL':
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                elif details['type'] == 'INTEGER':
                    df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')  # Int64 allows NaN
            except Exception as e:
                print(f"Error converting column {col}: {e}")
    
    return {
        'success': True, 
        'df': df,
        'extra_columns': extra_columns
    }



def generate_excel_template(table_name):
    """Generate an Excel template that matches the database schema."""
    schema = get_table_schema(table_name)
    
    # Create a DataFrame with the columns from the schema
    df = pd.DataFrame(columns=list(schema.keys()))
    
    # Remove 'id' as it's typically auto-generated
    if 'id' in df.columns:
        df = df.drop('id', axis=1)
    
    # Save to Excel
    os.makedirs('excel_templates', exist_ok=True)
    template_path = f'excel_templates/{table_name}_template.xlsx'
    df.to_excel(template_path, index=False)
    
    return template_path
