import sqlite3
import os

db_path = "callinggen.db"

if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE calls ADD COLUMN recording_url TEXT")
    print("Successfully added column calls.recording_url")
except sqlite3.OperationalError as e:
    # If the column already exists, this catches it
    print(f"Skipped calls.recording_url: {e}")

conn.commit()
conn.close()
print("Migration completed successfully.")
