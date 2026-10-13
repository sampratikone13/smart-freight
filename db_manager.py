"""
Smart Freight SQLite Database Manager
Handles user authentication and prediction history tracking.
"""

import os
import sqlite3
from datetime import datetime

INSTANCE_DIR = os.path.join(os.path.dirname(__file__), "instance")
DB_PATH = os.path.join(INSTANCE_DIR, "smart_freight.db")

def get_db_connection():
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'analyst',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Predictions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        scheduled_days REAL,
        shipping_mode TEXT,
        order_type TEXT,
        customer_segment TEXT,
        market TEXT,
        order_region TEXT,
        order_country TEXT,
        order_state TEXT,
        category_name TEXT,
        department_name TEXT,
        quantity REAL,
        sales REAL,
        discount REAL,
        product_price REAL,
        predicted_days REAL,
        speed_category TEXT,
        is_delayed_risk INTEGER DEFAULT 0,
        source TEXT DEFAULT 'manual',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)

    # Clustering experiments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clustering_experiments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        k INTEGER NOT NULL,
        algorithm TEXT NOT NULL,
        silhouette_score REAL,
        calinski_harabasz REAL,
        davies_bouldin REAL,
        wcss REAL,
        personas_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Association rules experiments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS association_rule_experiments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        min_support REAL NOT NULL,
        min_confidence REAL NOT NULL,
        item_level TEXT NOT NULL,
        itemsets_count INTEGER,
        rules_count INTEGER,
        max_lift REAL,
        avg_confidence REAL,
        rules_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # OLAP Query History table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS olap_query_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation_type TEXT NOT NULL,
        dimensions_json TEXT NOT NULL,
        filters_json TEXT,
        measure TEXT,
        row_count INTEGER,
        execution_time_ms REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    conn.commit()
    conn.close()

def save_prediction(input_data: dict, result: dict, user_id: int = None, source: str = 'manual') -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO predictions (
            user_id, scheduled_days, shipping_mode, order_type, customer_segment,
            market, order_region, order_country, order_state, category_name,
            department_name, quantity, sales, discount, product_price,
            predicted_days, speed_category, is_delayed_risk, source
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        float(input_data.get('Days for shipment (scheduled)', 4) or 4),
        str(input_data.get('Shipping Mode', 'Standard Class')),
        str(input_data.get('Type', 'DEBIT')),
        str(input_data.get('Customer Segment', 'Consumer')),
        str(input_data.get('Market', 'Europe')),
        str(input_data.get('Order Region', 'Western Europe')),
        str(input_data.get('Order Country', 'Germany')),
        str(input_data.get('Order State', 'Berlin')),
        str(input_data.get('Category Name', 'Sporting Goods')),
        str(input_data.get('Department Name', 'Fitness')),
        float(input_data.get('Order Item Quantity', 1) or 1),
        float(input_data.get('Sales', 150) or 150),
        float(input_data.get('Order Item Discount', 0) or 0),
        float(input_data.get('Product Price', 150) or 150),
        float(result.get('predicted_shipping_days', 3.0)),
        str(result.get('speed_category', 'Standard')),
        1 if result.get('is_delayed_risk') else 0,
        source
    ))
    
    pred_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return pred_id

def get_recent_predictions(limit: int = 50) -> list:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM predictions
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

get_prediction_history = get_recent_predictions

def get_prediction_kpis() -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total_count FROM predictions")
    total_count = cursor.fetchone()['total_count']
    
    if total_count == 0:
        conn.close()
        return {
            "total_predictions": 0,
            "avg_predicted_days": 0.0,
            "delayed_risk_count": 0,
            "delayed_risk_rate": 0.0,
            "fast_count": 0,
            "standard_count": 0,
            "longer_count": 0,
            "shipping_mode_distribution": {},
            "speed_distribution": {}
        }
        
    cursor.execute("SELECT AVG(predicted_days) as avg_days FROM predictions")
    avg_days = cursor.fetchone()['avg_days'] or 0.0
    
    cursor.execute("SELECT COUNT(*) as delayed_cnt FROM predictions WHERE is_delayed_risk = 1")
    delayed_cnt = cursor.fetchone()['delayed_cnt'] or 0
    
    cursor.execute("""
        SELECT shipping_mode, COUNT(*) as cnt
        FROM predictions
        GROUP BY shipping_mode
    """)
    mode_dist = {row['shipping_mode']: row['cnt'] for row in cursor.fetchall()}
    
    cursor.execute("""
        SELECT speed_category, COUNT(*) as cnt
        FROM predictions
        GROUP BY speed_category
    """)
    speed_dist = {row['speed_category']: row['cnt'] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "total_predictions": total_count,
        "avg_predicted_days": round(float(avg_days), 2),
        "delayed_risk_count": delayed_cnt,
        "delayed_risk_rate": round((delayed_cnt / total_count) * 100, 1),
        "shipping_mode_distribution": mode_dist,
        "speed_distribution": speed_dist
    }

