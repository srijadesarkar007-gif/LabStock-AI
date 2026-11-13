"""
Database initialization and starter seeding script for LabStock AI.
Populates core engineering lab suppliers, categories, items (with expiry dates),
stock transactions, and laboratory practical schedules.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'labstock.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'database', 'schema.sql')


def get_connection(db_path=DB_PATH):
    """Create and return a database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_database(db_path=DB_PATH, schema_path=SCHEMA_PATH, reset=False):
    """Execute SQL schema to create tables if they do not exist."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if reset and os.path.exists(db_path):
        os.remove(db_path)

    with get_connection(db_path) as conn:
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
    seed_starter_data(db_path)


def seed_starter_data(db_path=DB_PATH):
    """Insert initial engineering laboratory starter records if empty."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Seed Default Administrator User if missing
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """INSERT INTO users (username, password_hash, full_name, role)
                   VALUES (?, ?, ?, ?)""",
                ("admin@engg.edu", generate_password_hash("admin123"), "Dr. Aris (Laboratory Director)", "Administrator")
            )
            conn.commit()

        # Check if items already seeded
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] > 0:
            return

        print("Seeding academic lab suppliers, inventory items, and practical schedules...")

        # 1. Insert Suppliers
        suppliers = [
            ("Apex Scientific & Instruments", "Dr. S. Nair", "sales@apexscientific.edu", "+1-800-555-0199", "Tech Park, Building 4", 5),
            ("Element14 Academic Direct", "Marcus Vance", "academic@element14.com", "+1-800-555-0142", "Industrial Logistics Hub", 3),
            ("Sigma & Fisher Chemical Reagents", "Elena Rostova", "orders@sigmafisher.com", "+1-800-555-0177", "Biotech Research Avenue", 7),
            ("ProFab Tools & Fasteners", "Rajesh Kumar", "contact@profabtools.in", "+91-98765-43210", "Phase 2 Engineering Zone", 4)
        ]
        cursor.executemany(
            """INSERT INTO suppliers (name, contact_person, email, phone, address, lead_time_days)
               VALUES (?, ?, ?, ?, ?, ?)""",
            suppliers
        )

        # 2. Insert Categories
        categories = [
            ("Embedded Systems & IoT", "Electronics & Communication", "Microcontrollers, development boards, and IoT sensors"),
            ("Electrical Machines & Circuits", "Electrical Engineering", "Meters, passive components, transformers, and breadboards"),
            ("Mechanical Prototyping", "Mechanical Engineering", "Fasteners, 3D printing filaments, calipers, and bearings"),
            ("Applied Chemistry & Materials", "Chemical Engineering", "Reagents, glassware, indicators, and safety consumables")
        ]
        cursor.executemany(
            "INSERT INTO categories (name, department, description) VALUES (?, ?, ?)",
            categories
        )

        # Dates for Expiry Tracking
        today = datetime.now().date()
        exp_soon = str(today + timedelta(days=15))      # Expiring in 15 days
        exp_next_month = str(today + timedelta(days=38)) # Expiring in 38 days
        exp_expired = str(today - timedelta(days=5))     # Already expired 5 days ago
        exp_safe = str(today + timedelta(days=365))      # Safe for a year

        # 3. Insert Items (with batch numbers, expiry dates, supplier links)
        items = [
            ("ECE-DEV-001", "Arduino Uno Rev3", 1, 2, "Microcontroller Lab", 42, "units", 15, 18.50, "Cabinet A-1", "BAT-2024-ARD", None, "In Stock"),
            ("ECE-SEN-004", "Ultrasonic Sensor HC-SR04", 1, 2, "IoT Systems Lab", 12, "units", 20, 3.20, "Drawer B-3", "BAT-2025-SEN", None, "Low Stock"),
            ("ECE-DEV-008", "ESP32 Wi-Fi + BLE Board", 1, 2, "IoT Systems Lab", 28, "units", 10, 8.00, "Cabinet A-2", "BAT-2025-ESP", None, "In Stock"),
            ("EEE-CMP-020", "Resistor Assortment Kit (1/4W)", 2, 2, "Circuits Lab", 8, "kits", 12, 14.00, "Rack C-1", "BAT-2023-RES", None, "Low Stock"),
            ("EEE-MET-002", "Digital Multimeter Fluke 101", 2, 1, "Instrumentation Lab", 24, "units", 5, 45.00, "Locker D-4", "CAL-2024-FLK", None, "In Stock"),
            ("MEC-FIL-011", "PLA 3D Printing Filament 1.75mm (1kg)", 3, 4, "CAD/CAM & Fab Lab", 5, "spools", 8, 22.00, "Storage Bin 2", "FIL-2025-PLA", None, "Critical"),
            ("MEC-TLS-005", "Digital Vernier Caliper 150mm", 3, 4, "Metrology Lab", 18, "units", 6, 25.50, "Tool Chest 1", "TLS-2024-CAL", None, "In Stock"),
            ("CHE-GLS-003", "Borosil Glass Beakers Set (250ml)", 4, 3, "Material Testing Lab", 35, "sets", 10, 16.00, "Glass Cabinet 3", "GLS-2024-BEA", None, "In Stock"),
            ("CHE-CHM-014", "Standard Buffer Solution pH 7.00", 4, 3, "Chemical Analytics Lab", 4, "bottles", 6, 12.50, "Chemical Rack 1", "LOT-BUF-700", exp_soon, "Low Stock"),
            ("CHE-CHM-022", "Conductivity Standard 1413 µS/cm", 4, 3, "Chemical Analytics Lab", 2, "bottles", 5, 19.00, "Chemical Rack 2", "LOT-CND-141", exp_expired, "Critical"),
            ("CHE-CHM-030", "Phenolphthalein Indicator Solution 1%", 4, 3, "Chemistry Core Lab", 14, "bottles", 8, 9.50, "Chemical Cabinet B", "LOT-PHT-092", exp_next_month, "In Stock")
        ]
        cursor.executemany(
            """INSERT INTO items 
               (item_code, name, category_id, supplier_id, lab_name, quantity, unit, 
                minimum_threshold, unit_cost, storage_location, batch_number, expiry_date, status) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            items
        )

        # 4. Insert Stock Transactions
        transactions = [
            (1, 'RESTOCK', 20, str(today - timedelta(days=30)), 'Supplier Shipment: Element14', 'Semester Inventory Restocking', 'Lab Storekeeper', 'Received in good condition'),
            (1, 'ISSUE', 10, str(today - timedelta(days=12)), 'Batch 2024-ECE-A', 'Practical Experiment 4: Interfacing', 'Prof. Sharma', 'Approved student issue slip #402'),
            (6, 'ISSUE', 4, str(today - timedelta(days=4)), 'Mech Final Year Team 8', 'Capstone Prototype Fabrication', 'Lab Tech Davis', '3D printer filament requisition'),
            (9, 'RESTOCK', 6, str(today - timedelta(days=60)), 'Sigma & Fisher PO-8891', 'Annual Laboratory Consumables Batch', 'Dr. Aris', 'Stored under controlled temperature')
        ]
        cursor.executemany(
            """INSERT INTO stock_transactions 
               (item_id, transaction_type, quantity, transaction_date, recipient_or_source, purpose, logged_by, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            transactions
        )

        # 5. Insert Laboratory Practical Schedules
        schedules = [
            (
                "EC304L", "Microcontroller & Embedded Systems Lab", "Experiment 6: Sensor Interfacing & PWM Control",
                "Lab Room 204", "Electronics & Communication", "Batch 2024 ECE-B", 32,
                str(today + timedelta(days=2)), "09:00 AM", "12:00 PM", "Prof. R. Sengupta", "Upcoming"
            ),
            (
                "CS408L", "Internet of Things Practicals", "Experiment 4: ESP32 Cloud MQTT Telemetry",
                "IoT Hub Lab 102", "Electronics & Communication", "Batch 2025 IoT Sec-1", 28,
                str(today + timedelta(days=4)), "01:30 PM", "04:30 PM", "Dr. K. Raman", "Upcoming"
            ),
            (
                "ME210L", "Computer Aided Manufacturing Lab", "Session 9: Rapid Prototyping & FDM Slicing",
                "Fab Lab Studio", "Mechanical Engineering", "Batch 2024 MECH-A", 24,
                str(today + timedelta(days=6)), "10:00 AM", "01:00 PM", "Prof. Alan Miller", "Upcoming"
            ),
            (
                "CH102L", "Engineering Chemistry Lab", "Experiment 3: Determination of pH and Buffer Capacity",
                "Chemistry Lab 001", "Chemical Engineering", "Batch 2026 CHEM Core", 30,
                str(today + timedelta(days=8)), "02:00 PM", "05:00 PM", "Dr. Meenakshi Iyer", "Upcoming"
            )
        ]
        cursor.executemany(
            """INSERT INTO lab_schedules 
               (course_code, course_name, practical_title, lab_room, department, 
                student_batch, student_count, scheduled_date, start_time, end_time, instructor_name, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            schedules
        )

        # 6. Insert Schedule Resource Requirements (links items needed for practicals)
        # Schedule 1 (Arduino Lab): needs 16 Arduino boards and 16 Ultrasonic sensors (1 per pair)
        # Schedule 2 (ESP32 IoT Lab): needs 14 ESP32 boards
        # Schedule 3 (3D Printing Fab Lab): needs 2 spools of PLA filament
        # Schedule 4 (Chemistry Lab): needs 2 bottles of Buffer Solution
        requirements = [
            (1, 1, 16), # Schedule 1 needs 16x Arduino Uno
            (1, 2, 16), # Schedule 1 needs 16x Ultrasonic Sensors
            (2, 3, 14), # Schedule 2 needs 14x ESP32 Boards
            (3, 6, 2),  # Schedule 3 needs 2x PLA Filament Spools
            (4, 9, 2)   # Schedule 4 needs 2x Buffer Solution bottles
        ]
        cursor.executemany(
            """INSERT INTO schedule_requirements (schedule_id, item_id, required_quantity)
               VALUES (?, ?, ?)""",
            requirements
        )

        # 7. Insert Historical Consumption Logs
        base_date = datetime.now().date()
        consumption_samples = [
            (1, 4, str(base_date - timedelta(days=25)), "Mini Project Experiments", "Batch 2024-ECE-A", 0),
            (1, 6, str(base_date - timedelta(days=18)), "Embedded Systems Lab Exam", "Batch 2024-ECE-B", 0),
            (1, 8, str(base_date - timedelta(days=10)), "Robotics Competition Workshop", "Robotics Club", 0),
            (2, 5, str(base_date - timedelta(days=22)), "Distance Measurement Practicals", "Batch 2025-IoT-A", 0),
            (2, 14, str(base_date - timedelta(days=5)), "Unusual Bulk Withdrawal", "Unknown / Project Team 4", 1),
            (6, 4, str(base_date - timedelta(days=12)), "Capstone Prototype 3D Printing", "Mech Final Year", 0),
            (6, 3, str(base_date - timedelta(days=3)), "Urgent Bracket Fabrication", "Aero Design Team", 0)
        ]
        cursor.executemany(
            """INSERT INTO consumption_logs 
               (item_id, quantity_used, logged_date, purpose, issued_to, is_anomaly)
               VALUES (?, ?, ?, ?, ?, ?)""",
            consumption_samples
        )

        # 8. Insert Starter Anomaly Flag
        cursor.execute(
            """INSERT INTO anomaly_logs
               (item_id, consumption_log_id, severity, anomaly_reason, resolved)
               VALUES (?, ?, ?, ?, ?)""",
            (2, 5, "High", "Single-day consumption exceeded 300% of rolling 30-day average.", 0)
        )

        # 9. Insert Default Administrator User
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                """INSERT INTO users (username, password_hash, full_name, role)
                   VALUES (?, ?, ?, ?)""",
                ("admin@engg.edu", generate_password_hash("admin123"), "Dr. Aris (Laboratory Director)", "Administrator")
            )

        conn.commit()
        print("Database successfully initialized and seeded with complete academic laboratory schema.")


if __name__ == '__main__':
    # When executed directly, reset and seed cleanly
    init_database(reset=True)
