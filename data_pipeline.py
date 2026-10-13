"""
Smart Freight Data Pipeline & Ingestion Engine
Handles dataset loading, validation, leakage prevention, and profiling.
"""

import os
import json
import pandas as pd
import numpy as np

HIERARCHY_PATH = os.path.join(os.path.dirname(__file__), "data", "dropdown_hierarchy.json")
_cached_hierarchy = None

DATA_PATHS = [
    os.path.join(os.path.dirname(__file__), "data", "DataCo_Cleaned-2.csv"),
    os.path.join(os.path.dirname(__file__), "DataCo_Cleaned-2.csv"),
    "DataCo_Cleaned-2.csv",
    "data/DataCo_Cleaned-2.csv"
]

FEATURE_COLUMNS = [
    'Days for shipment (scheduled)',
    'Shipping Mode',
    'Type',
    'Customer Segment',
    'Market',
    'Order Region',
    'Order Country',
    'Order State',
    'Category Name',
    'Department Name',
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

TARGET_COLUMN = 'Days for shipping (real)'

LEAKAGE_COLUMNS = [
    'Late_delivery_risk',
    'Delivery Status',
    'shipping date (DateOrders)',
    'Shipping delays',
    'Days for shipping (real)'
]

_cached_df = None

def get_dataset_path() -> str:
    for path in DATA_PATHS:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("DataCo_Cleaned-2.csv not found in expected locations.")

def load_data(force_reload: bool = False) -> pd.DataFrame:
    global _cached_df
    if _cached_df is not None and not force_reload:
        return _cached_df
    
    path = get_dataset_path()
    df = pd.read_csv(path)
    
    # Ensure proper data types
    numeric_cols = [
        'Days for shipping (real)', 'Days for shipment (scheduled)',
        'Order Item Quantity', 'Sales', 'Order Item Discount',
        'Product Price', 'Latitude', 'Longitude',
        'order_month', 'order_day', 'order_weekday', 'order_hour', 'is_weekend'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # Clean string columns
    str_cols = [
        'Shipping Mode', 'Type', 'Customer Segment', 'Market',
        'Order Region', 'Order Country', 'Order State',
        'Category Name', 'Department Name'
    ]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Derived delay target safely for academic labs
    if 'Days for shipping (real)' in df.columns and 'Days for shipment (scheduled)' in df.columns:
        df['delivery_delay_class'] = (
            df['Days for shipping (real)'] > df['Days for shipment (scheduled)']
        ).astype(int)

    _cached_df = df
    return _cached_df

def get_dataset_overview() -> dict:
    df = load_data()
    return {
        "total_rows": int(len(df)),
        "total_columns": int(df.shape[1]),
        "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
        "total_missing_values": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": list(df.columns)
    }

def get_descriptive_stats() -> list:
    df = load_data()
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    stats_list = []
    
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        q25 = float(series.quantile(0.25))
        q75 = float(series.quantile(0.75))
        iqr = float(q75 - q25)
        skew = float(series.skew()) if len(series) > 2 else 0.0
        
        stats_list.append({
            "column": col,
            "count": int(series.count()),
            "mean": round(float(series.mean()), 3),
            "median": round(float(series.median()), 3),
            "std": round(float(series.std()), 3),
            "min": round(float(series.min()), 3),
            "max": round(float(series.max()), 3),
            "q25": round(q25, 3),
            "q75": round(q75, 3),
            "iqr": round(iqr, 3),
            "skewness": round(skew, 3)
        })
    return stats_list

def get_column_profiles() -> list:
    df = load_data()
    profiles = []
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        total = len(df)
        pct_null = round((null_count / total) * 100, 2)
        unique_cnt = int(df[col].nunique())
        sample_vals = df[col].dropna().unique()[:3].tolist()
        sample_vals_str = [str(v) for v in sample_vals]
        
        profiles.append({
            "name": col,
            "dtype": str(df[col].dtype),
            "null_count": null_count,
            "null_percent": pct_null,
            "unique_count": unique_cnt,
            "samples": sample_vals_str,
            "is_feature": col in FEATURE_COLUMNS,
            "is_target": col == TARGET_COLUMN,
            "is_leakage": col in LEAKAGE_COLUMNS
        })
    return profiles

def get_sample_records(limit: int = 25, offset: int = 0, search: str = "") -> dict:
    df = load_data()
    subset = df
    if search:
        search_lower = search.lower()
        # Search across key string columns
        str_cols = ['Shipping Mode', 'Category Name', 'Order Country', 'Market', 'Type']
        str_cols = [c for c in str_cols if c in df.columns]
        mask = False
        for c in str_cols:
            mask = mask | df[c].astype(str).str.lower().str.contains(search_lower, na=False)
        subset = df[mask]
        
    total_matching = len(subset)
    sliced = subset.iloc[offset:offset + limit]
    
    return {
        "total": total_matching,
        "offset": offset,
        "limit": limit,
        "records": sliced.fillna("").to_dict(orient="records"),
        "columns": list(df.columns)
    }

def get_dropdown_options() -> dict:
    df = load_data()
    
    def get_sorted_uniques(col, max_items=100):
        if col in df.columns:
            uniques = df[col].dropna().unique().tolist()
            uniques = [str(x).strip() for x in uniques if str(x).strip() and str(x) != 'nan']
            uniques = sorted(list(set(uniques)))
            return uniques[:max_items]
        return []

    return {
        "shipping_modes": get_sorted_uniques('Shipping Mode'),
        "types": get_sorted_uniques('Type'),
        "customer_segments": get_sorted_uniques('Customer Segment'),
        "markets": get_sorted_uniques('Market'),
        "order_regions": get_sorted_uniques('Order Region'),
        "order_countries": get_sorted_uniques('Order Country', max_items=200),
        "order_states": get_sorted_uniques('Order State', max_items=200),
        "categories": get_sorted_uniques('Category Name', max_items=100),
        "departments": get_sorted_uniques('Department Name')
    }

def classify_shipping_speed(days: float) -> dict:
    """
    Canonical speed classification applied everywhere (prediction card,
    dashboard charts, watchlist, API response, batch export).

    Rules (same threshold used across the entire codebase):
        days  < 2.0  → Fast / Same-Day
        2.0 <= days < 4.0  → Standard Duration
        days >= 4.0  → Longer Duration
    """
    if days < 2.0:
        return {
            "category": "Fast / Same-Day",
            "badge_class": "badge-success",
            "icon": "zap",
            "desc": "Expedited fulfillment – less than 2 days in transit",
            "watchlist_threshold": False,
        }
    elif days < 4.0:
        return {
            "category": "Standard Duration",
            "badge_class": "badge-primary",
            "icon": "truck",
            "desc": "Standard 2–3 day delivery window",
            "watchlist_threshold": False,
        }
    else:
        return {
            "category": "Longer Duration",
            "badge_class": "badge-warning",
            "icon": "clock",
            "desc": "Cross-border / complex logistics – 4 or more days",
            "watchlist_threshold": True,
        }


# ── Cascading Dropdown Hierarchy ───────────────────────────────────────────────

def _build_and_save_hierarchy():
    """
    Builds the Market→Region→Country→State and
    Department→Category cascading hierarchy from the cleaned dataset
    and writes it to data/dropdown_hierarchy.json.
    """
    df = load_data()

    def safe_sorted(lst):
        return sorted([str(x).strip() for x in lst
                       if str(x).strip() not in ("", "nan")])

    market_regions = {
        str(m): safe_sorted(g.unique())
        for m, g in df.groupby("Market")["Order Region"]
    }
    region_countries = {
        str(r): safe_sorted(g.unique())
        for r, g in df.groupby("Order Region")["Order Country"]
    }
    country_states = {
        str(c): safe_sorted(g.unique())
        for c, g in df.groupby("Order Country")["Order State"]
    }

    # Resolve Electronics → two departments conflict using modal department
    cat_dept = (
        df.groupby("Category Name")["Department Name"]
        .agg(lambda x: x.mode()[0])
        .to_dict()
    )
    cat_dept = {str(k).strip(): str(v).strip() for k, v in cat_dept.items()}

    dept_cats: dict = {}
    for cat, dept in cat_dept.items():
        dept_cats.setdefault(dept, []).append(cat)
    dept_cats = {k: sorted(v) for k, v in dept_cats.items()}

    data = {
        "markets": safe_sorted(df["Market"].unique()),
        "market_regions": market_regions,
        "region_countries": region_countries,
        "country_states": country_states,
        "departments": sorted(dept_cats.keys()),
        "dept_categories": dept_cats,
        "category_department": cat_dept,
        "shipping_modes": safe_sorted(df["Shipping Mode"].unique()),
        "types": safe_sorted(df["Type"].unique()),
        "customer_segments": safe_sorted(df["Customer Segment"].unique()),
        # flat lists used for legacy dropdown fallback
        "order_regions": safe_sorted(df["Order Region"].unique()),
        "order_countries": safe_sorted(df["Order Country"].unique()),
        "order_states": safe_sorted(df["Order State"].unique()),
        "categories": safe_sorted(df["Category Name"].unique()),
    }

    os.makedirs(os.path.dirname(HIERARCHY_PATH), exist_ok=True)
    with open(HIERARCHY_PATH, "w") as fh:
        json.dump(data, fh)
    return data


def get_dropdown_hierarchy() -> dict:
    global _cached_hierarchy
    if _cached_hierarchy is not None:
        return _cached_hierarchy
    if os.path.exists(HIERARCHY_PATH):
        with open(HIERARCHY_PATH) as fh:
            _cached_hierarchy = json.load(fh)
    else:
        _cached_hierarchy = _build_and_save_hierarchy()
    return _cached_hierarchy


def validate_geo_combination(
    market: str, region: str, country: str, state: str
) -> tuple[bool, str]:
    """
    Returns (is_valid, error_message).
    Empty string error_message means valid.
    Validation is permissive if hierarchy is incomplete for a key.
    """
    h = get_dropdown_hierarchy()

    if market and market not in h.get("markets", []):
        return False, f"'{market}' is not a recognised Market in the dataset."

    if market and region:
        allowed_regions = h.get("market_regions", {}).get(market, [])
        if allowed_regions and region not in allowed_regions:
            return (
                False,
                f"Region '{region}' does not belong to Market '{market}'. "
                f"Valid regions: {', '.join(allowed_regions[:6])} …",
            )

    if region and country:
        allowed_countries = h.get("region_countries", {}).get(region, [])
        if allowed_countries and country not in allowed_countries:
            return (
                False,
                f"Country '{country}' is not in Region '{region}'. "
                f"Valid countries: {', '.join(allowed_countries[:6])} …",
            )

    if country and state:
        allowed_states = h.get("country_states", {}).get(country, [])
        if allowed_states and state not in allowed_states:
            return (
                False,
                f"State/Province '{state}' is not in Country '{country}'. "
                f"Valid options: {', '.join(allowed_states[:6])} …",
            )

    return True, ""
