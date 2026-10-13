"""
Smart Freight Data Profiler Module (Lab 0)
Calculates comprehensive schema, missingness, statistical moments,
distribution counts, and data-quality warnings across source & warehouse tables.
Caches output to data/profile_cache.json for instantaneous web rendering.
"""

import os
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

INSTANCE_DIR = os.path.join(os.path.dirname(__file__), "instance")
DB_PATH = os.path.join(INSTANCE_DIR, "smart_freight.db")
CACHE_PATH = os.path.join(os.path.dirname(__file__), "data", "profile_cache.json")
CSV_PATH = os.path.join(os.path.dirname(__file__), "DataCo_Cleaned-2.csv")

SENSITIVE_LEAKAGE_COLUMNS = [
    'Late_delivery_risk',
    'Delivery Status',
    'shipping date (DateOrders)',
    'Shipping delays',
    'Days for shipping (real)'
]

PII_SUSPECT_COLUMNS = [
    'Customer Email', 'Customer Password', 'Customer Fname', 'Customer Lname',
    'Customer Street', 'Order Zipcode', 'Product Description'
]


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def profile_dataframe(df: pd.DataFrame, table_key: str, table_display_name: str, table_type: str) -> dict:
    total_rows = int(len(df))
    total_cols = int(df.shape[1])
    total_cells = total_rows * total_cols
    
    # Duplicate rows
    duplicate_rows = int(df.duplicated().sum())

    total_missing_cells = int(df.isna().sum().sum())
    missing_cell_pct = round((total_missing_cells / total_cells * 100) if total_cells > 0 else 0.0, 2)

    column_profiles = []
    numeric_count = 0
    categorical_count = 0

    missing_chart_data = []
    type_distribution = {}

    for col in df.columns:
        series = df[col]
        dtype_str = str(series.dtype)
        is_numeric = pd.api.types.is_numeric_dtype(series)

        # Standardize type classification
        if is_numeric:
            numeric_count += 1
            type_category = "Numeric (Float)" if "float" in dtype_str else "Numeric (Integer)"
        else:
            categorical_count += 1
            type_category = "Categorical / Text"

        type_distribution[type_category] = type_distribution.get(type_category, 0) + 1

        null_count = int(series.isna().sum())
        missing_pct = round((null_count / total_rows * 100) if total_rows > 0 else 0.0, 2)
        non_null_count = total_rows - null_count
        unique_count = int(series.nunique(dropna=True))

        missing_chart_data.append({
            "column": col,
            "missing_pct": missing_pct,
            "missing_count": null_count
        })

        # Quality warnings
        warnings = []
        if null_count > 0:
            warnings.append({
                "type": "missing_values",
                "level": "warning",
                "label": f"{null_count} missing ({missing_pct}%)"
            })
        if unique_count == 1:
            warnings.append({
                "type": "constant_column",
                "level": "danger",
                "label": "Zero variance (constant)"
            })
        elif unique_count == total_rows and total_rows > 10:
            warnings.append({
                "type": "unique_identifier",
                "level": "info",
                "label": "Potential primary key / ID"
            })
        elif (unique_count > 0.5 * total_rows) and not is_numeric and total_rows > 100:
            warnings.append({
                "type": "high_cardinality",
                "level": "warning",
                "label": f"High cardinality ({unique_count} distinct)"
            })

        if col in SENSITIVE_LEAKAGE_COLUMNS:
            warnings.append({
                "type": "target_leakage",
                "level": "danger",
                "label": "ML Target Leakage (Excluded from Features)"
            })

        if any(pii.lower() in col.lower() for pii in PII_SUSPECT_COLUMNS):
            warnings.append({
                "type": "pii_risk",
                "level": "danger",
                "label": "PII Risk Attribute"
            })

        # Numerical vs Categorical statistics
        num_stats = None
        cat_stats = None

        if is_numeric and non_null_count > 0:
            clean_num = series.dropna()
            mean_val = float(clean_num.mean())
            median_val = float(clean_num.median())
            std_val = float(clean_num.std()) if len(clean_num) > 1 else 0.0
            min_val = float(clean_num.min())
            max_val = float(clean_num.max())
            q25 = float(clean_num.quantile(0.25))
            q75 = float(clean_num.quantile(0.75))
            iqr = round(q75 - q25, 4)
            skew_val = float(clean_num.skew()) if len(clean_num) > 2 else 0.0

            # Histogram bins (10 equal intervals)
            hist_counts, bin_edges = np.histogram(clean_num, bins=10)
            hist_data = {
                "bins": [f"{round(bin_edges[i], 1)}–{round(bin_edges[i+1], 1)}" for i in range(len(hist_counts))],
                "counts": [int(c) for c in hist_counts]
            }

            num_stats = {
                "mean": round(mean_val, 4),
                "median": round(median_val, 4),
                "std": round(std_val, 4),
                "min": round(min_val, 4),
                "max": round(max_val, 4),
                "q25": round(q25, 4),
                "q75": round(q75, 4),
                "iqr": iqr,
                "skewness": round(skew_val, 4),
                "histogram": hist_data
            }
        else:
            # Top categorical values
            val_counts = series.value_counts(dropna=True).head(10)
            top_values = [
                {
                    "value": str(idx),
                    "count": int(cnt),
                    "percentage": round((cnt / total_rows * 100) if total_rows > 0 else 0.0, 2)
                }
                for idx, cnt in val_counts.items()
            ]
            cat_stats = {
                "top_value": top_values[0]["value"] if top_values else "N/A",
                "top_count": top_values[0]["count"] if top_values else 0,
                "top_percentage": top_values[0]["percentage"] if top_values else 0.0,
                "distribution": top_values
            }

        column_profiles.append({
            "name": col,
            "data_type": dtype_str,
            "type_category": type_category,
            "is_numeric": is_numeric,
            "non_null_count": non_null_count,
            "null_count": null_count,
            "missing_pct": missing_pct,
            "unique_count": unique_count,
            "warnings": warnings,
            "numeric_stats": num_stats,
            "categorical_stats": cat_stats
        })

    # Filter out sensitive columns before saving preview
    safe_cols = [c for c in df.columns if not any(pii.lower() in c.lower() for pii in PII_SUSPECT_COLUMNS)]
    preview_rows = df[safe_cols].head(50).fillna("").to_dict(orient="records")

    return {
        "table_key": table_key,
        "table_display_name": table_display_name,
        "table_type": table_type,
        "summary": {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "total_cells": total_cells,
            "missing_cells": total_missing_cells,
            "missing_cell_pct": missing_cell_pct,
            "duplicate_rows": duplicate_rows,
            "numeric_columns_count": numeric_count,
            "categorical_columns_count": categorical_count,
        },
        "column_profiles": column_profiles,
        "missing_chart_data": sorted(missing_chart_data, key=lambda x: x["missing_pct"], reverse=True),
        "type_distribution": type_distribution,
        "preview_columns": safe_cols,
        "preview_rows": preview_rows
    }


