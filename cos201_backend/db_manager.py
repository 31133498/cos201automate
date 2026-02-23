import sqlite3

DB_PATH = "tokens.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_string TEXT UNIQUE NOT NULL,
            is_used BOOLEAN DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def insert_token(token_string):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tokens (token_string, is_used) VALUES (?, 0)", (token_string,))
    conn.commit()
    conn.close()

def validate_token(token_string):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tokens WHERE token_string = ? AND is_used = 0", (token_string,))
    result = cursor.fetchone()
    
    if result:
        cursor.execute("UPDATE tokens SET is_used = 1 WHERE id = ?", (result[0],))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False
