-- LabStock AI SQLite Database Schema
-- College-level Engineering Laboratories Predictive Inventory & Resource Optimization System

PRAGMA foreign_keys = ON;

-- 1. Suppliers / Vendors
CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    contact_person TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    lead_time_days INTEGER DEFAULT 7,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Categories / Lab Departments
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    department TEXT NOT NULL,
    description TEXT
);

-- 3. Inventory Items (Equipments, Sensors, Consumables, Reagents)
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    supplier_id INTEGER,
    lab_name TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    unit TEXT NOT NULL DEFAULT 'units',
    minimum_threshold INTEGER NOT NULL DEFAULT 10,
    unit_cost REAL NOT NULL DEFAULT 0.0,
    storage_location TEXT,
    batch_number TEXT,
    expiry_date DATE,
    status TEXT NOT NULL DEFAULT 'In Stock',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
);

-- 4. Stock Transactions (Issues, Returns, Restocks, Adjustments)
CREATE TABLE IF NOT EXISTS stock_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    transaction_type TEXT NOT NULL CHECK(transaction_type IN ('ISSUE', 'RETURN', 'RESTOCK', 'ADJUSTMENT')),
    quantity INTEGER NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recipient_or_source TEXT NOT NULL,
    purpose TEXT,
    logged_by TEXT DEFAULT 'Lab Assistant',
    notes TEXT,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

-- 5. Laboratory Practical Schedules
CREATE TABLE IF NOT EXISTS lab_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL,
    course_name TEXT NOT NULL,
    practical_title TEXT NOT NULL,
    lab_room TEXT NOT NULL,
    department TEXT NOT NULL,
    student_batch TEXT NOT NULL,
    student_count INTEGER NOT NULL DEFAULT 30,
    scheduled_date DATE NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    instructor_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Upcoming' CHECK(status IN ('Upcoming', 'In Progress', 'Completed', 'Cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Schedule Resource Requirements (Links items needed for each practical session)
CREATE TABLE IF NOT EXISTS schedule_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    required_quantity INTEGER NOT NULL,
    FOREIGN KEY (schedule_id) REFERENCES lab_schedules(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

-- 7. Consumption & Transaction Logs (Data source for AI Forecasting & Anomaly Detection)
CREATE TABLE IF NOT EXISTS consumption_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    quantity_used INTEGER NOT NULL,
    logged_date DATE NOT NULL,
    purpose TEXT,
    issued_to TEXT,
    is_anomaly INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

-- 8. AI Predictive Forecasting Records
CREATE TABLE IF NOT EXISTS forecast_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    forecast_period TEXT NOT NULL,
    predicted_demand REAL NOT NULL,
    suggested_reorder_qty INTEGER NOT NULL,
    confidence_score REAL,
    model_version TEXT DEFAULT 'v1.0-linear',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

-- 9. AI Detected Consumption Anomalies
CREATE TABLE IF NOT EXISTS anomaly_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    consumption_log_id INTEGER,
    severity TEXT NOT NULL DEFAULT 'Medium',
    anomaly_reason TEXT NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved INTEGER DEFAULT 0,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
    FOREIGN KEY (consumption_log_id) REFERENCES consumption_logs(id) ON DELETE SET NULL
);

-- 10. System Users / Administrators
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'Administrator',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

