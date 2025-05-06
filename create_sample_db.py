import sqlite3
from datetime import datetime, timedelta
import random
from werkzeug.security import generate_password_hash

def create_sample_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Create tables (same structure as your app)
    c.execute('''CREATE TABLE customers (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT,
                 registration_date TEXT,
                 total_points INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE transactions (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 ticket_number TEXT,
                 fuel_type TEXT,
                 amount REAL,
                 points_earned INTEGER,
                 date TEXT,
                 customer_id INTEGER)''')
    
    c.execute('''CREATE TABLE rewards (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT,
                 points_required INTEGER,
                 status TEXT DEFAULT 'Active')''')
    
    # Add sample rewards
    rewards = [
        ("1 Liter of Fuel", 100),
        ("Free Refill", 500),
        ("Car Wash", 200),
        ("Oil Change", 300)
    ]
    c.executemany("INSERT INTO rewards (name, points_required) VALUES (?, ?)", rewards)
    
    # Generate 50 customers with random registration dates
    fuel_types = ['Regular', 'Premium', 'Diesel']
    start_date = datetime(2020, 1, 1)
    end_date = datetime.now()
    
    for i in range(1, 51):
        # Random registration date between 2020 and now
        random_days = random.randint(0, (end_date - start_date).days)
        reg_date = (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d')
        
        c.execute("INSERT INTO customers (name, registration_date) VALUES (?, ?)",
                 (f"Customer {i}", reg_date))
        
        # Generate 2-10 transactions per customer
        transaction_count = random.randint(2, 10)
        for _ in range(transaction_count):
            random_days = random.randint(0, (end_date - start_date).days)
            trans_date = (start_date + timedelta(days=random_days)).strftime('%Y-%m-%d %H:%M:%S')
            fuel = random.choice(fuel_types)
            amount = round(random.uniform(500, 5000), 2)
            points = int(amount // 100)
            ticket_num = f"TRX-{i}-{trans_date.replace(' ', '').replace(':', '').replace('-', '')}"
            
            c.execute('''INSERT INTO transactions 
                        (ticket_number, fuel_type, amount, points_earned, date, customer_id)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (ticket_num, fuel, amount, points, trans_date, i))
            
            # Update customer's total points
            c.execute("UPDATE customers SET total_points = total_points + ? WHERE id = ?",
                     (points, i))
    
    conn.commit()
    conn.close()
    print("Successfully created sample database with 50 customers and transactions!")

if __name__ == '__main__':
    create_sample_db()