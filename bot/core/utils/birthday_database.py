import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bot_database.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS birthday_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    date_sent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

def has_sent_birthday_message(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = datetime.now().strftime('%m-%d')

    cursor.execute('''
    SELECT 1 FROM birthday_messages WHERE name = ? AND date_sent = ?
    ''', (name, today))

    result = cursor.fetchone()
    conn.close()

    return result is not None

def mark_birthday_sent(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = datetime.now().strftime('%m-%d')

    cursor.execute('''
    INSERT INTO birthday_messages (name, date_sent)
    VALUES (?, ?)
    ''', (name, today))

    conn.commit()
    conn.close()

conn.commit()
conn.close()