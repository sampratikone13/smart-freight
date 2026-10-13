"""
Smart Freight Supervised Classification Pipeline (Labs 4–5)
- Predicts binary shipping delay risk: delivery_delay_class = (Days real > Days scheduled)
- 0 = On-time / early shipment
- 1 = Delayed shipment
- Strict Leakage Prevention: Excludes all post-fulfillment and target-derived columns
- Fixed stratified train/test split
- Class-imbalance strategies: Baseline, Balanced Class Weights, SMOTE (SMOTENC on training only)
"""

import os
import time
import json
import hashlib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    roc_curve, precision_recall_curve
)
from imblearn.over_sampling import SMOTENC

CSV_PATH = os.path.join(os.path.dirname(__file__), "DataCo_Cleaned-2.csv")

# Strict Feature Separation
LEAKAGE_PROHIBITED_FEATURES = [
    'Days for shipping (real)',
    'Late_delivery_risk',
    'Delivery Status',
    'shipping date (DateOrders)',
    'Shipping delays',
    'delivery_delay_class'
]

NUMERIC_FEATURES = [
    'Days for shipment (scheduled)',
    'Order Item Quantity',
    'Sales',
    'Order Item Discount',
    'Product Price',
    'Latitude',
    'Longitude',
    'order_month',
    'order_day',
    'order_weekday',
    'order_hour',
    'is_weekend'
]

CATEGORICAL_FEATURES = [
    'Shipping Mode',
    'Type',
    'Customer Segment',
    'Market',
    'Order Region',
    'Order Country',
    'Order State',
    'Category Name',
    'Department Name'
]

