import os
import pandas as pd
from datetime import datetime
from modules.database.connection import get_db_connection

def export_table_to_excel(table_name, output_path=None):
    """
    Export a database table to an Excel file.
    
    Args:
        table_name (str): Name of the table to export
        output_path (str, optional): Path where to save the Excel file. 
                                    If None, a default path is used.
    
    Returns:
        str: Path to the generated Excel file
    """
    try:
        # Create connection
        conn = get_db_connection()
        
        # Query all data from the table
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql_query(query, conn)
        
        # Close connection
        conn.close()
        
        # Generate output path if not provided
        if output_path is None:
            # Create exports directory if it doesn't exist
            os.makedirs('exports', exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'exports/{table_name}_export_{timestamp}.xlsx'
        
        # Export to Excel
        df.to_excel(output_path, index=False, engine='openpyxl')
        
        return {
            'success': True,
            'file_path': output_path,
            'row_count': len(df)
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def export_all_tables(output_path=None):
    """
    Export all tables from the database to a single Excel file with multiple sheets.
    
    Args:
        output_path (str, optional): Path where to save the Excel file.
                                    If None, a default path is used.
    
    Returns:
        dict: Result information including path to the generated Excel file
    """
    try:
        # Create connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        # Generate output path if not provided
        if output_path is None:
            # Create exports directory if it doesn't exist
            os.makedirs('exports', exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'exports/database_export_{timestamp}.xlsx'
        
        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            table_data = {}
            
            # Export each table to a separate sheet
            for table in tables:
                if table != 'sqlite_sequence':  # Skip SQLite internal tables
                    query = f"SELECT * FROM {table}"
                    df = pd.read_sql_query(query, conn)
                    
                    # Write to Excel
                    df.to_excel(writer, sheet_name=table, index=False)
                    
                    # Store info for return
                    table_data[table] = len(df)
        
        # Close connection
        conn.close()
        
        return {
            'success': True,
            'file_path': output_path,
            'tables': table_data
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }