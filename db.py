import sqlite3


def get_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_table():

    conn = get_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        mobile TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        age INTEGER NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        profile_picture TEXT DEFAULT 'default.png'
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Interview Results table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interview_results(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        interview_type TEXT,
        score TEXT,
        feedback TEXT,
        interview_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    from werkzeug.security import generate_password_hash

    cursor.execute("SELECT * FROM admin")

    if cursor.fetchone() is None:

        cursor.execute("""
        INSERT INTO admin(username,password)
        VALUES(?,?)
        """,(
            "admin",
             generate_password_hash("admin123")
        ))
    conn.commit()
    conn.close()


def save_result(username, interview_type, score, feedback):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO interview_results
    (username, interview_type, score, feedback)
    VALUES (?, ?, ?, ?)
    """, (username, interview_type, score, feedback))

    conn.commit()
    conn.close()