from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('ration_shop.db')
    conn.row_factory = sqlite3.Row
    return conn

# Homepage
@app.route('/')
def index():
    conn = get_db_connection()
    districts = conn.execute('SELECT * FROM districts ORDER BY district_name').fetchall()
    conn.close()
    return render_template('index.html', districts=districts)

# Get shops by district
@app.route('/shops/<int:district_id>')
def shops(district_id):
    conn = get_db_connection()
    shops = conn.execute('''
        SELECT s.*, d.district_name, u.name as manager_name, u.contact as manager_contact
        FROM shops s 
        LEFT JOIN districts d ON s.district_id = d.district_id 
        LEFT JOIN users u ON s.manager_id = u.user_id
        WHERE s.district_id = ?
    ''', (district_id,)).fetchall()
    
    district = conn.execute('SELECT district_name FROM districts WHERE district_id = ?', (district_id,)).fetchone()
    conn.close()
    
    return render_template('shops.html', shops=shops, district=district)

# Get products for a shop
@app.route('/products/<int:shop_id>')
def products(shop_id):
    conn = get_db_connection()
    
    # Get shop details
    shop = conn.execute('''
        SELECT s.*, d.district_name, u.name as manager_name, u.email as manager_email, u.contact as manager_contact
        FROM shops s 
        LEFT JOIN districts d ON s.district_id = d.district_id 
        LEFT JOIN users u ON s.manager_id = u.user_id
        WHERE s.shop_id = ?
    ''', (shop_id,)).fetchone()
    
    # Get stock details
    stock = conn.execute('''
        SELECT p.product_name, st.quantity, st.last_updated
        FROM stock st
        JOIN products p ON st.product_id = p.product_id
        WHERE st.shop_id = ?
        ORDER BY p.product_name
    ''', (shop_id,)).fetchall()
    
    conn.close()
    
    return render_template('products.html', shop=shop, stock=stock)

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['name'] = user['name']
            
            if user['role'] == 'system_admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('branch_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

# Forgot password page
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        # In a real application, you would send a password reset email here
        # For this demo, we'll just show a success message
        flash('If that email exists in our system, a password reset link has been sent.', 'info')
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Admin Dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'system_admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get counts for dashboard
    district_count = conn.execute('SELECT COUNT(*) FROM districts').fetchone()[0]
    shop_count = conn.execute('SELECT COUNT(*) FROM shops').fetchone()[0]
    product_count = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    manager_count = conn.execute('SELECT COUNT(*) FROM users WHERE role = "branch_manager"').fetchone()[0]
    
    # Get districts for the form
    districts = conn.execute('SELECT * FROM districts ORDER BY district_name').fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                          district_count=district_count, 
                          shop_count=shop_count,
                          product_count=product_count,
                          manager_count=manager_count,
                          districts=districts)

# Branch Manager Dashboard
@app.route('/branch/dashboard')
def branch_dashboard():
    if 'user_id' not in session or session['role'] != 'branch_manager':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get shop details for the manager
    shop = conn.execute('''
        SELECT s.*, d.district_name 
        FROM shops s 
        JOIN districts d ON s.district_id = d.district_id 
        WHERE s.manager_id = ?
    ''', (session['user_id'],)).fetchone()
    
    # Get stock details
    stock = conn.execute('''
        SELECT p.product_id, p.product_name, st.quantity, st.last_updated
        FROM stock st
        JOIN products p ON st.product_id = p.product_id
        WHERE st.shop_id = ?
        ORDER BY p.product_name
    ''', (shop['shop_id'],)).fetchall()
    
    # Get all available products that are NOT in this shop's stock
    available_products = conn.execute('''
        SELECT p.* 
        FROM products p 
        WHERE p.product_id NOT IN (
            SELECT product_id FROM stock WHERE shop_id = ?
        )
        ORDER BY p.product_name
    ''', (shop['shop_id'],)).fetchall()
    
    conn.close()
    
    return render_template('branch_dashboard.html', shop=shop, stock=stock, available_products=available_products)

