import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def get_db_connection():
    conn = sqlite3.connect('ration_shop.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect('ration_shop.db')
    cursor = conn.cursor()
    
    # Drop tables if they exist (for development)
    cursor.execute('DROP TABLE IF EXISTS stock')
    cursor.execute('DROP TABLE IF EXISTS products')
    cursor.execute('DROP TABLE IF EXISTS shops')
    cursor.execute('DROP TABLE IF EXISTS users')
    cursor.execute('DROP TABLE IF EXISTS districts')
    
    # Create tables
    cursor.execute('''
    CREATE TABLE districts (
        district_id INTEGER PRIMARY KEY AUTOINCREMENT,
        district_name TEXT NOT NULL UNIQUE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('system_admin', 'branch_manager')),
        shop_id INTEGER,
        name TEXT NOT NULL,
        contact TEXT NOT NULL,
        FOREIGN KEY (shop_id) REFERENCES shops (shop_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE shops (
        shop_id INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_name TEXT NOT NULL,
        district_id INTEGER NOT NULL,
        manager_id INTEGER,
        address TEXT,
        FOREIGN KEY (district_id) REFERENCES districts (district_id),
        FOREIGN KEY (manager_id) REFERENCES users (user_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL UNIQUE
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE stock (
        stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
        shop_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity REAL NOT NULL DEFAULT 0,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (shop_id) REFERENCES shops (shop_id),
        FOREIGN KEY (product_id) REFERENCES products (product_id),
        UNIQUE(shop_id, product_id)
    )
    ''')
    
    # Insert sample data
    cursor.execute("INSERT INTO districts (district_name) VALUES ('Chennai'), ('Coimbatore'), ('Madurai')")
    
    cursor.execute("INSERT INTO products (product_name) VALUES ('Rice'), ('Wheat'), ('Sugar'), ('Oil'), ('Salt')")
    
    # Insert default admin user (password: admin123)
    admin_password = generate_password_hash('admin123')
    cursor.execute("INSERT INTO users (username, email, password, role, name, contact) VALUES (?, ?, ?, ?, ?, ?)",
                   ('admin', 'admin@rationshop.com', admin_password, 'system_admin', 'System Administrator', '9876543210'))
    
    # Insert sample shops
    cursor.execute("INSERT INTO shops (shop_name, district_id, address) VALUES (?, ?, ?)",
                   ('Anna Nagar Ration Shop', 1, '1st Main Road, Anna Nagar'))
    cursor.execute("INSERT INTO shops (shop_name, district_id, address) VALUES (?, ?, ?)",
                   ('T Nagar Ration Shop', 1, 'North Usman Road, T Nagar'))
    cursor.execute("INSERT INTO shops (shop_name, district_id, address) VALUES (?, ?, ?)",
                   ('RS Puram Ration Shop', 2, 'DB Road, RS Puram'))
    
    # Insert sample branch manager (password: manager123)
    manager_password = generate_password_hash('manager123')
    cursor.execute("INSERT INTO users (username, email, password, role, shop_id, name, contact) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   ('manager1', 'manager1@rationshop.com', manager_password, 'branch_manager', 1, 'Ramesh Kumar', '8765432109'))
    
    # Update shop with manager ID
    cursor.execute("UPDATE shops SET manager_id = 2 WHERE shop_id = 1")
    
    # Insert sample stock data
    cursor.execute("INSERT INTO stock (shop_id, product_id, quantity) VALUES (1, 1, 500)")
    cursor.execute("INSERT INTO stock (shop_id, product_id, quantity) VALUES (1, 2, 300)")
    cursor.execute("INSERT INTO stock (shop_id, product_id, quantity) VALUES (1, 3, 200)")
    cursor.execute("INSERT INTO stock (shop_id, product_id, quantity) VALUES (1, 4, 150)")
    cursor.execute("INSERT INTO stock (shop_id, product_id, quantity) VALUES (1, 5, 100)")
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()