ALLOWED_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def load_classification_data(csv_path: str = CSV_PATH) -> tuple[pd.DataFrame, pd.Series]:
    """Loads dataset and extracts non-leaking features + binary delay target."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset CSV not found at {csv_path}")

    df = pd.read_csv(csv_path)

    # 1. Target Definition
    # 0 = On-time or early, 1 = Delayed
    y = (df['Days for shipping (real)'] > df['Days for shipment (scheduled)']).astype(int)

    # 2. Clean Feature Matrix
    X = pd.DataFrame(index=df.index)
    for col in NUMERIC_FEATURES:
        if col in df.columns:
            X[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        else:
            X[col] = 0.0

    for col in CATEGORICAL_FEATURES:
        if col in df.columns:
            X[col] = df[col].fillna('Unknown').astype(str).str.strip()
        else:
            X[col] = 'Unknown'

    return X, y


def build_experiment_hash(
    algorithm: str,
    imbalance_strategy: str,
    hyperparams: dict,
    test_size: float = 0.2,
    random_state: int = 42,
    row_count: int = 59606
) -> str:
    """Generates deterministic MD5 hash for experiment run caching."""
    h_dict = {
        "alg": algorithm.lower().strip(),
        "imb": imbalance_strategy.lower().strip(),
        "hp": sorted(hyperparams.items()),
        "test_size": round(test_size, 3),
        "seed": random_state,
        "rows": row_count
    }
    raw = json.dumps(h_dict, sort_keys=True)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def downsample_curve_points(x_vals, y_vals, max_points: int = 40) -> list[dict]:
    """Downsamples curve coordinates for fast, smooth Chart.js rendering."""
    n = len(x_vals)
    if n <= max_points:
        return [{"x": round(float(x), 4), "y": round(float(y), 4)} for x, y in zip(x_vals, y_vals)]
    indices = np.linspace(0, n - 1, max_points, dtype=int)
    return [{"x": round(float(x_vals[i]), 4), "y": round(float(y_vals[i]), 4)} for i in indices]


def train_and_evaluate_classifier(
    algorithm: str = "random_forest",
    imbalance_strategy: str = "baseline",
    hyperparams: dict = None,
    test_size: float = 0.20,
    random_state: int = 42
) -> dict:
    """
    Executes a complete classification experiment:
    1. Stratified train/test split on real dataset
    2. Encoders/Scalers fit strictly on training set
    3. Resampling (if SMOTE) applied strictly to training set
    4. Evaluates on held-out test set
    5. Returns metrics, confusion matrix, ROC/PR curves, and feature importances
    """
    start_total = time.time()
    hyperparams = hyperparams or {}

    X, y = load_classification_data()
    total_samples = len(y)

    # 1. Fixed Stratified Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )

    class_counts_original = {
        "class_0_ontime": int((y == 0).sum()),
        "class_1_delayed": int((y == 1).sum()),
        "imbalance_ratio": round(float((y == 1).sum() / (y == 0).sum()), 2)
    }

    train_class_counts_before = {
        "class_0_ontime": int((y_train == 0).sum()),
        "class_1_delayed": int((y_train == 1).sum()),
    }

    # 2. Categorical & Numerical Preprocessing
    # Encoders fit STRICTLY on X_train to prevent leakage
    oe = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
    X_train_cat = oe.fit_transform(X_train[CATEGORICAL_FEATURES])
    X_test_cat = oe.transform(X_test[CATEGORICAL_FEATURES])

    scaler = StandardScaler()
    X_train_num = scaler.fit_transform(X_train[NUMERIC_FEATURES])
    X_test_num = scaler.transform(X_test[NUMERIC_FEATURES])

    X_train_enc = np.hstack([X_train_num, X_train_cat])
    X_test_enc = np.hstack([X_test_num, X_test_cat])

    feature_names = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    cat_indices = list(range(len(NUMERIC_FEATURES), len(feature_names)))

    # 3. Class-Imbalance Handling
    train_class_counts_after = dict(train_class_counts_before)
    imbalance_method_used = imbalance_strategy.lower().strip()

    if imbalance_method_used == "smote":
        # SMOTENC resamples categorical ordinals using mode interpolation
        smotenc = SMOTENC(categorical_features=cat_indices, random_state=random_state)
        X_train_proc, y_train_proc = smotenc.fit_resample(X_train_enc, y_train)
        train_class_counts_after = {
            "class_0_ontime": int((y_train_proc == 0).sum()),
            "class_1_delayed": int((y_train_proc == 1).sum()),
        }
    else:
        X_train_proc, y_train_proc = X_train_enc, y_train

    # 4. Instantiate Model
    alg_key = algorithm.lower().strip()
    use_balanced = (imbalance_method_used == "balanced")

    if alg_key in ["logistic_regression", "lr"]:
        c_val = float(hyperparams.get("C", 1.0))
        max_iter = int(hyperparams.get("max_iter", 1000))
        model = LogisticRegression(
            C=c_val,
            max_iter=max_iter,
            class_weight="balanced" if use_balanced else None,
            random_state=random_state,
            solver="lbfgs"
        )
        model_display_name = "Logistic Regression"

    elif alg_key in ["decision_tree", "dt"]:
        max_depth = int(hyperparams.get("max_depth", 10))
        min_samples_split = int(hyperparams.get("min_samples_split", 10))
        model = DecisionTreeClassifier(
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            class_weight="balanced" if use_balanced else None,
            random_state=random_state
        )
        model_display_name = "Decision Tree Classifier"

    elif alg_key in ["random_forest", "rf"]:
        n_estimators = int(hyperparams.get("n_estimators", 100))
        max_depth = int(hyperparams.get("max_depth", 12))
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            class_weight="balanced" if use_balanced else None,
            random_state=random_state,
            n_jobs=-1
        )
        model_display_name = "Random Forest Classifier"

    elif alg_key in ["gaussian_nb", "gnb", "naive_bayes"]:
        # GaussianNB does not have class_weight, adjust priors if balanced requested
        priors = [0.5, 0.5] if use_balanced else None
        model = GaussianNB(priors=priors)
        model_display_name = "Gaussian Naive Bayes"

    else:
        raise ValueError(f"Unsupported algorithm '{algorithm}'. Choose logistic_regression, decision_tree, random_forest, or gaussian_nb.")

    # 5. Fit Model & Measure Training Duration
    t_train_start = time.time()
    model.fit(X_train_proc, y_train_proc)
    training_time_sec = round(time.time() - t_train_start, 4)

    # 6. Evaluate strictly on held-out X_test_enc
    y_pred = model.predict(X_test_enc)
    
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_test_enc)[:, 1]
    else:
        # Fallback for models without proba
        y_prob = model.decision_function(X_test_enc)

    # 7. Metrics Computation
    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    
    # Specificity = TN / (TN + FP)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

    try:
        auc = float(roc_auc_score(y_test, y_prob))
    except Exception:
        auc = 0.5

    # 8. Curves Data for Interactive Visuals
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    prec_curve, rec_curve, _ = precision_recall_curve(y_test, y_prob)
    roc_points = downsample_curve_points(fpr, tpr, max_points=35)
    pr_points = downsample_curve_points(rec_curve, prec_curve, max_points=35)

    # 9. Confusion Matrix Object
    cm_dict = {
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
        "tn_pct": round(float(tn / len(y_test) * 100), 1),
        "fp_pct": round(float(fp / len(y_test) * 100), 1),
        "fn_pct": round(float(fn / len(y_test) * 100), 1),
        "tp_pct": round(float(tp / len(y_test) * 100), 1),
    }

    # 10. Classification Report Dict
    clf_rep = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    # 11. Feature Importance Extraction
    importances = []
    if hasattr(model, "feature_importances_"):
        raw_imp = model.feature_importances_
        importances = sorted(
            [{"feature": f, "importance": round(float(imp), 4)} for f, imp in zip(feature_names, raw_imp)],
            key=lambda x: x["importance"],
            reverse=True
        )[:12]
    elif hasattr(model, "coef_"):
        raw_coef = np.abs(model.coef_[0])
        importances = sorted(
            [{"feature": f, "importance": round(float(c), 4)} for f, c in zip(feature_names, raw_coef)],
            key=lambda x: x["importance"],
            reverse=True
        )[:12]

    run_hash = build_experiment_hash(
        algorithm, imbalance_strategy, hyperparams,
        test_size, random_state, total_samples
    )

    total_duration = round(time.time() - start_total, 3)

    return {
        "run_hash": run_hash,
        "algorithm": alg_key,
        "model_display_name": model_display_name,
        "imbalance_strategy": imbalance_method_used,
        "hyperparams": hyperparams,
        "test_size": test_size,
        "random_state": random_state,
        "total_dataset_rows": total_samples,
        "class_counts_original": class_counts_original,
        "train_class_counts_before": train_class_counts_before,
        "train_class_counts_after": train_class_counts_after,
        "metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "specificity": round(spec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(auc, 4),
            "training_time_seconds": training_time_sec
        },
        "confusion_matrix": cm_dict,
        "classification_report": clf_rep,
        "curves": {
            "roc_curve": roc_points,
            "pr_curve": pr_points
        },
        "feature_importances": importances,
        "total_execution_seconds": total_duration,
        "leakage_prevention_notice": {
            "status": "Verified",
            "excluded_columns": LEAKAGE_PROHIBITED_FEATURES,
            "explanation": "Target delay class is derived solely for academic evaluation. Post-delivery columns (Late_delivery_risk, Days real, Delivery Status) are strictly prohibited from the feature matrix to avoid 100% artificial accuracy."
        }
    }


if __name__ == "__main__":
    print("Testing classification pipeline with Random Forest + SMOTE...")
    res = train_and_evaluate_classifier(
        algorithm="random_forest",
        imbalance_strategy="smote",
        hyperparams={"n_estimators": 50, "max_depth": 10}
    )
    print("Execution Success! Metrics:")
    print(json.dumps(res["metrics"], indent=2))