# Profile page
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form['contact']
        
        conn.execute('''
            UPDATE users 
            SET name = ?, email = ?, contact = ?
            WHERE user_id = ?
        ''', (name, email, contact, session['user_id']))
        conn.commit()
        
        session['name'] = name
        flash('Profile updated successfully', 'success')
    
    user = conn.execute('SELECT * FROM users WHERE user_id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    return render_template('profile.html', user=user)

# Add new district (Admin only)
@app.route('/admin/add_district', methods=['POST'])
def add_district():
    if 'user_id' not in session or session['role'] != 'system_admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    district_name = request.form['district_name']
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO districts (district_name) VALUES (?)', (district_name,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'District added successfully'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'District already exists'})

# Add new branch (Admin only)
@app.route('/admin/add_branch', methods=['POST'])
def add_branch():
    if 'user_id' not in session or session['role'] != 'system_admin':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    shop_name = request.form['shop_name']
    district_id = request.form['district_id']
    address = request.form['address']
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO shops (shop_name, district_id, address) VALUES (?, ?, ?)', 
                     (shop_name, district_id, address))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Branch added successfully'})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

# Hire/assign manager (Admin only)
@app.route('/admin/hire_manager', methods=['GET', 'POST'])
def hire_manager():
    if 'user_id' not in session or session['role'] != 'system_admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        name = request.form['name']
        contact = request.form['contact']
        shop_id = request.form['shop_id']
        
        try:
            # First insert the user
            conn.execute('''
                INSERT INTO users (username, email, password, role, shop_id, name, contact)
                VALUES (?, ?, ?, 'branch_manager', ?, ?, ?)
            ''', (username, email, password, shop_id, name, contact))
            
            # Get the last inserted user ID
            user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            
            # Update shop with manager ID
            conn.execute('UPDATE shops SET manager_id = ? WHERE shop_id = ?', (user_id, shop_id))
            
            conn.commit()
            flash('Manager hired and assigned successfully', 'success')
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'danger')
        except sqlite3.Error as e:
            flash(f'Error: {str(e)}', 'danger')
    
    shops = conn.execute('''
        SELECT s.*, d.district_name 
        FROM shops s 
        JOIN districts d ON s.district_id = d.district_id 
        WHERE s.manager_id IS NULL
    ''').fetchall()
    
    conn.close()
    
    return render_template('hire_manager.html', shops=shops)

# Update stock quantity (Branch Manager only)
@app.route('/branch/update_stock', methods=['POST'])
def update_stock():
    if 'user_id' not in session or session['role'] != 'branch_manager':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity')
    
    if not product_id or not quantity:
        return jsonify({'success': False, 'message': 'Missing required fields'})
    
    try:
        quantity = float(quantity)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid quantity value'})
    
    conn = get_db_connection()
    
    try:
        # Get shop ID for the manager
        shop = conn.execute('SELECT shop_id FROM shops WHERE manager_id = ?', (session['user_id'],)).fetchone()
        
        if not shop:
            conn.close()
            return jsonify({'success': False, 'message': 'Shop not found'})
        
        shop_id = shop['shop_id']
        
        # Check if stock record exists
        existing = conn.execute('SELECT * FROM stock WHERE shop_id = ? AND product_id = ?', 
                               (shop_id, product_id)).fetchone()
        
        if existing:
            conn.execute('''
                UPDATE stock 
                SET quantity = ?, last_updated = datetime('now')
                WHERE shop_id = ? AND product_id = ?
            ''', (quantity, shop_id, product_id))
        else:
            conn.execute('''
                INSERT INTO stock (shop_id, product_id, quantity)
                VALUES (?, ?, ?)
            ''', (shop_id, product_id, quantity))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Stock updated successfully'})
    
    except sqlite3.Error as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'})

