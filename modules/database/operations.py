import math
import sqlite3
import re
from modules.database.connection import get_db_connection


def validate_and_insert_data(data_rows, table_name, conn=None):
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
        # Filtre Produse
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
        'furnizor_id': {
            'filter': lambda x: x is None or isinstance(x, int) or (isinstance(x, str) and x.isdigit()),
            'error_msg': "must be a valid supplier ID",
            'expected_type': "INTEGER"
        },

        # Filtre Furnizori
        
    }
    
    successful_rows = []
    failed_rows = []
    duplicate_rows = []
    close_conn = False
    
    # Create connection if not provided
    if conn is None:
        conn = get_db_connection()
        close_conn = True
    
    cursor = conn.cursor()
    
    # Get table schema to validate against correct column types
    cursor.execute(f"PRAGMA table_info({table_name})")
    table_schema = get_table_schema(table_name)
    
    for row_index, row_data in enumerate(data_rows):
        # Clean the data - handle NaN values, etc.
        cleaned_data = clean_and_format_data(row_data, table_schema)
        cleaned_data.pop("id", None)
        
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
                'data': cleaned_data,
                'validation_errors': validation_errors,
                'error': f"Validation failed for {', '.join([e['column'] for e in validation_errors])}",
                'problematic_column': validation_errors[0]['column'],  # First error column
                'problematic_colmun_type': validation_errors[0]['expected_type']  # First error type
            }
            failed_rows.append(failed_row)
            continue
            
        # Check if product code already exists in the database
        if 'cod_produs' in cleaned_data and cleaned_data['cod_produs']:
            # Execute query to check if cod_produs exists
            cursor.execute(
                "SELECT * FROM produse WHERE cod_produs = ?", 
                (cleaned_data['cod_produs'],)
            )
            existing_product = cursor.fetchone()
            
            if existing_product:
                # Convert DB row to dictionary
                columns = [column[0] for column in cursor.description]
                existing_data = dict(zip(columns, existing_product))
                
                # NOTE: in viitor ar trebui sa modific impementarea aceasta, folosind pre_process()
                existing_data.pop("id", None)
                cleaned_data.pop("id", None)

                existing_data.pop("pret_raft_fara_TVA", None)
                cleaned_data.pop("pret_raft_fara_TVA", None)

                existing_data.pop("furnizor_id", None)
                cleaned_data.pop("furnizor_id", None)

                # DEBUGGING
                # print(existing_data)
                # print(f"\n {existing_data == cleaned_data}\n {dict_differences(existing_data, cleaned_data)} \n\n")
                # print(cleaned_data)

                #if the new data doesn't have any changes, ignore it
                if existing_data == cleaned_data:
                    continue

                # Create a record with both existing and new data
                duplicate_row = {
                    'excel_row_number': row_index + 2,  # +2 for header and 0-indexing
                    'new_data': cleaned_data,
                    'existing_data': existing_data,
                    'cod_produs': cleaned_data['cod_produs']
                }
                
                # Add to duplicate_rows list
                duplicate_rows.append(duplicate_row)
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
            conn.commit()
            
            # Add to successful rows
            successful_rows.append(cleaned_data)
            
        except sqlite3.Error as e:
            error_msg = str(e)
            print(error_msg)
            conn.rollback()
            
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
                'data': cleaned_data,
                'error': error_msg,
                'problematic_column': problematic_column,
                'problematic_colmun_type': problematic_column_type
            }
            failed_rows.append(failed_row)
    
    update_product_rows_with_furnizor_id(successful_rows, conn)

    # Close connection if we created it
    if close_conn:
        conn.close()
    
    return successful_rows, failed_rows, duplicate_rows

def insert_duplicate_data_row(data_row, table_name, connection=None):
    """
    Updates an existing database row with data from an Excel import when a duplicate is found.
    
    Args:
        data_row (dict): Dictionary containing the row data to update, with both new_data and existing_data
        table_name (str): Name of the table to update
        connection: Optional SQLite connection object (if None, one will be created)
        
    Returns:
        bool: True if update was successful, False otherwise
        str: Error message if update failed, empty string otherwise
    """
    
    close_conn = False
    
    # Create connection if not provided
    if connection is None:
        connection = get_db_connection()
        close_conn = True
    
    cursor = connection.cursor()
    
    try:
        # Extract the product code and new data
        product_code = data_row.get('cod_produs')
        new_data = data_row.get('new_data', {})
        
        if not product_code or not new_data:
            return False, "Missing product code or update data"
        
        # Get table schema to validate fields
        cursor.execute(f"PRAGMA table_info({table_name})")
        table_schema = {row[1]: row[2] for row in cursor.fetchall()}
        
        # Prepare the SQL update
        set_clauses = []
        values = []
        
        # Create SET clauses for each column except cod_produs and id
        for key, value in new_data.items():
            # Skip the product code itself, id, and fields not in schema
            if key != 'cod_produs' and key != 'id' and key in table_schema:
                set_clauses.append(f"{key} = ?")
                values.append(value)
        
        # If no fields to update, return success
        if not set_clauses:
            return True, ""
        
        # Add the WHERE condition value
        values.append(product_code)
        
        # Build and execute the update query
        query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE cod_produs = ?"
        cursor.execute(query, values)
        connection.commit()
        
        # Check if a row was actually updated
        if cursor.rowcount == 0:
            return False, f"Product with code {product_code} not found"
        
        return True, ""
        
    except sqlite3.Error as e:
        # Rollback in case of error
        connection.rollback()
        return False, str(e)
    
    finally:
        # Close connection if we created it
        if close_conn:
            connection.close()

