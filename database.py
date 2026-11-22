import sqlite3
import os
from typing import Any, List, Optional, Tuple, Dict

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'students.db')

def get_db_connection() -> sqlite3.Connection:
    """Creates a database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def score_to_grade(score: Optional[float]) -> Tuple[str, float]:
    """Converts a numerical score (0-100) to Letter Grade and GPA points."""
    if score is None:
        return "-", 0.0
    if score >= 90:
        return "A+", 4.0
    elif score >= 80:
        return "A", 3.7
    elif score >= 70:
        return "B", 3.0
    elif score >= 60:
        return "C", 2.0
    elif score >= 50:
        return "D", 1.0
    else:
        return "F", 0.0

def init_db():
    """Initializes tables in the SQLite database if they don't already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT UNIQUE NOT NULL,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        gender TEXT,
        dob TEXT,
        department TEXT NOT NULL,
        year INTEGER NOT NULL DEFAULT 1,
        address TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        credits INTEGER NOT NULL DEFAULT 3,
        semester TEXT NOT NULL,
        instructor TEXT,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        semester TEXT NOT NULL,
        score REAL DEFAULT NULL,
        grade TEXT DEFAULT '-',
        status TEXT DEFAULT 'Enrolled',
        enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
        UNIQUE(student_id, course_id, semester)
    );

    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
        UNIQUE(student_id, course_id, date)
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        student_id INTEGER DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE SET NULL
    );

    CREATE INDEX IF NOT EXISTS idx_student_roll ON students(roll_no);
    CREATE INDEX IF NOT EXISTS idx_student_dept ON students(department);
    CREATE INDEX IF NOT EXISTS idx_course_code ON courses(code);
    CREATE INDEX IF NOT EXISTS idx_enrollment_student ON enrollments(student_id);
    CREATE INDEX IF NOT EXISTS idx_user_username ON users(username);
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully at:", DB_PATH)