def create_user(username: str, password_hash: str, role: str = 'analyst') -> bool:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                       (username.strip(), password_hash, role))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def get_user_by_username(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username.strip(),))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def save_clustering_run(k: int, algorithm: str, metrics: dict, personas: list) -> int:
    import json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clustering_experiments (
            k, algorithm, silhouette_score, calinski_harabasz, davies_bouldin, wcss, personas_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        int(k),
        str(algorithm),
        float(metrics.get("silhouette_score", 0.0) or 0.0),
        float(metrics.get("calinski_harabasz", 0.0) or 0.0),
        float(metrics.get("davies_bouldin", 0.0) or 0.0),
        float(metrics.get("wcss", 0.0) or 0.0) if metrics.get("wcss") is not None else None,
        json.dumps(personas)
    ))
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id

def save_association_rules_run(min_support: float, min_confidence: float, item_level: str, overview: dict, rules: list) -> int:
    import json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO association_rule_experiments (
            min_support, min_confidence, item_level, itemsets_count, rules_count, max_lift, avg_confidence, rules_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        float(min_support),
        float(min_confidence),
        str(item_level),
        int(overview.get("frequent_itemsets_count", 0)),
        int(overview.get("rules_count", 0)),
        float(overview.get("max_lift", 0.0)),
        float(overview.get("avg_confidence", 0.0)),
        json.dumps(rules[:50])  # store top 50 rules
    ))
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id

def save_olap_query(operation_type: str, dimensions: list, filters: dict, measure: str, row_count: int, execution_time_ms: float) -> int:
    import json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO olap_query_history (
            operation_type, dimensions_json, filters_json, measure, row_count, execution_time_ms
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        str(operation_type),
        json.dumps(dimensions),
        json.dumps(filters or {}),
        str(measure or ""),
        int(row_count),
        float(execution_time_ms)
    ))
    query_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return query_id

def get_recent_experiment_history(limit: int = 15) -> list:
    """
    Returns aggregated recent runs from SQLite across classification, regression, clustering, association rules, and OLAP.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    history = []

    # 1. Classification
    try:
        cursor.execute("""
            SELECT 'Classification' as lab_type, algorithm as title, 
                   'F1=' || ROUND(f1_score, 3) || ', Acc=' || ROUND(accuracy, 3) as summary, 
                   created_at
            FROM classification_metrics
            ORDER BY id DESC LIMIT ?
        """, (limit,))
        history.extend([dict(r) for r in cursor.fetchall()])
    except Exception:
        pass

    # 2. Regression
    try:
        cursor.execute("""
            SELECT 'Regression' as lab_type, model_name as title, 
                   'RMSE=' || ROUND(rmse, 3) || ', R2=' || ROUND(r2_score, 3) as summary, 
                   created_at
            FROM regression_metrics
            ORDER BY id DESC LIMIT ?
        """, (limit,))
        history.extend([dict(r) for r in cursor.fetchall()])
    except Exception:
        pass

    # 3. Clustering
    try:
        cursor.execute("""
            SELECT 'Clustering' as lab_type, algorithm || ' (k=' || k || ')' as title,
                   'Silhouette=' || ROUND(silhouette_score, 4) as summary,
                   created_at
            FROM clustering_experiments
            ORDER BY id DESC LIMIT ?
        """, (limit,))
        history.extend([dict(r) for r in cursor.fetchall()])
    except Exception:
        pass

    # 4. Association Rules
    try:
        cursor.execute("""
            SELECT 'Association Rules' as lab_type, 'Apriori (' || item_level || ')' as title,
                   rules_count || ' rules, Max Lift=' || ROUND(max_lift, 3) as summary,
                   created_at
            FROM association_rule_experiments
            ORDER BY id DESC LIMIT ?
        """, (limit,))
        history.extend([dict(r) for r in cursor.fetchall()])
    except Exception:
        pass

    # 5. OLAP Queries
    try:
        cursor.execute("""
            SELECT 'OLAP Query' as lab_type, operation_type as title,
                   row_count || ' rows in ' || ROUND(execution_time_ms, 1) || 'ms' as summary,
                   created_at
            FROM olap_query_history
            ORDER BY id DESC LIMIT ?
        """, (limit,))
        history.extend([dict(r) for r in cursor.fetchall()])
    except Exception:
        pass

    conn.close()
    # Sort chronologically descending
    history.sort(key=lambda x: str(x.get('created_at', '')), reverse=True)
    return history[:limit]

def get_warehouse_health_summary() -> dict:
    """
    Returns actual row counts and database health metrics directly from SQLite.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    tables = [
        "FactOrders", "FactShippingPerformance",
        "DimDate", "DimGeography", "DimProduct",
        "DimCustomer", "DimShipping"
    ]
    counts = {}
    for tbl in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
            counts[tbl] = cursor.fetchone()[0]
        except Exception:
            counts[tbl] = 0
            
    # Check predictions and users
    try:
        cursor.execute("SELECT COUNT(*) FROM predictions")
        counts["predictions"] = cursor.fetchone()[0]
    except Exception:
        counts["predictions"] = 0

    conn.close()

    db_size_mb = 0.0
    if os.path.exists(DB_PATH):
        db_size_mb = round(os.path.getsize(DB_PATH) / (1024 * 1024), 2)

    return {
        "status": "healthy",
        "db_path": DB_PATH,
        "db_size_mb": db_size_mb,
        "table_counts": counts,
        "fact_orders_rows": counts.get("FactOrders", 0),
        "constellation_fact_rows": counts.get("FactShippingPerformance", 0),
        "total_warehouse_rows": sum(counts.values())
    }

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at", DB_PATH)
