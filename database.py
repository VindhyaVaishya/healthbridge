
import sqlite3

def get_db_connection():
    conn = sqlite3.connect("healthbridge.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    conn = get_db_connection()

    # PATIENT TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT UNIQUE,
            name TEXT NOT NULL,
            dob TEXT NOT NULL,
            gender TEXT NOT NULL,
            mobile TEXT UNIQUE NOT NULL,
            email TEXT,
            address TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # DOCTOR TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            specialization TEXT,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    from werkzeug.security import generate_password_hash

    conn.execute("""
        INSERT OR IGNORE INTO doctors
        (doctor_id, full_name, specialization, password)
        VALUES (?, ?, ?, ?)
    """, (
        "HB-DOC-001",
        "Dr. Asha Sharma",
        None,
        generate_password_hash("Doctor@123")
    ))

    # APPOINTMENTS TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            doctor_id TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            token_number INTEGER NOT NULL,
            status TEXT DEFAULT 'Waiting',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add appointment time to existing database
    columns = [
        row["name"] for row in
        conn.execute("PRAGMA table_info(appointments)").fetchall()
    ]

    if "appointment_time" not in columns:
        conn.execute("""
            ALTER TABLE appointments
            ADD COLUMN appointment_time TEXT
        """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS doctor_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id TEXT NOT NULL,
            slot_date TEXT NOT NULL,
            slot_time TEXT NOT NULL,
            status TEXT DEFAULT 'Available',
            FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id),
            UNIQUE (doctor_id, slot_date, slot_time)
        )
    """)

    # STAFF TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            mobile TEXT UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # DEMO STAFF ACCOUNT
    conn.execute("""
        INSERT OR IGNORE INTO staff
        (staff_id, full_name, role, mobile, password)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "HB-STF-001",
        "Priya Verma",
        "Nurse",
        "9876543210",
        generate_password_hash("Staff@123")
    ))

    conn.execute("""
        CREATE TABLE IF NOT EXISTS staff_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id TEXT NOT NULL,
            staff_role TEXT NOT NULL,
            message TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # DEMO BILLING STAFF ACCOUNT
    conn.execute("""
        INSERT OR IGNORE INTO staff
        (staff_id, full_name, role, mobile, password)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "HB-STF-002",
        "Rahul Verma",
        "Billing Staff",
        "9876543211",
        generate_password_hash("Billing@123")
    ))

    # STAFF ATTENDANCE TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS staff_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id TEXT NOT NULL,
            attendance_date TEXT NOT NULL,
            check_in TEXT,
            status TEXT DEFAULT 'Present',
            UNIQUE (staff_id, attendance_date)
        )
    """)

    # BILLING TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            staff_id TEXT NOT NULL,
            consultation_charge REAL DEFAULT 0,
            lab_charge REAL DEFAULT 0,
            other_charge REAL DEFAULT 0,
            total_amount REAL NOT NULL,
            payment_status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # DOCTOR ATTENDANCE TABLE
    conn.execute("""
        CREATE TABLE IF NOT EXISTS doctor_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id TEXT NOT NULL,
            attendance_date TEXT NOT NULL,
            check_in TEXT,
            status TEXT DEFAULT 'Present',
            UNIQUE (doctor_id, attendance_date)
        )
    """)

    conn.commit()
    conn.close()
