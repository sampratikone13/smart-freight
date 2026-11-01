"""
Smart Freight Regression Training & Evaluation Module
- Strict data-leakage prevention
- Selects production model by: lowest RMSE → lowest MAE → highest R²
- Writes authoritative model_metadata.json read by every UI component
"""

import os
import json
import time
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from data_pipeline import load_data, FEATURE_COLUMNS, TARGET_COLUMN, classify_shipping_speed

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
METADATA_PATH = os.path.join(MODEL_DIR, "model_metadata.json")
MODEL_FILE_TMPL = os.path.join(MODEL_DIR, "{key}_pipeline.joblib")

# Key used to locate the production model file on disk
PRODUCTION_KEY = "smart_freight_model"
PRODUCTION_MODEL_PATH = os.path.join(MODEL_DIR, "smart_freight_model_pipeline.joblib")
FEATURE_LIST_PATH = os.path.join(MODEL_DIR, "smart_freight_feature_list.joblib")
PREVIOUS_PRODUCTION_MODEL_PATH = os.path.join(MODEL_DIR, "production_pipeline.joblib")


def _build_preprocessor(numeric_features, categorical_features):
    return ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median"), numeric_features),
            (
                "cat",
                OneHotEncoder(
                    handle_unknown="ignore", min_frequency=20, sparse_output=True
                ),
                categorical_features,
            ),
        ],
        remainder="drop",
    )


