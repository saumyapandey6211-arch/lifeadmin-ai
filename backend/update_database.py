import sqlite3

connection = sqlite3.connect("lifeadmin.db")

cursor = connection.cursor()

cursor.execute("""
ALTER TABLE tasks
ADD COLUMN status TEXT DEFAULT 'pending'
""")

connection.commit()

connection.close()

print("Database updated successfully!")