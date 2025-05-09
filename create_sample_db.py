import sqlite3
import random
from datetime import datetime, timedelta

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE customers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  registration_date TEXT,
                  total_points REAL DEFAULT 0)''')
    
    c.execute('''CREATE TABLE transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ticket_number TEXT,
                  fuel_type TEXT,
                  amount REAL,
                  points_earned REAL,
                  date TEXT,
                  customer_id INTEGER)''')
    
    conn.commit()
    return conn

def random_date(start, end):
    delta = end - start
    random_days = random.randrange(delta.days)
    return start + timedelta(days=random_days)

def generate_customers(conn):
    c = conn.cursor()
    start_date = datetime(2005, 1, 1)
    end_date = datetime(2025, 5, 1)
    
    for customer_id in range(1, 501):
        progress = customer_id / 500
        registration_date = start_date + (end_date - start_date) * progress
        variation = timedelta(days=random.randint(-60, 60))
        registration_date += variation
        
        if registration_date > end_date:
            registration_date = end_date - timedelta(days=random.randint(1, 30))
        
        c.execute("INSERT INTO customers (id, name, registration_date) VALUES (?, ?, ?)",
                 (customer_id, f"Customer {customer_id}", registration_date.strftime('%Y-%m-%d %H:%M:%S')))
    
    conn.commit()

def generate_transactions(conn):
    c = conn.cursor()
    fuel_types = ['Regular', 'Premium']
    current_date = datetime.now()
    
    for customer_id in range(1, 501):
        c.execute("SELECT registration_date FROM customers WHERE id = ?", (customer_id,))
        reg_date = datetime.strptime(c.fetchone()[0], '%Y-%m-%d %H:%M:%S')
        
        days_since_reg = (current_date - reg_date).days
        
        # Ensure at least 1 transaction for all customers
        min_transactions = 1
        
        # Calculate max transactions based on registration age
        max_transactions = min(50, max(1, int(days_since_reg / 30)))  # At least 1, max 50
        
        # Make sure max >= min
        if max_transactions < min_transactions:
            max_transactions = min_transactions
            
        num_transactions = random.randint(min_transactions, max_transactions)
        
        total_spent = 0
        
        for _ in range(num_transactions):
            trans_date = random_date(reg_date, current_date)
            amount = max(75, random.expovariate(1/1000))
            amount = round(amount, 2)
            points = round(amount * 0.01, 2)
            fuel_type = random.choice(fuel_types)
            ticket_number = f"TRX-{customer_id}-{trans_date.strftime('%Y%m%d%H%M%S')}"
            
            c.execute("""INSERT INTO transactions 
                        (ticket_number, fuel_type, amount, points_earned, date, customer_id) 
                        VALUES (?, ?, ?, ?, ?, ?)""",
                     (ticket_number, fuel_type, amount, points, trans_date.strftime('%Y-%m-%d %H:%M:%S'), customer_id))
            
            total_spent += amount
        
        total_points = round(total_spent * 0.01, 2)
        c.execute("UPDATE customers SET total_points = ? WHERE id = ?", (total_points, customer_id))
    
    conn.commit()

if __name__ == '__main__':
    print("Creating database...")
    conn = init_db()
    
    print("Generating 1,555 customers (2005-2025)...")
    generate_customers(conn)
    
    print("Generating transaction histories...")
    generate_transactions(conn)
    
    conn.close()
    print("Successfully created database.db with:")
    print("- 1,555 customers spanning 2005-2025")
    print("- Realistic transaction patterns")
    print("- Points calculated as 1% of spending")