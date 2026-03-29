"""
xyz.py - OTP-Based Attendance System (Main Application)
Menu-driven CLI application for managing student attendance via OTP verification.

Flow:
  1. Student enters phone number
  2. System finds all students linked to that phone
  3. Student selects their name
  4. OTP is generated and "sent" to the phone
  5. Student enters OTP to verify
  6. Attendance is marked upon successful verification
"""

import datetime
import sqlite3
import os
import sys

# Import project modules
from generate import generate_otp, store_otp, verify_otp
from text import send_otp_message
from addface import (
    get_connection,
    add_student,
    get_student_by_phone,
    get_student_by_roll,
    get_all_students,
    delete_student,
    update_student_phone,
    validate_phone_number,
    DB_PATH
)


# ============================================================
#  ATTENDANCE FUNCTIONS
# ============================================================

def mark_attendance(student):
    """
    Mark attendance for a student in the database.
    
    Args:
        student (dict): Student record from the database
    
    Returns:
        tuple: (bool, str) - (success, message)
    """
    now = datetime.datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO attendance (student_id, roll_number, date, time, status, verified_via) VALUES (?, ?, ?, ?, ?, ?)",
            (student['id'], student['roll_number'], date_str, time_str, 'Present', 'OTP')
        )
        
        conn.commit()
        conn.close()
        return True, f"Attendance marked for {student['name']} (Roll: {student['roll_number']}) at {time_str} on {date_str}"
    
    except sqlite3.IntegrityError:
        conn.close()
        return False, f"Attendance already marked for {student['name']} (Roll: {student['roll_number']}) today ({date_str})."
    except Exception as e:
        conn.close()
        return False, f"Error marking attendance: {str(e)}"


def get_today_attendance():
    """
    Get all attendance records for today.
    
    Returns:
        list: List of attendance records with student info
    """
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.*, s.name, s.class_section, s.phone_number
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.date = ?
        ORDER BY a.time
    ''', (today,))
    
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return records


def get_attendance_by_date(date_str):
    """
    Get all attendance records for a specific date.
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
    
    Returns:
        list: List of attendance records with student info
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.*, s.name, s.class_section, s.phone_number
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.date = ?
        ORDER BY a.time
    ''', (date_str,))
    
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return records


