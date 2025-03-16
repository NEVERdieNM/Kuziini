# Converts list of lists to list of dicts
import math
import sqlite3


def dict_query(result):
    """
    Converts a list of lists to a list of dictionaries.

    Parameters:
    result (object): A database result object with methods keys() and fetchall().

    Returns:
    list: A list of dictionaries where each dictionary represents a row.
    """
    columns = result.keys()
    rows = result.fetchall()
    if not rows:
        return {}
    return [dict(zip(columns, row)) for row in rows]

#converts a single row to a dict
def dict_row(result):
    columns = result.keys()
    row = result.fetchone()
    if not row:
        return {}
    return dict(zip(columns, row))

# Function to replace NaN with None
def handle_nan(value):
    if isinstance(value, float) and math.isnan(value):
        return None
    return value

def get_db_connection():
    """Helper function to connect to the SQLite database"""
    conn = sqlite3.connect('kuziini.db')
    conn.row_factory = sqlite3.Row
    return conn