def train_and_benchmark_models(save_best: bool = True) -> dict:
    os.makedirs(MODEL_DIR, exist_ok=True)

    print("Loading cleaned dataset …")
    df = load_data()

    X = df[FEATURE_COLUMNS].copy()
    y = df[TARGET_COLUMN].copy()

    # Separate column types using actual pandas dtypes
    numeric_features = [
        col for col in FEATURE_COLUMNS if X[col].dtype not in ["object", "string"]
    ]
    categorical_features = [col for col in FEATURE_COLUMNS if col not in numeric_features]

    print(f"Dataset rows: {len(df):,}  |  Features: {len(FEATURE_COLUMNS)}")
    print(f"Numeric ({len(numeric_features)}): {numeric_features}")
    print(f"Categorical ({len(categorical_features)}): {categorical_features}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )
    print(f"Train: {len(X_train):,}  Test: {len(X_test):,}")

    candidates = {
        "Linear Regression": LinearRegression(),
        "Decision Tree Regressor": DecisionTreeRegressor(max_depth=15, random_state=42),
        "Random Forest Regressor": RandomForestRegressor(
            n_estimators=100, random_state=42, n_jobs=-1
        ),
        "Tuned Random Forest Regressor": RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1,
        ),
    }

    results = {}
    trained_pipelines = {}
    preprocessor = _build_preprocessor(numeric_features, categorical_features)

    for name, regressor in candidates.items():
        print(f"\n[Training] {name} …")
        pipeline = Pipeline(
            steps=[("preprocessor", preprocessor), ("regressor", regressor)]
        )
        t0 = time.time()
        pipeline.fit(X_train, y_train)
        train_time = round(time.time() - t0, 2)

        y_pred = pipeline.predict(X_test)
        mae = round(float(mean_absolute_error(y_test, y_pred)), 4)
        mse = round(float(mean_squared_error(y_test, y_pred)), 4)
        rmse = round(float(np.sqrt(mse)), 4)
        r2 = round(float(r2_score(y_test, y_pred)), 4)

        results[name] = {
            "name": name,
            "mae": mae,
            "mse": mse,
            "rmse": rmse,
            "r2": r2,
            "train_time_sec": train_time,
        }
        trained_pipelines[name] = pipeline
        print(
            f"  MAE={mae}  MSE={mse}  RMSE={rmse}  R²={r2}  Time={train_time}s"
        )

    # ── Model selection: lowest RMSE → lowest MAE → highest R² ──────────────
    sorted_models = sorted(
        results.values(),
        key=lambda m: (m["rmse"], m["mae"], -m["r2"]),
    )
    best = sorted_models[0]
    best_name = best["name"]
    print(f"\n✓ Selected production model: {best_name} (RMSE={best['rmse']})")

    # Feature importances for tree models
    best_pipeline = trained_pipelines[best_name]
    top_features = []
    regressor = best_pipeline.named_steps["regressor"]
    if hasattr(regressor, "feature_importances_"):
        fitted_pre = best_pipeline.named_steps["preprocessor"]
        cat_names = list(
            fitted_pre.named_transformers_["cat"].get_feature_names_out(
                categorical_features
            )
        )
        all_names = numeric_features + cat_names
        imps = regressor.feature_importances_
        feat_imp = sorted(
            zip(all_names, [float(i) for i in imps]),
            key=lambda x: x[1],
            reverse=True,
        )
        top_features = [{"feature": f, "importance": round(imp, 6)} for f, imp in feat_imp[:20]]

    # ── Write authoritative model_metadata.json ──────────────────────────────
    metadata = {
        "dataset_name": "DataCo cleaned supply-chain dataset",
        "dataset_rows_after_cleaning": len(df),
        "test_size": 0.20,
        "random_state": 42,
        "target": TARGET_COLUMN,
        "feature_count": len(FEATURE_COLUMNS),
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "selected_final_model": best_name,
        "metrics": {
            "mae": best["mae"],
            "mse": best["mse"],
            "rmse": best["rmse"],
            "r2": best["r2"],
            "train_time_sec": best["train_time_sec"],
        },
        "model_comparison": sorted(results.values(), key=lambda m: m["rmse"]),
        "top_feature_importances": top_features,
        "evaluated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    if save_best:
        joblib.dump(best_pipeline, PRODUCTION_MODEL_PATH)
        with open(METADATA_PATH, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"Model saved → {PRODUCTION_MODEL_PATH}")
        print(f"Metadata  → {METADATA_PATH}")

    return metadata


# ── Runtime helpers ───────────────────────────────────────────────────────────

_cached_model = None
_cached_metadata = None


def get_loaded_pipeline():
    global _cached_model
    if _cached_model is not None:
        return _cached_model
    if os.path.exists(PRODUCTION_MODEL_PATH):
        _cached_model = joblib.load(PRODUCTION_MODEL_PATH)
        return _cached_model
    if os.path.exists(PREVIOUS_PRODUCTION_MODEL_PATH):
        _cached_model = joblib.load(PREVIOUS_PRODUCTION_MODEL_PATH)
        return _cached_model
    # Not yet trained – train now
    train_and_benchmark_models(save_best=True)
    _cached_model = joblib.load(PRODUCTION_MODEL_PATH)
    return _cached_model


def get_metadata() -> dict:
    global _cached_metadata
    if _cached_metadata is not None:
        return _cached_metadata
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH) as f:
            _cached_metadata = json.load(f)
        return _cached_metadata
    _cached_metadata = train_and_benchmark_models(save_best=True)
    return _cached_metadata


def get_benchmarks() -> dict:
    """Backward-compatible alias used by app.py"""
    return get_metadata()


