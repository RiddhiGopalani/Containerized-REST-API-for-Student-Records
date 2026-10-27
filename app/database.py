"""SQLite helper functions for storing student records."""

import os
import sqlite3

# The database file location can be changed with the DB_PATH environment variable.
# Inside Docker this points to /app/data/students.db, which is backed by a volume.
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "students.db")

SAMPLE_STUDENTS = [
    {"name": "Aarav Sharma", "roll_no": "CS101", "department": "Computer Engineering", "email": "aarav.sharma@example.com"},
    {"name": "Sneha Patil", "roll_no": "IT102", "department": "Information Technology", "email": "sneha.patil@example.com"},
    {"name": "Rohan Kulkarni", "roll_no": "EC103", "department": "Electronics", "email": "rohan.kulkarni@example.com"},
]


def get_db_path():
    return os.getenv("DB_PATH", DEFAULT_DB_PATH)


def get_connection():
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    return conn


def init_db():
    """Create the students table if it does not exist and add sample data once."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                roll_no TEXT NOT NULL UNIQUE,
                department TEXT NOT NULL,
                email TEXT NOT NULL
            )
            """
        )
        seed = os.getenv("SEED_SAMPLE_DATA", "true").lower() == "true"
        count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if seed and count == 0:
            conn.executemany(
                "INSERT INTO students (name, roll_no, department, email) "
                "VALUES (:name, :roll_no, :department, :email)",
                SAMPLE_STUDENTS,
            )


def fetch_all_students():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM students ORDER BY id").fetchall()
    return [dict(row) for row in rows]


def fetch_student(student_id):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    return dict(row) if row else None


def insert_student(student):
    """Insert a student and return the new record. Raises sqlite3.IntegrityError on duplicate roll_no."""
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO students (name, roll_no, department, email) "
            "VALUES (:name, :roll_no, :department, :email)",
            student,
        )
        new_id = cursor.lastrowid
    return fetch_student(new_id)


def update_student(student_id, student):
    """Update a student and return the updated record, or None if the ID does not exist."""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE students SET name = :name, roll_no = :roll_no, "
            "department = :department, email = :email WHERE id = :id",
            {**student, "id": student_id},
        )
        if cursor.rowcount == 0:
            return None
    return fetch_student(student_id)
