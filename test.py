import sqlite3
import re

def detect_failing_column(db_path, table_name, insert_data):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get the table schema to check required columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()

    # Find NOT NULL columns
    not_null_columns = {col[1] for col in columns_info if col[3] == 1}  # col[3] is the NOT NULL flag

    try:
        # Generate an INSERT statement with only the provided columns
        columns = ", ".join(insert_data.keys())
        placeholders = ", ".join(["?"] * len(insert_data))
        values = tuple(insert_data.values())

        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)
        conn.commit()
        print("Insert successful!")

    except sqlite3.IntegrityError as e:
        error_message = str(e)
        print("Insert failed:", error_message)

        # Try to extract the column causing the issue
        match = re.search(r"NOT NULL constraint failed: (\w+)\.(\w+)", error_message)
        if match:
            failing_column = match.group(2)
            print(f"Missing required column: {failing_column}")
            return failing_column

        match = re.search(r"UNIQUE constraint failed: (\w+)\.(\w+)", error_message)
        if match:
            failing_column = match.group(2)
            print(f"Duplicate value in unique column: {failing_column}")
            return failing_column

        print("Could not determine the failing column.")

    finally:
        conn.close()

# Example Usage
db_path = "kuziini.db"
table_name = "produse"
insert_data = {"pret_intrare": "Alice"}  # Intentionally leaving out required columns

detect_failing_column(db_path, table_name, insert_data)
