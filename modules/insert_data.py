import math
import re
import sqlite3
from helpers import handle_nan

import pandas as pd


def validate_and_insert_data(data_rows, table_name='produse', connection=None):
    """
    Validates and inserts data into the database, applying column-specific filters.
    
    Args:
        data_rows (list): List of dictionaries containing the row data to insert
        table_name (str): Name of the table to insert data into
        connection: SQLite connection object (if None, one will be created)
        
    Returns:
        tuple: (successful_rows, failed_rows)
            - successful_rows: List of row IDs successfully inserted
            - failed_rows: List of dictionaries with error information
    """
    # Define validation filters for specific columns
    validation_filters = {
        'pret_intrare': {
            'filter': lambda x: isinstance(x, (int, float)) or (isinstance(x, str) and x.replace('.', '', 1).isdigit()),
            'error_msg': "must be a valid number",
            'expected_type': "REAL"
        },
        'pret_recomandat': {
            'filter': lambda x: x is None or isinstance(x, (int, float)) or (isinstance(x, str) and (x == '' or x.replace('.', '', 1).isdigit())),
            'error_msg': "must be a valid number or empty",
            'expected_type': "REAL"
        },
        'cota_TVA': {
            'filter': lambda x: x is None or isinstance(x, (int, float)) or (isinstance(x, str) and (x == '' or x.replace('.', '', 1).isdigit())),
            'error_msg': "must be a valid percentage number or empty",
            'expected_type': "REAL"
        },
        'greutate': {
            'filter': lambda x: x is None or isinstance(x, (int, float)) or (isinstance(x, str) and (x == '' or x.replace('.', '', 1).isdigit())),
            'error_msg': "must be a valid number or empty",
            'expected_type': "REAL"
        },
        'cod_produs': {
            'filter': lambda x: x is not None and x != '',
            'error_msg': "cannot be empty",
            'expected_type': "TEXT"
        },
        # Add more column validations as needed
    }
    
    successful_rows = []
    failed_rows = []
    close_conn = False
    
    # Create connection if not provided
    if connection is None:
        connection = sqlite3.connect('kuziini.db')
        close_conn = True
    
    cursor = connection.cursor()
    
    # Get table schema to validate against correct column types
    cursor.execute(f"PRAGMA table_info({table_name})")
    table_schema = {row[1]: row[2] for row in cursor.fetchall()}
    
    for row_index, row_data in enumerate(data_rows):
        # Clean the data - handle NaN values, etc.
        cleaned_data = {key: handle_nan(value) for key, value in row_data.items()}
        
        # Validate each column against its filter
        validation_errors = []
        for column, value in cleaned_data.items():
            # Skip columns not in the table schema
            if column not in table_schema:
                continue
                
            # Apply column-specific validation if defined
            if column in validation_filters:
                filter_func = validation_filters[column]['filter']
                if value == 1:
                    print(value, filter_func(value))
                if value is not None and not filter_func(value):
                    print("IT CAUGHT IT", value)
                    validation_errors.append({
                        'column': column,
                        'value': value,
                        'error': validation_filters[column]['error_msg'],
                        'expected_type': validation_filters[column]['expected_type']
                    })
        
        # If validation errors found, add to failed rows
        if validation_errors:
            failed_row = {
                'excel_row_number': row_index + 2,  # +2 to account for header and 0-indexing
                # 'row_id': generate_row_id(row_index, cleaned_data),
                'data': cleaned_data,
                'validation_errors': validation_errors,
                'error': f"Validation failed for {', '.join([e['column'] for e in validation_errors])}",
                'problematic_column': validation_errors[0]['column'],  # First error column
                'problematic_colmun_type': validation_errors[0]['expected_type']  # First error type
            }
            failed_rows.append(failed_row)
            continue
        
        # If no validation errors, attempt to insert
        try:
            # Get columns and values
            columns = [col for col in cleaned_data.keys() if col in table_schema]
            placeholders = ', '.join(['?' for _ in columns])
            values = [cleaned_data[col] for col in columns]
            
            # Build and execute the insert query
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            cursor.execute(query, values)
            connection.commit()
            
            # Add to successful rows
            successful_rows.append(cursor.lastrowid)
            
        except sqlite3.Error as e:
            error_msg = str(e)
            print(error_msg)
            connection.rollback()
            
            # Try to extract problematic column from error message
            problematic_column_match = re.search(f"{table_name}\.(\w+)", error_msg)
            problematic_column = problematic_column_match.group(1) if problematic_column_match else None
            
            # Try to extract column type from error message
            problematic_column_type_match = re.search(r"value in\s+(\w+)", error_msg)
            problematic_column_type = problematic_column_type_match.group(1) if problematic_column_type_match else None
            
            # If we couldn't get the column from the error message but have a problematic column
            if not problematic_column and 'column' in error_msg.lower():
                for col in cleaned_data.keys():
                    if col in error_msg:
                        problematic_column = col
                        break
            
            # Get the expected type from schema if possible
            if problematic_column and not problematic_column_type:
                problematic_column_type = table_schema.get(problematic_column)
                
            failed_row = {
                'excel_row_number': row_index + 2,  # +2 to account for header and 0-indexing
                # 'row_id': generate_row_id(row_index, cleaned_data),
                'data': cleaned_data,
                'error': error_msg,
                'problematic_column': problematic_column,
                'problematic_colmun_type': problematic_column_type
            }
            failed_rows.append(failed_row)
    
    # Close connection if we created it
    if close_conn:
        connection.close()
    
    return successful_rows, failed_rows
