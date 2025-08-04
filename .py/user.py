import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'member.db')

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def user():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    user()
