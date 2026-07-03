import sqlite3

conn = sqlite3.connect("database.db")

cursor = conn.cursor()

cursor.execute("""
SELECT
name,
mobile,
email,
username,
password
FROM users
""")

rows = cursor.fetchall()

print("\n------ USERS IN DATABASE ------\n")

for row in rows:
    print(row)

conn.close()