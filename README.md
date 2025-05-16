# KIBS Inventory Management System - Backend

## Database Tables Issue Fix

There's an issue with missing database tables for audit logs and inventory analytics. To fix this issue, follow these steps:

1. Make sure your virtual environment is activated (if you're using one)

2. Run the following command from the project root directory:

```bash
python -m ims-kibs-backend.migrations.create_tables
```

3. If you encounter any issues, you can manually create the tables by running these SQL commands in your database:

```sql
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    product_id INTEGER NOT NULL,
    user_id INTEGER,
    action_type VARCHAR(50) NOT NULL,
    previous_value VARCHAR(255),
    new_value VARCHAR(255),
    notes TEXT,
    timestamp DATETIME NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS inventory_analytics (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    product_id INTEGER NOT NULL,
    last_movement_date DATETIME,
    days_without_movement INTEGER,
    stockout_count INTEGER NOT NULL DEFAULT 0,
    last_stockout_date DATETIME,
    is_dead_stock BOOLEAN NOT NULL DEFAULT 0,
    is_slow_moving BOOLEAN NOT NULL DEFAULT 0,
    is_top_product BOOLEAN NOT NULL DEFAULT 0,
    movement_rank INTEGER,
    revenue_rank INTEGER,
    last_updated DATETIME NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

4. Restart the backend server after creating the tables.

## Note

Until the tables are created, the system will use mock data for audit logs and inventory analytics.