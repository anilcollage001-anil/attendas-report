"""
addface.py - Student Registration & Database Module
Manages student records in an SQLite database.
Each student has: name, roll number, phone number, class/section.
"""

import sqlite3
import os
import re

# Database file path (same directory as this script)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "attendance.db")


def get_connection():
    """
    Get a connection to the SQLite database.
    Creates the database and tables if they don't exist.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    conn = sqlite3.connect(DB_PATH)

    
    conn.row_factory = sqlite3.Row  # Access columns by name
    
    # Create tables if they don't exist
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            phone_number TEXT NOT NULL,
            class_section TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            roll_number TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT DEFAULT 'Present',
            verified_via TEXT DEFAULT 'OTP',
            FOREIGN KEY (student_id) REFERENCES students(id),
            UNIQUE(roll_number, date)
        )
    ''')
    
    conn.commit()
    return conn


def validate_phone_number(phone):
    """
    Validate an Indian phone number (10 digits, starts with 6-9).
    
    Args:
        phone (str): Phone number to validate
    
    Returns:
        tuple: (bool, str) - (is_valid, cleaned_number_or_error)
    """
    # Remove spaces, dashes, and +91 prefix
    cleaned = re.sub(r'[\s\-]', '', phone)
    if cleaned.startswith('+91'):
        cleaned = cleaned[3:]
    elif cleaned.startswith('91') and len(cleaned) == 12:
        cleaned = cleaned[2:]
    
    if not cleaned.isdigit():
        return False, "Phone number must contain only digits."
    
    if len(cleaned) != 10:
        return False, "Phone number must be exactly 10 digits."
    
    if cleaned[0] not in '6789':
        return False, "Invalid phone number. Must start with 6, 7, 8, or 9."
    
    return True, cleaned


def add_student(name, roll_number, phone_number, class_section):
    """
    Register a new student in the database.
    
    Args:
        name (str): Student's full name
        roll_number (str): Unique roll number
        phone_number (str): 10-digit phone number
        class_section (str): Class and section (e.g., "10-A")
    
    Returns:
        tuple: (bool, str) - (success, message)
    """
    # Validate inputs
    if not name or not name.strip():
        return False, "Student name cannot be empty."
    
    if not roll_number or not roll_number.strip():
        return False, "Roll number cannot be empty."
    
    # Validate phone number
    is_valid, result = validate_phone_number(phone_number)
    if not is_valid:
        return False, result
    phone_number = result  # Use cleaned number
    
    if not class_section or not class_section.strip():
        return False, "Class/Section cannot be empty."
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO students (name, roll_number, phone_number, class_section) VALUES (?, ?, ?, ?)",
            (name.strip(), roll_number.strip().upper(), phone_number, class_section.strip().upper())
        )
        
        conn.commit()
        conn.close()
        return True, f"Student '{name.strip()}' (Roll: {roll_number.strip().upper()}) registered successfully!"
    
    except sqlite3.IntegrityError:
        conn.close()
        return False, f"Roll number '{roll_number.strip().upper()}' is already registered."
    except Exception as e:
        conn.close()
        return False, f"Database error: {str(e)}"


def get_student_by_phone(phone_number):
    """
    Look up a student by their phone number.
    
    Args:
        phone_number (str): Phone number to search
    
    Returns:
        list: List of student records (dicts) matching the phone number
    """
    is_valid, cleaned = validate_phone_number(phone_number)
    if not is_valid:
        return []
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE phone_number = ?", (cleaned,))
    students = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return students


def get_student_by_roll(roll_number):
    """
    Look up a student by their roll number.
    
    Args:
        roll_number (str): Roll number to search
    
    Returns:
        dict or None: Student record if found
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE roll_number = ?", (roll_number.strip().upper(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_students():
    """
    Get all registered students.
    
    Returns:
        list: List of all student records (dicts)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students ORDER BY class_section, roll_number")
    students = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return students


def delete_student(roll_number):
    """
    Delete a student by roll number.
    
    Args:
        roll_number (str): Roll number of student to delete
    
    Returns:
        tuple: (bool, str) - (success, message)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE roll_number = ?", (roll_number.strip().upper(),))
    
    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        return True, f"Student with roll number '{roll_number.strip().upper()}' deleted."
    else:
        conn.close()
        return False, f"No student found with roll number '{roll_number.strip().upper()}'."


def update_student_phone(roll_number, new_phone):
    """
    Update a student's phone number.
    
    Args:
        roll_number (str): Roll number of student
        new_phone (str): New phone number
    
    Returns:
        tuple: (bool, str) - (success, message)
    """
    is_valid, cleaned = validate_phone_number(new_phone)
    if not is_valid:
        return False, cleaned
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE students SET phone_number = ? WHERE roll_number = ?",
        (cleaned, roll_number.strip().upper())
    )
    
    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        return True, f"Phone number updated for roll number '{roll_number.strip().upper()}'."
    else:
        conn.close()
        return False, f"No student found with roll number '{roll_number.strip().upper()}'."


if __name__ == "__main__":
    # Quick test
    print("Testing student registration...")
    
    success, msg = add_student("Rahul Sharma", "CS101", "9876543210", "10-A")
    print(f"Add: {success} - {msg}")
    
    success, msg = add_student("Priya Patel", "CS102", "8765432109", "10-A")
    print(f"Add: {success} - {msg}")
    
    students = get_all_students()
    print(f"\nAll Students ({len(students)}):")
    for s in students:
        print(f"  {s['roll_number']}: {s['name']} | Phone: {s['phone_number']} | Class: {s['class_section']}")
    
    found = get_student_by_phone("9876543210")
    print(f"\nSearch by phone '9876543210': {[s['name'] for s in found]}")