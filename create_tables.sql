-- KIBS IMS Database Schema for PythonAnywhere
-- Run this script in your PythonAnywhere MySQL console

-- Create rooms table
CREATE TABLE IF NOT EXISTS rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create products table
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
);

-- Create suppliers table
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
);

-- Create users table
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
);

-- Create audit_logs table
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
);

-- Create routines table
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
);

-- Create routine_completions table
CREATE TABLE IF NOT EXISTS routine_completions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    routine_id INT NOT NULL,
    completion_date DATE NOT NULL,
    completed_at DATETIME,
    completed_by INT,
    is_completed BOOLEAN DEFAULT FALSE NOT NULL,
    notes TEXT,
    FOREIGN KEY (routine_id) REFERENCES routines(id)
);

-- Create suggestions table
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
);

-- Insert default admin user (password: admin123)
INSERT IGNORE INTO users (username, email, phone, password_hash, role, is_active)
VALUES ('admin', 'admin@kibs.com', '+1234567890', 'pbkdf2:sha256:600000$salt$hash', 'admin', TRUE);

-- Insert sample rooms
INSERT IGNORE INTO rooms (name, description) VALUES 
('Main Lab', 'Primary laboratory space'),
('Storage Room', 'Chemical and equipment storage'),
('Cold Storage', 'Refrigerated storage area'),
('Equipment Room', 'Heavy equipment storage'),
('Office', 'Administrative office space');

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_products_qr_code ON products(qr_code);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_room_id ON products(room_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_product_id ON audit_logs(product_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_routines_scheduled_time ON routines(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_suggestions_status ON suggestions(status);