def get_student_attendance_report(roll_number):
    """
    Get full attendance history for a student.
    
    Args:
        roll_number (str): Student's roll number
    
    Returns:
        list: List of attendance records
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.date, a.time, a.status, a.verified_via
        FROM attendance a
        WHERE a.roll_number = ?
        ORDER BY a.date DESC, a.time DESC
    ''', (roll_number.strip().upper(),))
    
    records = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return records


# ============================================================
#  OTP ATTENDANCE FLOW
# ============================================================

def otp_attendance_flow():
    """
    Main OTP-based attendance flow:
    1. Enter phone number
    2. Find linked students
    3. Select student
    4. Send OTP
    5. Verify OTP
    6. Mark attendance
    """
    print("\n" + "=" * 55)
    print("  📋  OTP-BASED ATTENDANCE VERIFICATION")
    print("=" * 55)
    
    # Step 1: Enter phone number
    phone = input("\n  📱 Enter your registered phone number: ").strip()
    
    is_valid, result = validate_phone_number(phone)
    if not is_valid:
        print(f"\n  ❌ {result}")
        return
    phone = result
    
    # Step 2: Find students linked to this phone
    students = get_student_by_phone(phone)
    
    if not students:
        print(f"\n  ❌ No students found with phone number: {phone}")
        print("  💡 Please register first using the 'Register Student' option.")
        return
    
    # Step 3: Select student (if multiple students share the same phone)
    if len(students) == 1:
        selected = students[0]
        print(f"\n  👤 Student found: {selected['name']} (Roll: {selected['roll_number']}, Class: {selected['class_section']})")
    else:
        print(f"\n  📋 Multiple students found with this phone number:")
        print("  " + "-" * 45)
        for i, s in enumerate(students, 1):
            print(f"  {i}. {s['name']} | Roll: {s['roll_number']} | Class: {s['class_section']}")
        print("  " + "-" * 45)
        
        try:
            choice = int(input("\n  Select student number: "))
            if choice < 1 or choice > len(students):
                print("\n  ❌ Invalid selection.")
                return
            selected = students[choice - 1]
        except ValueError:
            print("\n  ❌ Please enter a valid number.")
            return
    
    # Step 4: Generate and send OTP
    otp = generate_otp()
    store_otp(phone, otp)
    
    success, msg = send_otp_message(phone, otp)
    if not success:
        print(f"\n  ❌ Failed to send OTP: {msg}")
        return
    print(f"  ✅ {msg}")
    
    # Step 5: Verify OTP (allow up to 3 attempts)
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        entered_otp = input(f"\n  🔑 Enter OTP (Attempt {attempt}/{max_attempts}): ").strip()
        
        success, msg = verify_otp(phone, entered_otp)
        
        if success:
            print(f"\n  ✅ {msg}")
            
            # Step 6: Mark attendance
            att_success, att_msg = mark_attendance(selected)
            if att_success:
                print(f"  🎉 {att_msg}")
            else:
                print(f"  ⚠️  {att_msg}")
            return
        else:
            print(f"  ❌ {msg}")
            if "expired" in msg.lower():
                return
            # Re-store the OTP for remaining attempts (since verify deletes it on mismatch only on match)
            # On wrong OTP, the OTP stays in store, so no need to re-store
    
    print("\n  ❌ Maximum attempts reached. Please try again later.")


# ============================================================
#  STUDENT REGISTRATION FLOW
# ============================================================

def register_student_flow():
    """Interactive student registration."""
    print("\n" + "=" * 55)
    print("  📝  STUDENT REGISTRATION")
    print("=" * 55)
    
    name = input("\n  👤 Enter student name: ").strip()
    roll = input("  🔢 Enter roll number: ").strip()
    phone = input("  📱 Enter phone number (10 digits): ").strip()
    cls = input("  🏫 Enter class-section (e.g., 10-A): ").strip()
    
    success, msg = add_student(name, roll, phone, cls)
    
    if success:
        print(f"\n  ✅ {msg}")
    else:
        print(f"\n  ❌ {msg}")


# ============================================================
#  VIEW ATTENDANCE REPORTS
# ============================================================

def view_today_attendance():
    """Display today's attendance records."""
    print("\n" + "=" * 55)
    print("  📊  TODAY'S ATTENDANCE REPORT")
    print("=" * 55)
    
    records = get_today_attendance()
    
    if not records:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        print(f"\n  📭 No attendance records for today ({today}).")
        return
    
    print(f"\n  {'#':<4} {'Name':<20} {'Roll':<10} {'Class':<8} {'Time':<10} {'Status':<10}")
    print("  " + "-" * 65)
    
    for i, r in enumerate(records, 1):
        print(f"  {i:<4} {r['name']:<20} {r['roll_number']:<10} {r['class_section']:<8} {r['time']:<10} {r['status']:<10}")
    
    print(f"\n  📈 Total present: {len(records)}")
    
    all_students = get_all_students()
    if all_students:
        absent_count = len(all_students) - len(records)
        print(f"  📉 Total absent:  {absent_count}")
        print(f"  📊 Attendance %:  {len(records) / len(all_students) * 100:.1f}%")


def view_attendance_by_date():
    """View attendance for a specific date."""
    print("\n" + "=" * 55)
    print("  📅  ATTENDANCE BY DATE")
    print("=" * 55)
    
    date_input = input("\n  📅 Enter date (YYYY-MM-DD): ").strip()
    
    try:
        datetime.datetime.strptime(date_input, "%Y-%m-%d")
    except ValueError:
        print("\n  ❌ Invalid date format. Please use YYYY-MM-DD.")
        return
    
    records = get_attendance_by_date(date_input)
    
    if not records:
        print(f"\n  📭 No attendance records for {date_input}.")
        return
    
    print(f"\n  Attendance for {date_input}:")
    print(f"  {'#':<4} {'Name':<20} {'Roll':<10} {'Class':<8} {'Time':<10} {'Status':<10}")
    print("  " + "-" * 65)
    
    for i, r in enumerate(records, 1):
        print(f"  {i:<4} {r['name']:<20} {r['roll_number']:<10} {r['class_section']:<8} {r['time']:<10} {r['status']:<10}")
    
    print(f"\n  📈 Total present: {len(records)}")


def view_student_report():
    """View attendance report for a specific student."""
    print("\n" + "=" * 55)
    print("  👤  STUDENT ATTENDANCE REPORT")
    print("=" * 55)
    
    roll = input("\n  🔢 Enter student roll number: ").strip()
    student = get_student_by_roll(roll)
    
    if not student:
        print(f"\n  ❌ No student found with roll number: {roll.upper()}")
        return
    
    print(f"\n  Student: {student['name']}")
    print(f"  Roll:    {student['roll_number']}")
    print(f"  Class:   {student['class_section']}")
    print(f"  Phone:   {student['phone_number']}")
    
    records = get_student_attendance_report(roll)
    
    if not records:
        print("\n  📭 No attendance records found.")
        return
    
    print(f"\n  {'#':<4} {'Date':<14} {'Time':<10} {'Status':<10} {'Verified':<10}")
    print("  " + "-" * 50)
    
    for i, r in enumerate(records, 1):
        print(f"  {i:<4} {r['date']:<14} {r['time']:<10} {r['status']:<10} {r['verified_via']:<10}")
    
    print(f"\n  📈 Total days present: {len(records)}")