def predict_single(input_data: dict) -> dict:
    pipeline = get_loaded_pipeline()

    row = {}
    for col in FEATURE_COLUMNS:
        val = input_data.get(col, None)
        if val is None or val == "":
            defaults = {
                "Days for shipment (scheduled)": 4,
                "Order Item Quantity": 1,
                "Sales": 150.0,
                "Order Item Discount": 0.0,
                "Product Price": 150.0,
                "Latitude": 0.0,
                "Longitude": 0.0,
                "order_month": 5,
                "order_day": 15,
                "order_weekday": 2,
                "order_hour": 14,
                "is_weekend": 0,
            }
            val = defaults.get(col, "Standard")
        row[col] = val

    df_single = pd.DataFrame([row])[FEATURE_COLUMNS]

    numeric_cols = [
        "Days for shipment (scheduled)",
        "Order Item Quantity",
        "Sales",
        "Order Item Discount",
        "Product Price",
        "Latitude",
        "Longitude",
        "order_month",
        "order_day",
        "order_weekday",
        "order_hour",
        "is_weekend",
    ]
    for c in numeric_cols:
        df_single[c] = pd.to_numeric(df_single[c], errors="coerce").fillna(0)

    str_cols = [
        "Shipping Mode",
        "Type",
        "Customer Segment",
        "Market",
        "Order Region",
        "Order Country",
        "Category Name",
        "Department Name",
    ]
    for c in str_cols:
        df_single[c] = df_single[c].astype(str).str.strip()

    pred_days_raw = float(pipeline.predict(df_single)[0])
    pred_days_rounded = int(round(pred_days_raw))
    scheduled_days = float(row.get("Days for shipment (scheduled)", 4))
    scheduled_days_display = int(round(scheduled_days))
    diff_raw = pred_days_raw - scheduled_days
    diff_display = pred_days_rounded - scheduled_days_display
    speed_info = classify_shipping_speed(pred_days_rounded)

    return {
        "predicted_shipping_days": pred_days_rounded,
        "predicted_shipping_days_raw": round(pred_days_raw, 4),
        "scheduled_shipping_days": scheduled_days_display,
        "scheduled_shipping_days_raw": scheduled_days,
        "difference_days": diff_display,
        "difference_days_raw": round(diff_raw, 4),
        "is_delayed_risk": bool(diff_raw > 0.3),
        "speed_category": speed_info["category"],
        "badge_class": speed_info["badge_class"],
        "icon": speed_info["icon"],
        "description": speed_info["desc"],
        "disclaimer": (
            "This is an estimated shipping duration, "
            "not a guaranteed delivery date."
        ),
    }


def predict_batch(df_input: pd.DataFrame) -> pd.DataFrame:
    pipeline = get_loaded_pipeline()

    df_features = pd.DataFrame()
    for col in FEATURE_COLUMNS:
        if col in df_input.columns:
            df_features[col] = df_input[col]
        else:
            numeric_defaults = {
                "Days for shipment (scheduled)": 4,
                "Order Item Quantity": 1,
                "Sales": 150.0,
                "Order Item Discount": 0.0,
                "Product Price": 150.0,
                "Latitude": 0.0,
                "Longitude": 0.0,
                "order_month": 5,
                "order_day": 15,
                "order_weekday": 2,
                "order_hour": 14,
                "is_weekend": 0,
            }
            df_features[col] = numeric_defaults.get(col, "Unknown")

    numeric_cols = [
        "Days for shipment (scheduled)",
        "Order Item Quantity",
        "Sales",
        "Order Item Discount",
        "Product Price",
        "Latitude",
        "Longitude",
        "order_month",
        "order_day",
        "order_weekday",
        "order_hour",
        "is_weekend",
    ]
    for c in numeric_cols:
        df_features[c] = pd.to_numeric(df_features[c], errors="coerce").fillna(0)

    str_cols = [
        "Shipping Mode",
        "Type",
        "Customer Segment",
        "Market",
        "Order Region",
        "Order Country",
        "Category Name",
        "Department Name",
    ]
    for c in str_cols:
        df_features[c] = df_features[c].astype(str).str.strip()

    df_features = df_features[FEATURE_COLUMNS]
    preds = pipeline.predict(df_features)
    df_result = df_input.copy()
    df_result["predicted_shipping_days_raw"] = np.round(preds, 4)
    df_result["predicted_shipping_days"] = np.round(preds).astype(int)
    df_result["shipping_speed_category"] = [
        classify_shipping_speed(round(p))["category"] for p in preds
    ]
    return df_result


if __name__ == "__main__":
    train_and_benchmark_models(save_best=True)
