import base64
import csv
import json
import math
import os
import pandas as pd
import sqlite3
import re
from modules.helpers import handle_nan

# Remove global connection
# conn = sqlite3.connect('kuziini.db')
# cur = conn.cursor()

def process_file(self, file_path):
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
            failed_rows = insert_excel_data_into_db(save_path)
            if failed_rows:
                results = {
                    'filename': name,
                    'size': size,
                    'path': save_path,
                    'status': 'partially processed',
                    'failed_rows': failed_rows
                }
            else:
                # results.append({
                #     'filename': name,
                #     'size': size,
                #     'path': save_path,
                #     'status': 'processed'
                # })
                results = None
        else:
            results = None
            # results.append({
            #     'filename': name,
            #     'size': size,
            #     'path': save_path,
            #     'status': 'uploaded'
            # })
        
        #DEBUGGING
        with open('uploads/results.json', 'w') as f:
            f.write(json.dumps(results, indent=4))

        return results # json.dumps(results)


def insert_excel_data_into_db(file_path):
    failed_rows = []
    
    try:
        # Create connection inside function
        with sqlite3.connect('kuziini.db') as conn:
            cur = conn.cursor()

            df = pd.read_excel(file_path)

            for index, row in df.iterrows():
                categorie = row.get('categorie')
                subcategorie = row.get('subcategorie')
                camera = row.get('camera')
                destinatie = row.get('destinatie')
                colectie = row.get('colectie')
                cod_produs = row.get('cod_produs')
                descriere_scurta = row.get('descriere_scurta')
                descriere_detaliata = row.get('descriere_detaliata')
                dimensiuni = row.get('dimensiuni')
                greutate = row.get('greutate')
                cota_TVA = row.get('cota_TVA')
                pret_intrare = row.get('pret_intrare')
                pret_raft_fara_TVA = row.get('pret_raft_fara_TVA')
                pret_recomandat = row.get('pret_recomandat')
                poza_1 = row.get('poza_1')
                poza_2 = row.get('poza_2')
                termen_de_livrare = row.get('termen_de_livrare')
                culoare = row.get('culoare')
                atribute_specifice = row.get('atribute_specifice')
                compatibil_cu = row.get('compatibil_cu')
                furnizor_nume = row.get('furnizor_nume')
                furnizor_id = row.get('furnizor_id')
                try:
                    cur.execute("""
                        INSERT INTO produse (
                            categorie, subcategorie, camera, destinatie, colectie,
                            cod_produs, descriere_scurta, descriere_detaliata, dimensiuni,
                            greutate, cota_TVA, pret_intrare, pret_raft_fara_TVA,
                            pret_recomandat, poza_1, poza_2, termen_de_livrare,
                            culoare, atribute_specifice, compatibil_cu,
                            furnizor_nume, furnizor_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        categorie, subcategorie, camera, destinatie, colectie,
                        cod_produs, descriere_scurta, descriere_detaliata, dimensiuni,
                        greutate, cota_TVA, pret_intrare, pret_raft_fara_TVA,
                        pret_recomandat, poza_1, poza_2, termen_de_livrare,
                        culoare, atribute_specifice, compatibil_cu,
                        furnizor_nume, furnizor_id
                    ))
                    conn.commit()
                    # print(f"Inserted row {index + 2}")
                    
                except sqlite3.Error as e:
                    error_msg = str(e)
                    print(f"Failed to insert row {index + 2}: {error_msg}")
                    conn.rollback()

                    problematic_column_match = re.search(r"produse\.(\w+)", error_msg)
                    if problematic_column_match:
                        problematic_column = problematic_column_match.group(1)

                    problematic_column_type_match = re.search(r"value in\s+(\w+)", error_msg)
                    if problematic_column_type_match:
                        problematic_column_type = problematic_column_type_match.group(1)

                    failed_rows.append({
                        'excel_row_number': index + 2,
                        # 'row_id': cur.lastrowid,
                        'data': {key: handle_nan(value) for key, value in row.to_dict().items()}, # Replace NaN with None from all columns in row
                        'error': error_msg,
                        'problematic_column': problematic_column,
                        'problematic_colmun_type': problematic_column_type
                    })
                    
    except Exception as e:
        failed_rows.append({
            'row_number': 'N/A',
            'data': None,
            'error': f"Failed to read Excel file: {str(e)}"
        })
    
    return failed_rows