def generate_all_profiles() -> dict:
    """
    Profiles:
    1. Cleaned source dataset (DataCo_Cleaned-2.csv)
    2. FactOrders
    3. DimDate
    4. DimGeography
    5. DimProduct
    6. DimCustomer
    7. DimShipping
    """
    profiles = {}
    timestamp = datetime.now().isoformat()

    # 1. Source dataset
    if os.path.exists(CSV_PATH):
        df_src = pd.read_csv(CSV_PATH)
        profiles["source_dataset"] = profile_dataframe(
            df_src, "source_dataset", "Cleaned Source Dataset", "Source CSV"
        )

    # 2–7. Warehouse tables from SQLite
    conn = get_db_connection()
    wh_tables = [
        ("FactOrders", "FactOrders (Grain: Order Line)", "Fact Table"),
        ("FactShippingPerformance", "FactShippingPerformance (Galaxy Fact)", "Fact Table"),
        ("DimDate", "DimDate (Calendar & Time)", "Dimension Table"),
        ("DimGeography", "DimGeography (Spatial Hierarchy)", "Dimension Table"),
        ("DimProduct", "DimProduct (Merchandise Catalog)", "Dimension Table"),
        ("DimCustomer", "DimCustomer (Sanitized Demographics)", "Dimension Table"),
        ("DimShipping", "DimShipping (Logistics & Payment)", "Dimension Table")
    ]

    for tbl_name, display_name, tbl_type in wh_tables:
        try:
            df_tbl = pd.read_sql_query(f"SELECT * FROM {tbl_name}", conn)
            profiles[tbl_name] = profile_dataframe(df_tbl, tbl_name, display_name, tbl_type)
        except Exception as e:
            print(f"Warning: could not profile table {tbl_name}: {e}")

    conn.close()

    cache_payload = {
        "generated_at": timestamp,
        "table_keys": list(profiles.keys()),
        "table_catalog": [
            {
                "key": k,
                "name": p["table_display_name"],
                "type": p["table_type"],
                "rows": p["summary"]["total_rows"],
                "cols": p["summary"]["total_columns"]
            }
            for k, p in profiles.items()
        ],
        "tables": profiles,
        "academic_interpretation": {
            "what_does_this_mean": "Data profiling audits the statistical validity, completeness, and hygiene of raw records prior to dimensional ETL and machine learning. In Smart Freight, identifying target leakage attributes (such as post-delivery timestamps) ensures the regression model learns genuine causal predictors of shipment duration rather than memorizing historical outcomes.",
            "technical_moments": "We compute central tendency (arithmetic mean, 50th percentile median), dispersion (standard deviation, interquartile range IQR = Q75 - Q25), and shape asymmetry via the Fisher-Pearson coefficient of skewness. High positive skew indicates long-tail outlier shipments that require robust tree partitioning."
        }
    }

    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(cache_payload, f, indent=2)

    return cache_payload


def get_profile_cache() -> dict:
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return generate_all_profiles()


def get_table_profile(table_key: str) -> dict | None:
    cache = get_profile_cache()
    return cache.get("tables", {}).get(table_key)


if __name__ == "__main__":
    print("Generating profile cache...")
    start = datetime.now()
    res = generate_all_profiles()
    dur = (datetime.now() - start).total_seconds()
    print(f"Profiling complete in {dur:.2f}s across {len(res['tables'])} tables.")
    for k, t in res["tables"].items():
        print(f" - {k}: {t['summary']['total_rows']} rows, {t['summary']['total_columns']} cols")