# Function to replace NaN with None
def handle_nan(value):
    if isinstance(value, float) and math.isnan(value):
        return None
    return value

def get_table_schema(table_name):
    """Get the schema of a table as a dictionary with column names as keys and types as values."""
    with sqlite3.connect('kuziini.db') as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return {row[1]: {'type': row[2], 'not_null': row[3], 'pk': row[5]} for row in cursor.fetchall()}
    
def clean_and_format_data(row_data, table_schema):
    """
    Clean and format row data according to the table schema.
    
    Args:
        row_data (dict): Dictionary containing the row data to be cleaned
        table_schema (dict): Dictionary with column names as keys and column types as values
        
    Returns:
        dict: Cleaned and properly formatted data
    """
    # First, handle NaN values
    cleaned_data = {key: handle_nan(value) for key, value in row_data.items()}
    
    # Then format according to column types in schema
    for column, value in cleaned_data.items():

        # Skip None values
        if value is None:
            continue
            
        # Skip columns not in the schema
        if column not in table_schema:
            continue
            
        column_type = table_schema[column]['type']

        # Convert values based on column type
        if column_type in ('TEXT', 'VARCHAR', 'CHAR', 'STRING'):
            # Convert to string for text columns
            cleaned_data[column] = str(value).strip()
        # elif column_type in ('INTEGER', 'INT'):
        #     # Try to convert to integer
        #     try:
        #         cleaned_data[column] = int(float(value))
        #     except (ValueError, TypeError):
        #         # If conversion fails, keep the original value
        #         pass
        # elif column_type in ('REAL', 'FLOAT', 'DOUBLE'):
        #     # Try to convert to float
        #     try:
        #         cleaned_data[column] = float(value)
        #     except (ValueError, TypeError):
        #         # If conversion fails, keep the original value
        #         pass
        # elif column_type == 'BOOLEAN':
        #     # Handle boolean values
        #     if isinstance(value, str):
        #         cleaned_data[column] = value.lower() in ('true', 't', 'yes', 'y', '1')
        #     else:
        #         cleaned_data[column] = bool(value)
                
    return cleaned_data

def update_products_with_furnizor_id(conn=None):
    """
    Updates all products in the database with the correct furnizor_id by matching the 
    furnizor_nume field with entries in the furnizori table.
    
    Returns:
        dict: A dictionary containing statistics about the update operation:
            - 'total_products': Total number of products processed
            - 'updated_products': Number of products successfully updated
            - 'failed_products': Number of products that couldn't be updated
            - 'not_found_suppliers': List of supplier names that couldn't be found
    """
    close_conn = False
    if not conn:
        close_conn = True
        conn = get_db_connection()
    cursor = conn.cursor()
    
    # Statistics for operation summary
    stats = {
        'total_products': 0,
        'updated_products': 0,
        'failed_products': 0,
        'not_found_suppliers': set()
    }
    
    try:
        # Get all products that have a furnizor_nume but no furnizor_id
        cursor.execute("""
            SELECT id, furnizor_nume 
            FROM produse 
            WHERE furnizor_nume IS NOT NULL 
        """)
        # AND (furnizor_id IS NULL OR furnizor_id = '')


        products = cursor.fetchall()
        
        stats['total_products'] = len(products)
        
        # Process each product
        for product in products:
            product_id = product['id']
            furnizor_nume = product['furnizor_nume']
            
            # Skip if furnizor_nume is empty
            if not furnizor_nume or furnizor_nume.strip() == '':
                stats['failed_products'] += 1
                continue
            
            # Find matching supplier in furnizori table
            # NOTE: este posibil sa trebuieasca sa adaug LIKE, dar pentru a nu corupe datele, voi folosi fix pe fix deocamdata
            cursor.execute("""
                SELECT id FROM furnizori 
                WHERE furnizor_nume = ?
            """, (furnizor_nume,))
            # cursor.execute("""
            #     SELECT id FROM furnizori 
            #     WHERE nume = ? OR nume LIKE ? OR ? LIKE CONCAT('%', nume, '%')
            # """, (furnizor_nume, f"%{furnizor_nume}%", furnizor_nume))
            
            supplier = cursor.fetchone()
            
            if supplier:
                # Update the product with the found furnizor_id
                cursor.execute("""
                    UPDATE produse 
                    SET furnizor_id = ? 
                    WHERE id = ?
                """, (supplier['id'], product_id))
                
                stats['updated_products'] += 1
            else:
                # Supplier not found
                stats['failed_products'] += 1
                stats['not_found_suppliers'].add(furnizor_nume)
        
        # Commit changes
        conn.commit()
        
        # Convert set to list for JSON serialization
        stats['not_found_suppliers'] = list(stats['not_found_suppliers'])
        
        return stats
        
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        if close_conn:
            conn.close()

