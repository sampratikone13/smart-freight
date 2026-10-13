"""
Smart Freight Classification Experiment Runner & SQLite Persistence (Labs 4–5)
- Orchestrates classification model training and evaluation
- Persists experiment runs in SQLite (academic_experiment_runs & classification_metrics)
- Uses deterministic hashing for instantaneous cache hits on repeated parameters
- Generates 12-way comparative benchmarks across 4 algorithms x 3 imbalance strategies
"""

import os
import json
import sqlite3
import pandas as pd
from datetime import datetime
from classification_pipeline import (
    train_and_evaluate_classifier,
    build_experiment_hash
)

INSTANCE_DIR = os.path.join(os.path.dirname(__file__), "instance")
DB_PATH = os.path.join(INSTANCE_DIR, "smart_freight.db")


def get_db_connection():
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_classification_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS academic_experiment_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_hash TEXT UNIQUE NOT NULL,
        algorithm TEXT NOT NULL,
        imbalance_strategy TEXT NOT NULL,
        hyperparams_json TEXT,
        test_size REAL,
        random_state INTEGER,
        metrics_json TEXT NOT NULL,
        result_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS classification_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_hash TEXT NOT NULL,
        algorithm TEXT NOT NULL,
        imbalance_strategy TEXT NOT NULL,
        accuracy REAL,
        precision REAL,
        recall REAL,
        specificity REAL,
        f1_score REAL,
        roc_auc REAL,
        training_time REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_exp_hash ON academic_experiment_runs(run_hash);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_met_hash ON classification_metrics(run_hash);")

    conn.commit()
    conn.close()


def run_experiment(
    algorithm: str = "random_forest",
    imbalance_strategy: str = "baseline",
    hyperparams: dict = None,
    test_size: float = 0.20,
    random_state: int = 42,
    force_retrain: bool = False
) -> dict:
    """
    Executes experiment with SQLite caching.
    Returns cached run if exact parameters were run previously.
    """
    init_classification_db()
    hyperparams = hyperparams or {}

    expected_hash = build_experiment_hash(
        algorithm, imbalance_strategy, hyperparams,
        test_size, random_state
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
    result = train_and_evaluate_classifier(
        algorithm=algorithm,
        imbalance_strategy=imbalance_strategy,
        hyperparams=hyperparams,
        test_size=test_size,
        random_state=random_state
    )
    result["cached"] = False

    # Persist in SQLite
    run_hash = result["run_hash"]
    m = result["metrics"]

    cursor.execute("""
    INSERT OR REPLACE INTO academic_experiment_runs (
        run_hash, algorithm, imbalance_strategy, hyperparams_json,
        test_size, random_state, metrics_json, result_json, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_hash,
        result["algorithm"],
        result["imbalance_strategy"],
        json.dumps(result["hyperparams"]),
        result["test_size"],
        result["random_state"],
        json.dumps(m),
        json.dumps(result),
        datetime.now().isoformat()
    ))

    cursor.execute("""
    INSERT INTO classification_metrics (
        run_hash, algorithm, imbalance_strategy, accuracy,
        precision, recall, specificity, f1_score, roc_auc, training_time, created_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_hash,
        result["algorithm"],
        result["imbalance_strategy"],
        m["accuracy"],
        m["precision"],
        m["recall"],
        m["specificity"],
        m["f1_score"],
        m["roc_auc"],
        m["training_time_seconds"],
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()
    return result


def get_all_experiment_runs(limit: int = 50) -> list[dict]:
    init_classification_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT run_hash, algorithm, imbalance_strategy, metrics_json, created_at
    FROM academic_experiment_runs
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))
    rows = []
    for r in cursor.fetchall():
        rows.append({
            "run_hash": r["run_hash"],
            "algorithm": r["algorithm"],
            "imbalance_strategy": r["imbalance_strategy"],
            "metrics": json.loads(r["metrics_json"]),
            "created_at": r["created_at"]
        })
    conn.close()
    return rows


def get_benchmark_comparison_matrix() -> list[dict]:
    """
    Returns comparative performance across 4 algorithms x 3 imbalance strategies (12 combinations).
    Trains missing combinations on-demand.
    """
    algorithms = ["logistic_regression", "decision_tree", "random_forest", "gaussian_nb"]
    strategies = ["baseline", "balanced", "smote"]
    comparison = []

    for alg in algorithms:
        for strat in strategies:
            try:
                res = run_experiment(
                    algorithm=alg,
                    imbalance_strategy=strat,
                    test_size=0.20,
                    random_state=42
                )
                m = res["metrics"]
                comparison.append({
                    "algorithm": res["model_display_name"],
                    "strategy": strat.title(),
                    "accuracy": m["accuracy"],
                    "precision": m["precision"],
                    "recall": m["recall"],
                    "specificity": m["specificity"],
                    "f1_score": m["f1_score"],
                    "roc_auc": m["roc_auc"],
                    "training_time": m["training_time_seconds"],
                    "run_hash": res["run_hash"]
                })
            except Exception as e:
                print(f"Error benchmark {alg} + {strat}: {e}")

    return comparison


if __name__ == "__main__":
    print("Initializing Classification DB & Pre-warming Benchmark...")
    init_classification_db()
    bench = get_benchmark_comparison_matrix()
    print(f"Benchmark ready with {len(bench)} combinations.")
    df_b = pd.DataFrame(bench)
    print(df_b[["algorithm", "strategy", "accuracy", "f1_score", "roc_auc", "training_time"]])
