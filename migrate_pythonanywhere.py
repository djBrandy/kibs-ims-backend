#!/usr/bin/env python3
"""
Migration script for PythonAnywhere MySQL database
"""
import pymysql
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_migration():
    connection = None
    try:
        # Database connection for PythonAnywhere
        connection = pymysql.connect(
            host='djbrandy67.mysql.pythonanywhere-services.com',
            user='djbrandy67',
            password='Brandon',
            database='djbrandy67$kibs_ims_db',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        print("Running database migration for PythonAnywhere...")
        
        # Create tables if they don't exist
        table_creations = [
            """
            CREATE TABLE IF NOT EXISTS rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_name VARCHAR(255) NOT NULL,
                product_type VARCHAR(255) NOT NULL,
                category VARCHAR(255) NOT NULL,
                product_code VARCHAR(100) UNIQUE,
                manufacturer VARCHAR(255),
                qr_code VARCHAR(16) UNIQUE NOT NULL,
                price_in_kshs FLOAT NOT NULL,
                quantity INT NOT NULL,
                unit_of_measure VARCHAR(50) NOT NULL,
                concentration FLOAT,
                storage_temperature VARCHAR(255),
                expiration_date DATE,
                hazard_level VARCHAR(255),
                protocol_link VARCHAR(255),
                msds_link VARCHAR(255),
                low_stock_alert INT DEFAULT 10 NOT NULL,
                checkbox_expiry_date BOOLEAN DEFAULT FALSE,
                checkbox_hazardous_material BOOLEAN DEFAULT FALSE,
                checkbox_controlled_substance BOOLEAN DEFAULT FALSE,
                checkbox_requires_regular_calibration BOOLEAN DEFAULT FALSE,
                special_instructions TEXT,
                product_images LONGBLOB,
                date_of_entry DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                hidden_from_workers BOOLEAN DEFAULT FALSE,
                last_audit_time DATETIME,
                audit_message TEXT,
                force_low_stock_alert BOOLEAN DEFAULT FALSE,
                room_id INT,
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS suppliers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                shop_name VARCHAR(255) NOT NULL,
                primary_contact VARCHAR(255) NOT NULL,
                phone VARCHAR(50),
                email VARCHAR(255),
                address TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                product_id INT NOT NULL,
                user_id INT,
                action_type VARCHAR(100) NOT NULL,
                previous_value LONGTEXT,
                new_value LONGTEXT,
                notes LONGTEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                room_id INT,
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (room_id) REFERENCES rooms(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS routines (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                scheduled_time TIME NOT NULL,
                frequency VARCHAR(20) DEFAULT 'daily' NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                created_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS routine_completions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                routine_id INT NOT NULL,
                completion_date DATE NOT NULL,
                completed_at DATETIME,
                completed_by INT,
                is_completed BOOLEAN DEFAULT FALSE NOT NULL,
                notes TEXT,
                FOREIGN KEY (routine_id) REFERENCES routines(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS suggestions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                category VARCHAR(100),
                priority VARCHAR(20) DEFAULT 'medium' NOT NULL,
                status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                submitted_by INT,
                reviewed_by INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                admin_notes TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(64) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                phone VARCHAR(20) UNIQUE,
                password_hash VARCHAR(128) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                last_activity DATETIME,
                reset_token VARCHAR(128),
                role VARCHAR(20) NOT NULL DEFAULT 'worker',
                permissions TEXT,
                is_banned BOOLEAN DEFAULT FALSE,
                ban_reason TEXT
            )
            """
        ]
        
        for table_sql in table_creations:
            try:
                cursor.execute(table_sql)
                print(f"✓ Table created/verified")
            except Exception as e:
                print(f"✗ Error creating table: {e}")
        
        # Add missing columns
        column_additions = [
            "ALTER TABLE products ADD COLUMN IF NOT EXISTS last_audit_time DATETIME",
            "ALTER TABLE products ADD COLUMN IF NOT EXISTS audit_message TEXT",
            "ALTER TABLE products ADD COLUMN IF NOT EXISTS force_low_stock_alert BOOLEAN DEFAULT FALSE"
        ]
        
        for column_sql in column_additions:
            try:
                cursor.execute(column_sql)
                print(f"✓ Column added/verified")
            except Exception as e:
                if "Duplicate column name" not in str(e):
                    print(f"✗ Error adding column: {e}")
                else:
                    print(f"⚠ Column already exists")
        
        # Create default admin user
        try:
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
            admin_count = cursor.fetchone()[0]
            
            if admin_count == 0:
                from werkzeug.security import generate_password_hash
                password_hash = generate_password_hash('admin123')
                
                cursor.execute("""
                    INSERT INTO users (username, email, phone, password_hash, role, is_active)
                    VALUES ('admin', 'admin@kibs.com', '+1234567890', %s, 'admin', TRUE)
                """, (password_hash,))
                print("✓ Default admin user created")
            else:
                print("⚠ Admin user already exists")
        except Exception as e:
            print(f"✗ Error creating admin user: {e}")
        
        connection.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        if connection:
            connection.rollback()
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    run_migration()