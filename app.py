from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from zoneinfo import ZoneInfo


app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Admin credentials
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': generate_password_hash('1234')
}

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Create tables with REAL type for decimal points
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ticket_number TEXT,
                  fuel_type TEXT,
                  amount REAL,
                  points_earned REAL,
                  date TEXT,
                  customer_id INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS customers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  registration_date TEXT,
                  total_points REAL DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS redemptions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  customer_id INTEGER,
                  reward_name TEXT,
                  points_redeemed REAL,
                  date TEXT)''')
    
    conn.commit()
    conn.close()

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.context_processor
def inject_stats():
    stats = {
        'total_transactions': 0,
        'total_sales': 0,
        'total_customers': 0,
        'ADMIN_CREDENTIALS': ADMIN_CREDENTIALS
    }
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM transactions")
        stats['total_transactions'] = "{:,}".format(c.fetchone()[0] or 0)
        c.execute("SELECT SUM(amount) FROM transactions")
        total_sales = c.fetchone()[0] or 0
        stats['total_sales'] = "{:,.2f}".format(total_sales)
        c.execute("SELECT COUNT(*) FROM customers")
        stats['total_customers'] = "{:,}".format(c.fetchone()[0] or 0)
    except:
        pass
    finally:
        conn.close()
    return stats

@app.route('/')
def login():
    session.clear()
    return render_template('index.html')

@app.route('/auth', methods=['POST'])
def auth():
    username = request.form['username']
    password = request.form['password']
    
    if username == ADMIN_CREDENTIALS['username'] and check_password_hash(ADMIN_CREDENTIALS['password'], password):
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid credentials', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('admin.html')

@app.route('/customer-search')
@login_required
def customer_search():
    query = request.args.get('q', '').lower()
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    try:
        # Search by ID if query starts with number
        if query.isdigit():
            c.execute("""
                SELECT id, name, registration_date, total_points 
                FROM customers 
                WHERE id = ?
                ORDER BY id DESC
                LIMIT 10
            """, (query,))
        else:
            # Search by partial match to customer ID
            search_term = f"%{query}%"
            c.execute("""
                SELECT id, name, registration_date, total_points 
                FROM customers 
                WHERE name LIKE ? OR id LIKE ?
                ORDER BY id DESC
                LIMIT 10
            """, (search_term, search_term))
        
        customers = [{
            'id': row[0],
            'name': row[1],
            'registration_date': row[2],
            'points': row[3]
        } for row in c.fetchall()]
        
    except Exception as e:
        customers = []
        print(f"Search error: {str(e)}")
    finally:
        conn.close()
    
    return jsonify(customers)

@app.route('/transactions', methods=['GET', 'POST'])
@login_required
def transactions():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        fuel_type = request.form['fuel_type']
        amount = float(request.form['amount'])
        customer_id = request.form.get('customer_id')
        
        if not customer_id:
            flash('Customer selection is required', 'error')
            return redirect(url_for('transactions'))
        
        # Calculate points as 1% of amount (₱100 = 1.00 point)
        points_earned = round(amount * 0.01, 2)
        date = datetime.now(ZoneInfo('Asia/Manila')).strftime('%Y-%m-%d %H:%M:%S')
        transaction_id = f"TRX-{customer_id}-{datetime.now(ZoneInfo("Asia/Manila")).strftime('%Y%m%d%H%M%S')}"
        
        try:
            c.execute("""INSERT INTO transactions 
                        (ticket_number, fuel_type, amount, points_earned, date, customer_id) 
                        VALUES (?, ?, ?, ?, ?, ?)""",
                     (transaction_id, fuel_type, amount, points_earned, date, customer_id))
            
            c.execute("UPDATE customers SET total_points = total_points + ? WHERE id = ?",
                     (points_earned, customer_id))
            
            conn.commit()
            flash(f'Transaction recorded! ₱{amount:.2f} → {points_earned:.2f} points earned', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            conn.close()
        return redirect(url_for('transactions'))
    
    c.execute('''SELECT t.*, c.name 
                FROM transactions t
                LEFT JOIN customers c ON t.customer_id = c.id
                ORDER BY t.date DESC''')
    transactions = c.fetchall()
    conn.close()
    return render_template('transaction.html', transactions=transactions)

@app.route('/update-transaction', methods=['POST'])
@login_required
def update_transaction():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    try:
        transaction_id = request.form['id']
        new_amount = float(request.form['amount'])
        
        # Recalculate points based on new amount
        new_points = round(new_amount * 0.01, 2)
        
        # Get original transaction data
        c.execute("SELECT points_earned, customer_id FROM transactions WHERE id = ?", (transaction_id,))
        old_points, customer_id = c.fetchone()
        points_diff = new_points - old_points
        
        # Update transaction
        c.execute("UPDATE transactions SET amount = ?, points_earned = ? WHERE id = ?",
                 (new_amount, new_points, transaction_id))
        
        # Update customer's points
        if customer_id:
            c.execute("UPDATE customers SET total_points = total_points + ? WHERE id = ?",
                     (points_diff, customer_id))
        
        conn.commit()
        return jsonify({'success': True, 'new_points': new_points})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/customers', methods=['GET', 'POST'])
@login_required
def customers():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        c.execute("SELECT MAX(id) FROM customers")
        max_id = c.fetchone()[0]
        new_id = 1 if max_id is None else max_id + 1
        
        registration_date = datetime.now(ZoneInfo("Asia/Manila")).strftime('%Y-%m-%d')
        c.execute("INSERT INTO customers (id, name, registration_date) VALUES (?, ?, ?)",
                 (new_id, f"Customer {new_id}", registration_date))
        conn.commit()
        flash(f'Customer registered successfully with ID: CUST-{new_id}', 'success')
        return redirect(url_for('customers'))
    
    search = request.args.get('search', '')
    query = "SELECT id, name, registration_date, total_points FROM customers"
    if search:
        if search.upper().startswith('CUST-'):
            cust_id = search.upper().replace('CUST-', '')
            query += f" WHERE id = '{cust_id}'"
        else:
            query += f" WHERE name LIKE '%{search}%'"
    query += " ORDER BY id DESC"
    
    c.execute(query)
    customers = c.fetchall()
    conn.close()
    return render_template('customer.html', customers=customers)

@app.route('/redeem', methods=['GET', 'POST'])
@login_required
def redeem():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        points_to_redeem = float(request.form['points_to_redeem'])
        
        # Get customer's current points
        c.execute("SELECT total_points FROM customers WHERE id = ?", (customer_id,))
        customer_points = c.fetchone()
        
        if not customer_points:
            flash('Customer not found', 'error')
            return redirect(url_for('redeem'))
        
        if customer_points[0] < points_to_redeem:
            flash('Not enough points for this redemption', 'error')
            return redirect(url_for('redeem'))
        
        if points_to_redeem <= 0:
            flash('Please enter a positive number of points', 'error')
            return redirect(url_for('redeem'))
        
        date = datetime.now(ZoneInfo("Asia/Manila")).strftime('%Y-%m-%d %H:%M:%S')
        peso_value = round(points_to_redeem / 0.01, 2)
        c.execute("""INSERT INTO redemptions 
                    (customer_id, reward_name, points_redeemed, date) 
                    VALUES (?, ?, ?, ?)""",
                 (customer_id, f"{peso_value:.2f}₱ fuel refill", points_to_redeem, date))
        
        c.execute("UPDATE customers SET total_points = total_points - ? WHERE id = ?",
                 (points_to_redeem, customer_id))
        
        conn.commit()
        conn.close()
        flash(f'Successfully redeemed {points_to_redeem:.2f} points for {peso_value:.2f}₱ fuel!', 'success')
        return redirect(url_for('redeem'))
    
    c.execute("SELECT id, name, total_points FROM customers")
    customers = c.fetchall()
    
    c.execute('''SELECT r.date, r.customer_id, r.reward_name, r.points_redeemed, c.name 
                FROM redemptions r
                JOIN customers c ON r.customer_id = c.id
                ORDER BY r.date DESC''')
    redemptions = c.fetchall()
    
    conn.close()
    return render_template('redeem.html',
                         customers=customers,
                         redemptions=redemptions)

@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    username = data.get('username')
    new_password = data.get('new_password')
    
    if not username or not new_password:
        return jsonify({'success': False, 'message': 'Username and password are required'})
    
    if len(new_password) < 4:
        return jsonify({'success': False, 'message': 'Password must be at least 4 characters'})
    
    if username != ADMIN_CREDENTIALS['username']:
        return jsonify({'success': False, 'message': 'Username not found'})
    
    ADMIN_CREDENTIALS['password'] = generate_password_hash(new_password)
    return jsonify({'success': True, 'message': 'Password reset successfully'})

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json()
    new_username = data.get('username')
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not check_password_hash(ADMIN_CREDENTIALS['password'], current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'})
    
    if new_username != ADMIN_CREDENTIALS['username']:
        ADMIN_CREDENTIALS['username'] = new_username
    
    if new_password:
        if len(new_password) < 4:
            return jsonify({'success': False, 'message': 'Password must be at least 4 characters'})
        ADMIN_CREDENTIALS['password'] = generate_password_hash(new_password)
    
    return jsonify({
        'success': True,
        'message': 'Profile updated successfully',
        'new_username': ADMIN_CREDENTIALS['username']
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)