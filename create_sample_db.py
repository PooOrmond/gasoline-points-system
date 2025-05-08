import sqlite3
import random
from datetime import datetime, timedelta

def create_sample_database():
    # Create or connect to database
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS customers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  registration_date TEXT,
                  total_points REAL DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ticket_number TEXT,
                  fuel_type TEXT,
                  amount REAL,
                  points_earned REAL,
                  date TEXT,
                  customer_id INTEGER)''')
    
    # Start registration date
    current_date = datetime(2005, 1, 17, 1, 14, 29)
    
    for i in range(1, 1001):
        name = f"Customer {i}"

        # Save registration datetime
        reg_date_str = current_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Random points balance
        points = round(random.uniform(0, 500), 2)

        # Insert customer
        c.execute("INSERT INTO customers (name, registration_date, total_points) VALUES (?, ?, ?)",
                  (name, reg_date_str, points))
        
        # Generate 1–5 transactions
        for _ in range(random.randint(1, 5)):
            fuel_type = random.choice(["Regular", "Premium"])
            amount = round(random.uniform(100, 5000), 2)
            points_earned = round(amount * 0.01, 2)
            
            # Transaction date: 1–730 days after registration, add time
            trans_date = current_date + timedelta(days=random.randint(1, 730),
                                                  hours=random.randint(0, 23),
                                                  minutes=random.randint(0, 59),
                                                  seconds=random.randint(0, 59))
            # Ensure transaction date does not exceed 2025-12-31
            if trans_date.year > 2025:
                trans_date = datetime(2025, 12, 31, 23, 59, 59)

            trans_date_str = trans_date.strftime('%Y-%m-%d %H:%M:%S')
            ticket_number = f"TRX-{i}-{trans_date.strftime('%Y%m%d%H%M%S')}"
            
            c.execute("""INSERT INTO transactions 
                         (ticket_number, fuel_type, amount, points_earned, date, customer_id)
                         VALUES (?, ?, ?, ?, ?, ?)""",
                      (ticket_number, fuel_type, amount, points_earned, trans_date_str, i))
        
        # Advance current_date for next customer (1–3 days + random time)
        current_date += timedelta(days=random.randint(1, 3),
                                  hours=random.randint(0, 3),
                                  minutes=random.randint(0, 59),
                                  seconds=random.randint(0, 59))
        
        # Stop if we're about to exceed year 2025
        if current_date.year > 2025:
            break

    conn.commit()
    conn.close()
    print("Successfully created sample database with customers from 2005 to 2025.")

if __name__ == '__main__':
    create_sample_database()
