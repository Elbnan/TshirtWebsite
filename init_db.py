import sqlite3

conn = sqlite3.connect('tshirt.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    password TEXT,
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS TShirts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price REAL,
    description TEXT,
    sizes TEXT,
    payment_method TEXT,
    image_url TEXT,
    available_colors TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tshirt_id INTEGER,
    customer_name TEXT,
    phone TEXT,
    address TEXT,
    size TEXT,
    order_date TIMESTAMP,
    is_notified INTEGER DEFAULT 0,
    seen_by_admin INTEGER DEFAULT 0,
    color TEXT,
    quantity INTEGER,
    email TEXT
)
''')

conn.commit()
conn.close()
print("Database and tables created.")