# ============================================================
#  STUDENT MANAGEMENT
# ============================================================

def view_all_students():
    """Display all registered students."""
    print("\n" + "=" * 55)
    print("  📋  ALL REGISTERED STUDENTS")
    print("=" * 55)
    
    students = get_all_students()
    
    if not students:
        print("\n  📭 No students registered yet.")
        return
    
    print(f"\n  {'#':<4} {'Name':<20} {'Roll':<10} {'Class':<8} {'Phone':<14}")
    print("  " + "-" * 60)
    
    for i, s in enumerate(students, 1):
        print(f"  {i:<4} {s['name']:<20} {s['roll_number']:<10} {s['class_section']:<8} {s['phone_number']:<14}")
    
    print(f"\n  📊 Total students: {len(students)}")


def delete_student_flow():
    """Interactive student deletion."""
    print("\n" + "=" * 55)
    print("  🗑️   DELETE STUDENT")
    print("=" * 55)
    
    roll = input("\n  🔢 Enter roll number to delete: ").strip()
    
    student = get_student_by_roll(roll)
    if not student:
        print(f"\n  ❌ No student found with roll number: {roll.upper()}")
        return
    
    print(f"\n  ⚠️  About to delete: {student['name']} (Roll: {student['roll_number']})")
    confirm = input("  Are you sure? (yes/no): ").strip().lower()
    
    if confirm in ('yes', 'y'):
        success, msg = delete_student(roll)
        print(f"\n  {'✅' if success else '❌'} {msg}")
    else:
        print("\n  ↩️  Deletion cancelled.")


def update_phone_flow():
    """Interactive phone number update."""
    print("\n" + "=" * 55)
    print("  📱  UPDATE PHONE NUMBER")
    print("=" * 55)
    
    roll = input("\n  🔢 Enter roll number: ").strip()
    
    student = get_student_by_roll(roll)
    if not student:
        print(f"\n  ❌ No student found with roll number: {roll.upper()}")
        return
    
    print(f"\n  👤 Student: {student['name']}")
    print(f"  📱 Current phone: {student['phone_number']}")
    
    new_phone = input("  📱 Enter new phone number: ").strip()
    
    success, msg = update_student_phone(roll, new_phone)
    print(f"\n  {'✅' if success else '❌'} {msg}")


# ============================================================
#  MAIN MENU
# ============================================================

def print_banner():
    """Print the application banner."""
    print("\n" + "=" * 55)
    print("  ╔═══════════════════════════════════════════════╗")
    print("  ║     📱  OTP-BASED ATTENDANCE SYSTEM  📱      ║")
    print("  ║         Secure • Fast • Reliable              ║")
    print("  ╚═══════════════════════════════════════════════╝")
    print("=" * 55)


def main_menu():
    """Display main menu and handle user choices."""
    print_banner()
    
    while True:
        print("\n  ┌─────────────────────────────────────┐")
        print("  │          📋  MAIN MENU               │")
        print("  ├─────────────────────────────────────┤")
        print("  │  1. 📱  Mark Attendance (OTP)        │")
        print("  │  2. 📝  Register New Student         │")
        print("  │  3. 👥  View All Students            │")
        print("  │  4. 📊  Today's Attendance           │")
        print("  │  5. 📅  Attendance by Date           │")
        print("  │  6. 👤  Student Attendance Report    │")
        print("  │  7. 📱  Update Phone Number          │")
        print("  │  8. 🗑️   Delete Student              │")
        print("  │  0. 🚪  Exit                         │")
        print("  └─────────────────────────────────────┘")
        
        choice = input("\n  Enter your choice (0-8): ").strip()
        
        if choice == '1':
            otp_attendance_flow()
        elif choice == '2':
            register_student_flow()
        elif choice == '3':
            view_all_students()
        elif choice == '4':
            view_today_attendance()
        elif choice == '5':
            view_attendance_by_date()
        elif choice == '6':
            view_student_report()
        elif choice == '7':
            update_phone_flow()
        elif choice == '8':
            delete_student_flow()
        elif choice == '0':
            print("\n  👋 Thank you for using OTP Attendance System!")
            print("  Goodbye!\n")
            sys.exit(0)
        else:
            print("\n  ❌ Invalid choice. Please enter a number between 0-8.")


if __name__ == "__main__":
    main_menu()