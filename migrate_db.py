import sqlite3
import os
from datetime import datetime

def backup_database():
    """Create a timestamped backup of the database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"database_backup_{timestamp}.db"
    if os.path.exists('database.db'):
        with open('database.db', 'rb') as src, open(backup_file, 'wb') as dst:
            dst.write(src.read())
        print(f"Created backup: {backup_file}")
    else:
        print("No existing database to backup")

def migrate_database():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    try:
        print("\nStarting database migration...")
        backup_database()

        # 1. Handle customers table migration
        c.execute("PRAGMA table_info(customers)")
        columns = {col[1]: col[2].upper() for col in c.fetchall()}
        
        if 'total_points' in columns:
            if columns['total_points'] == 'INTEGER':
                print("Converting customers.total_points from INTEGER to REAL")
                
                # Create temporary table if not exists
                c.execute('''CREATE TABLE IF NOT EXISTS customers_temp 
                           (id INTEGER PRIMARY KEY AUTOINCREMENT,
                            registration_date TEXT,
                            total_points REAL DEFAULT 0)''')
                
                # Copy data with type conversion
                c.execute('''INSERT INTO customers_temp 
                           (id, registration_date, total_points)
                           SELECT id, registration_date, 
                           CAST(total_points AS REAL) FROM customers''')
                
                # Count records to verify
                c.execute("SELECT COUNT(*) FROM customers_temp")
                temp_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM customers")
                orig_count = c.fetchone()[0]
                
                if temp_count == orig_count:
                    # Drop old and rename new
                    c.execute("DROP TABLE customers")
                    c.execute("ALTER TABLE customers_temp RENAME TO customers")
                    print(f"Migrated {temp_count} customer records successfully")
                else:
                    raise Exception("Record count mismatch during migration")
            else:
                print("customers.total_points already REAL - no change needed")
        else:
            print("Adding total_points column to customers")
            c.execute("ALTER TABLE customers ADD COLUMN total_points REAL DEFAULT 0")

        # 2. Handle transactions table
        c.execute("PRAGMA table_info(transactions)")
        columns = {col[1]: col[2].upper() for col in c.fetchall()}
        
        if 'points_earned' not in columns:
            print("Adding points_earned column to transactions")
            c.execute("ALTER TABLE transactions ADD COLUMN points_earned REAL")
        else:
            print("transactions.points_earned already exists - no change needed")

        # 3. Verify schema
        print("\nFinal schema verification:")
        c.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
        for table in c.fetchall():
            print(f"\n{table[0]} schema:\n{table[1]}")

        conn.commit()
        print("\nDatabase migration completed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"\nMigration failed: {str(e)}")
        print("Database has been rolled back to pre-migration state")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()