# Add product to shop (Branch Manager only)
@app.route('/branch/add_product', methods=['POST'])
def add_product_to_shop():
    if 'user_id' not in session or session['role'] != 'branch_manager':
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity', 0)
    
    if not product_id:
        return jsonify({'success': False, 'message': 'Product selection is required'})
    
    try:
        quantity = float(quantity)
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid quantity value'})
    
    conn = get_db_connection()
    
    try:
        # Get shop ID for the manager
        shop = conn.execute('SELECT shop_id FROM shops WHERE manager_id = ?', (session['user_id'],)).fetchone()
        
        if not shop:
            conn.close()
            return jsonify({'success': False, 'message': 'Shop not found'})
        
        shop_id = shop['shop_id']
        
        # Check if product already exists in shop stock
        existing = conn.execute('SELECT * FROM stock WHERE shop_id = ? AND product_id = ?', 
                               (shop_id, product_id)).fetchone()
        
        if existing:
            conn.close()
            return jsonify({'success': False, 'message': 'Product already exists in your shop inventory'})
        
        # Add product to shop stock
        conn.execute('''
            INSERT INTO stock (shop_id, product_id, quantity)
            VALUES (?, ?, ?)
        ''', (shop_id, product_id, quantity))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Product added to shop successfully'})
    
    except sqlite3.Error as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'})

# View all branches and stock status (Admin only)
@app.route('/admin/view_branches')
def view_branches():
    if 'user_id' not in session or session['role'] != 'system_admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get all shops with their district and manager info
    shops = conn.execute('''
        SELECT s.*, d.district_name, u.name as manager_name, u.contact as manager_contact
        FROM shops s 
        LEFT JOIN districts d ON s.district_id = d.district_id 
        LEFT JOIN users u ON s.manager_id = u.user_id
        ORDER BY d.district_name, s.shop_name
    ''').fetchall()
    
    conn.close()
    
    return render_template('view_branches.html', shops=shops)

# View branch details and stock (Admin only)
@app.route('/admin/branch/<int:shop_id>')
def admin_branch_details(shop_id):
    if 'user_id' not in session or session['role'] != 'system_admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get shop details
    shop = conn.execute('''
        SELECT s.*, d.district_name, u.name as manager_name, u.email as manager_email, u.contact as manager_contact
        FROM shops s 
        LEFT JOIN districts d ON s.district_id = d.district_id 
        LEFT JOIN users u ON s.manager_id = u.user_id
        WHERE s.shop_id = ?
    ''', (shop_id,)).fetchone()
    
    # Get stock details
    stock = conn.execute('''
        SELECT p.product_name, st.quantity, st.last_updated
        FROM stock st
        JOIN products p ON st.product_id = p.product_id
        WHERE st.shop_id = ?
        ORDER BY p.product_name
    ''', (shop_id,)).fetchall()
    
    conn.close()
    
    return render_template('admin_branch_details.html', shop=shop, stock=stock)

# Get all products for AJAX requests
@app.route('/api/products')
def api_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products ORDER BY product_name').fetchall()
    conn.close()
    
    products_list = [{'product_id': p['product_id'], 'product_name': p['product_name']} for p in products]
    return jsonify(products_list)

# Get shop stock for AJAX requests
@app.route('/api/shop/<int:shop_id>/stock')
def api_shop_stock(shop_id):
    conn = get_db_connection()
    
    stock = conn.execute('''
        SELECT p.product_id, p.product_name, st.quantity, st.last_updated
        FROM stock st
        JOIN products p ON st.product_id = p.product_id
        WHERE st.shop_id = ?
        ORDER BY p.product_name
    ''', (shop_id,)).fetchall()
    
    conn.close()
    
    stock_list = [{
        'product_id': s['product_id'],
        'product_name': s['product_name'],
        'quantity': s['quantity'],
        'last_updated': s['last_updated']
    } for s in stock]
    
    return jsonify(stock_list)

if __name__ == '__main__':
    app.run(debug=True)