def update_product_rows_with_furnizor_id(data_rows, conn=None):

    # NOTE: aceasta functie este chemata doar in validate_and_insert_data, este posibil sa trebuieasca sa fie chemata si din app.py de unde insert_duplicate_data_row() este chemata

    """
    Updates products in the database with their corresponding furnizor_id
    by matching the furnizor_nume field with entries in the furnizori table.
    
    Args:
        data_rows (list): List of dictionaries containing product data rows
        conn: Optional database connection
        
    Returns:
        dict: Statistics about the update operation:
            - 'total_rows': Total number of rows processed
            - 'updated_rows': Number of rows successfully updated
            - 'failed_rows': Number of rows that couldn't be updated
            - 'not_found_suppliers': List of supplier names that couldn't be found
    """
    close_conn = False
    if not conn:
        close_conn = True
        conn = get_db_connection()
    cursor = conn.cursor()
    
    # Statistics for operation summary
    stats = {
        'total_rows': len(data_rows),
        'updated_rows': 0,
        'failed_rows': 0,
        'not_found_suppliers': set()
    }
    
    # Create a cache of supplier names to IDs to minimize database queries
    furnizor_cache = {}
    
    try:
        conn.execute("BEGIN TRANSACTION")
        
        # Process each data row
        for row in data_rows:
            # Skip if row doesn't have necessary fields
            if 'furnizor_nume' not in row or not row['furnizor_nume'] or 'cod_produs' not in row:
                stats['failed_rows'] += 1
                continue
            
            furnizor_nume = row['furnizor_nume']
            cod_produs = row['cod_produs']
            
            # Skip if furnizor_nume is empty or cod_produs is missing
            if not furnizor_nume.strip() or not cod_produs:
                stats['failed_rows'] += 1
                continue
            
            # Check cache first
            if furnizor_nume in furnizor_cache:
                furnizor_id = furnizor_cache[furnizor_nume]
            else:
                # Look up in database if not in cache
                cursor.execute("""
                    SELECT id FROM furnizori 
                    WHERE furnizor_nume = ?
                """, (furnizor_nume,))
                
                furnizor = cursor.fetchone()
                if furnizor:
                    # Add to cache for future lookups
                    furnizor_id = furnizor[0]
                    furnizor_cache[furnizor_nume] = furnizor_id
                else:
                    # Supplier not found
                    stats['failed_rows'] += 1
                    stats['not_found_suppliers'].add(furnizor_nume)
                    continue
            
            # Update the product in the database with the found furnizor_id
            try:
                cursor.execute("""
                    UPDATE produse 
                    SET furnizor_id = ? 
                    WHERE cod_produs = ?
                """, (furnizor_id, cod_produs))
                
                if cursor.rowcount > 0:
                    stats['updated_rows'] += 1
                else:
                    stats['failed_rows'] += 1
            except sqlite3.Error:
                stats['failed_rows'] += 1
        
        # Commit changes
        conn.commit()
        
        # Convert set to list for JSON serialization
        stats['not_found_suppliers'] = list(stats['not_found_suppliers'])
        
        return stats
        
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        if close_conn:
            conn.close()

