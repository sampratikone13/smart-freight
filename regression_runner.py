"""
Smart Freight Regression Experiment Runner & SQLite Persistence (Lab 6)
- Orchestrates 7 regression models comparison
- Persists experiment runs in SQLite (academic_experiment_runs & regression_metrics)
- Uses deterministic MD5 hashing for instant cache hits on repeated parameters
- Generates 7-model comparative benchmark matrix and regularization alpha curves
"""

import os
import json
import sqlite3
import pandas as pd
from datetime import datetime

from regression_pipeline import (
    train_and_evaluate_regressor,
    build_regression_hash,
    compute_regularization_path,
    load_data,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES
)
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder

INSTANCE_DIR = os.path.join(os.path.dirname(__file__), "instance")
DB_PATH = os.path.join(INSTANCE_DIR, "smart_freight.db")
CACHE_FILE = os.path.join(os.path.dirname(__file__), "data", "regression_benchmark_cache.json")


def get_db_connection():
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_regression_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS academic_experiment_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_hash TEXT UNIQUE NOT NULL,
        algorithm TEXT NOT NULL,
        imbalance_strategy TEXT DEFAULT 'none',
        hyperparams_json TEXT,
        test_size REAL,
        random_state INTEGER,
        metrics_json TEXT NOT NULL,
        result_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS regression_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_hash TEXT NOT NULL,
        model_key TEXT NOT NULL,
        model_name TEXT NOT NULL,
        mae REAL,
        mse REAL,
        rmse REAL,
        r2_score REAL,
        training_time REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reg_hash ON regression_metrics(run_hash);")
    conn.commit()
    conn.close()


def run_regression_experiment(
    model_key: str = "random_forest",
    hyperparams: dict = None,
    test_size: float = 0.20,
    random_state: int = 42,
    force_retrain: bool = False
) -> dict:
    """
    Executes experiment with SQLite caching.
    Returns cached run if exact parameters were evaluated previously.
    """
    init_regression_db()
    hyperparams = hyperparams or {}

    expected_hash = build_regression_hash(
        model_key, hyperparams, test_size, random_state
    )

    conn = get_db_connection()
    cursor = conn.cursor()

    if not force_retrain:
        cursor.execute(
            "SELECT result_json FROM academic_experiment_runs WHERE run_hash = ?",
            (expected_hash,)
        )
        row = cursor.fetchone()
        if row:
            conn.close()
            res = json.loads(row["result_json"])
            res["cached"] = True
            return res

    # Run fresh training
    result = train_and_evaluate_regressor(
        model_key=model_key,
        hyperparams=hyperparams,
        test_size=test_size,
        random_state=random_state
    )
    result["cached"] = False

    run_hash = result["run_hash"]
    m = result["metrics"]

    cursor.execute("""
    INSERT OR REPLACE INTO academic_experiment_runs (
        run_hash, algorithm, imbalance_strategy, hyperparams_json,
        test_size, random_state, metrics_json, result_json, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_hash,
        result["model_key"],
        "regression",
        json.dumps(result["hyperparams"]),
        result["test_size"],
        result["random_state"],
        json.dumps(m),
        json.dumps(result),
        datetime.now().isoformat()
    ))

    cursor.execute("""
    INSERT INTO regression_metrics (
        run_hash, model_key, model_name, mae, mse, rmse, r2_score, training_time, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_hash,
        result["model_key"],
        result["display_name"],
        m["mae"],
        m["mse"],
        m["rmse"],
        m["r2_score"],
        m["training_time_seconds"],
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()
    return result


def get_all_regression_runs(limit: int = 50) -> list[dict]:
    init_regression_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT run_hash, algorithm, metrics_json, created_at
    FROM academic_experiment_runs
    WHERE imbalance_strategy = 'regression'
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))
    rows = []
    for r in cursor.fetchall():
        rows.append({
            "run_hash": r["run_hash"],
            "model_key": r["algorithm"],
            "metrics": json.loads(r["metrics_json"]),
            "created_at": r["created_at"]
        })
    conn.close()
    return rows


def get_regression_benchmark_suite() -> dict:
    """
    Returns comparative evaluation of all 7 models.
    Caches suite to disk / SQLite for instantaneous web loading.
    """
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass

    models = [
        ("simple_linear", {}),
        ("multiple_linear", {}),
        ("lasso", {"alpha": 0.01}),
        ("ridge", {"alpha": 1.0}),
        ("elastic_net", {"alpha": 0.01, "l1_ratio": 0.5}),
        ("decision_tree", {"max_depth": 10, "min_samples_split": 10}),
        ("random_forest", {"n_estimators": 80, "max_depth": 12})
    ]

    benchmark_rows = []
    model_results = {}

    for m_key, hp in models:
        res = run_regression_experiment(
            model_key=m_key,
            hyperparams=hp,
            test_size=0.20,
            random_state=42
        )
        m = res["metrics"]
        benchmark_rows.append({
            "model_key": res["model_key"],
            "display_name": res["display_name"],
            "model_type": res["model_type"],
            "rmse": m["rmse"],
            "mae": m["mae"],
            "mse": m["mse"],
            "r2_score": m["r2_score"],
            "training_time": m["training_time_seconds"],
            "run_hash": res["run_hash"]
        })
        model_results[m_key] = res

    # Sort benchmark by canonical rule: lowest RMSE -> lowest MAE -> highest R²
    benchmark_rows = sorted(benchmark_rows, key=lambda x: (x["rmse"], x["mae"], -x["r2_score"]))
    best_model = benchmark_rows[0]

    # Precompute regularization path
    df = load_data()
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

    preprocessor = ColumnTransformer([
        ("num", Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler())
        ]), NUMERIC_FEATURES),
        ("cat", Pipeline([
            ("imp", SimpleImputer(strategy="most_frequent")),
            ("ohe", OneHotEncoder(handle_unknown="ignore", min_frequency=20, sparse_output=False))
        ]), CATEGORICAL_FEATURES)
    ])
    X_tr_proc = preprocessor.fit_transform(X_train)
    X_te_proc = preprocessor.transform(X_test)
    reg_paths = compute_regularization_path(X_tr_proc, y_train, X_te_proc, y_test)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "benchmark_table": benchmark_rows,
        "best_model": best_model,
        "regularization_paths": reg_paths,
        "model_results": {k: {
            "metrics": v["metrics"],
            "diagnostics": v["diagnostics"],
            "display_name": v["display_name"],
            "model_type": v["model_type"]
        } for k, v in model_results.items()}
    }

    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(payload, f, indent=2)

    return payload


if __name__ == "__main__":
    print("Pre-warming regression benchmark suite across all 7 models...")
    init_regression_db()
    suite = get_regression_benchmark_suite()
    print("Benchmark complete! Best model:")
    print(json.dumps(suite["best_model"], indent=2))
