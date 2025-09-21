import sqlite3
from werkzeug.security import generate_password_hash

def init_database():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('ration_shop.db')
    cursor = conn.cursor()
    
    # Drop tables if they exist (for clean setup)
    cursor.execute('DROP TABLE IF EXISTS stock')
    cursor.execute('DROP TABLE IF EXISTS products')
    cursor.execute('DROP TABLE IF EXISTS shops')
    cursor.execute('DROP TABLE IF EXISTS users')
    cursor.execute('DROP TABLE IF EXISTS districts')
    
    # Create districts table
    cursor.execute('''
    CREATE TABLE districts (
        district_id INTEGER PRIMARY KEY AUTOINCREMENT,
        district_name TEXT NOT NULL UNIQUE
    )
    ''')
    
    # Create users table
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
    
    # Create shops table
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
    
    # Create products table
    cursor.execute('''
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL UNIQUE
    )
    ''')
    
    # Create stock table
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
    
    # Insert sample districts
    districts = ['Chennai', 'Coimbatore', 'Madurai']
    for district in districts:
        cursor.execute("INSERT INTO districts (district_name) VALUES (?)", (district,))
    
    # Insert sample products
    products = ['Rice', 'Wheat', 'Sugar', 'Oil', 'Salt']
    for product in products:
        cursor.execute("INSERT INTO products (product_name) VALUES (?)", (product,))
    
    # Insert default admin user (password: admin123)
    admin_password = generate_password_hash('admin123')
    cursor.execute("INSERT INTO users (username, email, password, role, name, contact) VALUES (?, ?, ?, ?, ?, ?)",
                   ('admin', 'admin@rationshop.com', admin_password, 'system_admin', 'System Administrator', '9876543210'))
    
    # Insert sample shops
    shops_data = [
        ('Anna Nagar Ration Shop', 1, '1st Main Road, Anna Nagar'),
        ('T Nagar Ration Shop', 1, 'North Usman Road, T Nagar'),
        ('RS Puram Ration Shop', 2, 'DB Road, RS Puram')
    ]
    
    for shop_name, district_id, address in shops_data:
        cursor.execute("INSERT INTO shops (shop_name, district_id, address) VALUES (?, ?, ?)",
                       (shop_name, district_id, address))
    
    # Insert sample branch manager (password: manager123)
    manager_password = generate_password_hash('manager123')
    cursor.execute("INSERT INTO users (username, email, password, role, shop_id, name, contact) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   ('manager1', 'manager1@rationshop.com', manager_password, 'branch_manager', 1, 'Ramesh Kumar', '8765432109'))
    
    # Update shop with manager ID
    cursor.execute("UPDATE shops SET manager_id = 2 WHERE shop_id = 1")
    
    # Insert sample stock data
    stock_data = [
        (1, 1, 500),  # Shop 1, Rice, 500kg
        (1, 2, 300),  # Shop 1, Wheat, 300kg
        (1, 3, 200),  # Shop 1, Sugar, 200kg
        (1, 4, 150),  # Shop 1, Oil, 150kg
        (1, 5, 100),  # Shop 1, Salt, 100kg
        (2, 1, 400),  # Shop 2, Rice, 400kg
        (2, 2, 250),  # Shop 2, Wheat, 250kg
        (2, 3, 150),  # Shop 2, Sugar, 150kg
        (3, 1, 600),  # Shop 3, Rice, 600kg
        (3, 4, 200),  # Shop 3, Oil, 200kg
    ]
    
    for shop_id, product_id, quantity in stock_data:
        cursor.execute("INSERT INTO stock (shop_id, product_id, quantity) VALUES (?, ?, ?)",
                       (shop_id, product_id, quantity))
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database initialized successfully with sample data!")

if __name__ == '__main__':
    init_database()