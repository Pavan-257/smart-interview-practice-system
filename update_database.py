import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

try:
    cursor.execute("""
        ALTER TABLE users
        ADD COLUMN profile_picture TEXT
        DEFAULT 'default.png'
    """)
    print("✅ Profile picture column added successfully!")
except Exception as e:
    print("Info:", e)

conn.commit()
conn.close()