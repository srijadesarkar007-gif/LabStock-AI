# LabStock AI – Predictive Inventory Control & Resource Optimization System

An AI-powered resource management, predictive inventory, and laboratory readiness platform specifically designed for college engineering laboratories (Electronics, Electrical, Mechanical, IoT, and Chemical Engineering).

---

## 🏛️ Project Overview
In engineering institutions, laboratory equipment and consumables (microcontrollers, sensors, ICs, 3D printing filaments, chemical reagents) face frequent challenges:
- Unexpected stockouts right before semester practical examinations.
- Delayed reorders due to lack of demand forecasting.
- Expired chemicals and reagents due to absence of proactive shelf-life alerts.
- Anomalous consumption surges (e.g. bulk hoarding or unrecorded component burnouts).

**LabStock AI** addresses these problems through:
- **Predictive Inventory Forecasting**: Analyzes time-series consumption to forecast component demand across semester cycles.
- **Consumption Anomaly Detection**: Flags unusual spikes and abnormal single-batch withdrawals using statistical and ML algorithms.
- **Laboratory Practical Schedules & Resource Readiness**: Verifies in advance whether current stock meets the requirements of upcoming practical sessions.
- **Comprehensive Alerts Hub**: Centralized real-time alerts for low-stock thresholds, expired chemicals, and items expiring within 30 days.
- **Administrator Authentication**: Secure portal for faculty and laboratory staff.
- **Clean Academic Dashboard**: High-contrast white background with navy-blue accents and dynamic Chart.js visualizations.

---

## 📁 Modular Project Structure

```text
LabStock-AI/
│
├── backend/                       # Python Flask backend services & routing
│   ├── __init__.py                # Package initialization
│   ├── app.py                     # Main application factory & runner
│   ├── config.py                  # Environment and directory configurations
│   ├── db.py                      # SQLite connection helper & utilities
│   └── routes/                    # Modular route handlers (Flask Blueprints)
│       ├── __init__.py
│       ├── views.py               # View routes (Dashboard, Inventory, Analytics, Login)
│       ├── api.py                 # REST API endpoints (KPIs, Charts data, Anomalies)
│       ├── schedules.py           # Laboratory practical schedules & readiness checking
│       └── alerts.py              # Low-stock, chemical expiry, and anomaly alerts
│
├── ai/                            # Predictive intelligence & machine learning modules
│   ├── __init__.py                # Package exports
│   ├── forecasting.py             # Time-series demand forecasting logic
│   └── anomaly_detection.py       # Consumption spike & outlier detection logic
│
├── database/                      # Local SQLite database & schema management
│   ├── schema.sql                 # SQL schema (suppliers, items, transactions, schedules, logs)
│   ├── init_db.py                 # Database table initialization & starter seeder
│   ├── seed_history.py            # Deep time-series consumption generator for AI training
│   └── labstock.db                # SQLite database (auto-created on initialization)
│
├── static/                        # Frontend static assets
│   ├── css/
│   │   └── style.css              # Academic dashboard styling (white background & navy-blue accents)
│   └── js/
│       ├── main.js                # Frontend navigation & UI interactions
│       └── charts.js              # Chart.js initialization & dynamic API data integration
│
├── templates/                     # Jinja2 HTML templates
│   ├── base.html                  # Master academic layout (navy navbar, sidebar, content, footer)
│   ├── login.html                 # Administrator authentication portal
│   ├── index.html                 # Main dashboard with KPI cards, Chart.js graphs, & alerts
│   ├── inventory.html             # Equipment, sensor, and consumable catalog table
│   ├── schedules.html             # Practical timetable & stock readiness view
│   └── alerts.html                # Low-stock and chemical expiry alert center
│
├── requirements.txt               # Project dependencies (Flask, pandas, numpy, scikit-learn)
├── .gitignore                     # Git ignore rules for Python, virtual environments, and SQLite
└── README.md                      # Comprehensive academic documentation and setup guide
```

---

## 🔐 Administrator Authentication & Credentials

Interactive inventory actions (adding items, issuing stock, restocking, and resolving anomalies) are protected by session-based authentication with `werkzeug.security` password hashing:
- **Admin Username**: `admin@engg.edu`
- **Admin Password**: `admin123`

---

## 📊 Note on Synthetic & Simulated Benchmark Data

The time-series consumption records in `consumption_logs` (generated via `database/seed_history.py`) are **clearly labelled synthetic / simulated benchmark datasets**. They simulate academic semester consumption cycles (regular lab practicals, mid-semester project surges, and intentional anomaly spikes) to evaluate the forecasting and outlier detection algorithms in college laboratory environments. They are **not** real-world historical records.

---

## 🗄️ Relational Database Schema

The SQLite schema (`database/schema.sql`) supports complete academic laboratory tracking:
1. **`users`**: Faculty/administrator authentication with secure password hashes.
2. **`suppliers`**: Vendor registry with contact details, address, and lead times.
3. **`categories`**: Laboratory departments (IoT, Circuits, Prototyping, Materials).
4. **`items`**: Catalog of hardware, consumables, and reagents, including `batch_number`, `expiry_date`, `minimum_threshold`, `unit_cost`, and storage location.
5. **`stock_transactions`**: Complete audit trail of `ISSUE`, `RETURN`, `RESTOCK`, and `ADJUSTMENT` operations.
6. **`lab_schedules`**: Academic practical timetable with course codes, batches, student counts, dates, times, and instructors.
7. **`schedule_requirements`**: Mapping table linking practical experiments with required equipment and minimum student quantities.
8. **`consumption_logs`**: Simulated time-series usage for training forecasting models.
9. **`forecast_records`**: AI demand predictions and automated reorder recommendations.
10. **`anomaly_logs`**: Flagged consumption spikes and abnormal checkout records.

---

## 🚀 How to Run the Application

### 1. Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python backend/app.py
```

### 4. Available URLs
- **Main Dashboard**: `http://127.0.0.1:5000/`
- **Lab Inventory**: `http://127.0.0.1:5000/inventory`
- **Practical Schedules**: `http://127.0.0.1:5000/schedules`
- **Inventory & Expiry Alerts**: `http://127.0.0.1:5000/alerts`
- **AI Analytics**: `http://127.0.0.1:5000/analytics`
- **Admin Login**: `http://127.0.0.1:5000/login`