def calculate_pret_fara_TVA_for_products(conn=None):
    """
    Updates all products in the database with the correct pret_raft_fara_TVA value
    by calculating it based on the adaos_comercial of the product's supplier.
    
    The calculation uses the formula:
    pret_raft_fara_TVA = pret_intrare * (1 + adaos_comercial)
    
    Uses a cache to minimize database queries for supplier adaos_comercial values.
    
    Args:
        conn: Optional SQLite connection object (if None, one will be created)
        
    Returns:
        dict: A dictionary containing statistics about the update operation:
            - 'total_products': Total number of products processed
            - 'updated_products': Number of products successfully updated
            - 'failed_products': Number of products that couldn't be updated
            - 'no_supplier_products': Number of products without a supplier
            - 'no_adaos_suppliers': Number of products with suppliers missing adaos_comercial
            - 'no_initial_price_products': Number of products that do not have an initial price (pret_intrare_fara_TVA)
    """
    
    close_conn = False
    if not conn:
        close_conn = True
        conn = get_db_connection()
    cursor = conn.cursor()
    
    # Statistics for operation summary
    stats = {
        'total_products': 0,
        'no_initial_price_products': 0,
        'updated_products': 0,
        'failed_products': 0,
        'no_supplier_products': 0,
        'no_adaos_suppliers': 0,
        'suppliers_without_adaos': set()
    }
    
    # Create a cache for supplier adaos values to minimize database queries
    adaos_cache = {}
    
    try:
        # First, build the cache of all suppliers with their adaos_comercial
        cursor.execute("SELECT id, furnizor_nume, adaos_comercial FROM furnizori")
        suppliers = cursor.fetchall()
        
        for supplier in suppliers:
            adaos_cache[supplier['id']] = {
                'adaos_comercial': supplier['adaos_comercial'],
                'nume': supplier['furnizor_nume']
            }
        
        # Get all products which don't have an initial price
        cursor.execute("""
            SELECT
                id
            FROM    
                produse
            WHERE
                pret_intrare IS NULL       
                       """)
        
        no_initial_price_products = cursor.fetchall()
        stats["no_initial_price_products"] = len(no_initial_price_products)

        # Get all products with their price and supplier ID
        cursor.execute("""
            SELECT 
                id, 
                cod_produs,
                pret_intrare, 
                furnizor_id
            FROM 
                produse
            WHERE 
                pret_intrare IS NOT NULL
        """)
        
        products = cursor.fetchall()
        stats['total_products'] = len(products) + len(no_initial_price_products)
        
        # Begin transaction for batch update
        conn.execute("BEGIN TRANSACTION")
        
        # Process each product
        for product in products:
            product_id = product['id']
            cod_produs = product['cod_produs']
            pret_intrare = product['pret_intrare']
            furnizor_id = product['furnizor_id']
            
            # Skip if product has no price
            if pret_intrare is None or pret_intrare == 0:
                stats['failed_products'] += 1
                continue
            
            # Skip if product has no supplier
            if furnizor_id is None:
                stats['no_supplier_products'] += 1
                continue
            
            # Get supplier adaos_comercial from cache
            supplier_info = adaos_cache.get(furnizor_id)
            
            # Skip if supplier has no adaos_comercial
            if supplier_info is None or supplier_info['adaos_comercial'] is None or supplier_info['adaos_comercial'] == 0:
                stats['no_adaos_suppliers'] += 1
                if supplier_info:
                    stats['suppliers_without_adaos'].add(supplier_info['nume'])
                continue
            
            adaos_comercial = supplier_info['adaos_comercial']
            
            # Calculate pret_raft_fara_TVA using the formula
            try:
                pret_raft_fara_TVA = pret_intrare *(1 + adaos_comercial)
                
                # Round to 2 decimal places for currency
                pret_raft_fara_TVA = round(pret_raft_fara_TVA, 2)
                
                # Update the product
                cursor.execute("""
                    UPDATE produse 
                    SET pret_raft_fara_TVA = ? 
                    WHERE id = ?
                """, (pret_raft_fara_TVA, product_id))
                
                stats['updated_products'] += 1
            except Exception as e:
                print(f"Error updating product {cod_produs}: {str(e)}")
                stats['failed_products'] += 1
        
        # Commit changes
        conn.commit()
        
        # Convert set to list for JSON serialization
        stats['suppliers_without_adaos'] = list(stats['suppliers_without_adaos'])
        
        return stats
        
    except sqlite3.Error as e:
        conn.rollback()
        raise e
    finally:
        if close_conn:
            conn.close()

# FOR DEBUGGING used at line 137
def dict_differences(dict1, dict2):
                    """Find differences between two dictionaries and return them in a readable format."""
                    all_keys = set(dict1.keys()) | set(dict2.keys())
                    differences = []
                    
                    for key in all_keys:
                        if key not in dict1:
                            differences.append(f"Key '{key}' only in second dict with value: {dict2[key]}")
                        elif key not in dict2:
                            differences.append(f"Key '{key}' only in first dict with value: {dict1[key]}")
                        elif dict1[key] != dict2[key]:
                            differences.append(f"Key '{key}' has different values: {dict1[key]} vs {dict2[key]}")
                    
                    return differences