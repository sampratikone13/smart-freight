"""
Smart Freight Multi-Dimensional OLAP Engine (Lab 9)
Implements:
- True warehouse OLAP operations directly over SQLite Star Schema:
    - FactOrders (59,606 rows) joined with DimDate, DimGeography, DimProduct, DimCustomer, DimShipping
- Core OLAP Operations:
    1. Roll-up (e.g. City -> State -> Country -> Region -> Market; Hour -> Weekday -> Month -> Quarter -> Year)
    2. Drill-down (e.g. Market -> Region -> Country -> State -> City)
    3. Slice (filter by a single dimension member)
    4. Dice (multi-dimensional sub-cube slicing across 2+ attributes)
    5. Pivot Summary (2D Cross-Tab matrix of any measure across two dimensions)
- Pre-aggregated measures:
    - order_count
    - total_sales
    - avg_actual_shipping_days
    - avg_scheduled_shipping_days
    - avg_order_quantity
    - avg_discount
    - delayed_order_count
    - delay_rate (%)
- Generated SQL query string and query execution plan for academic Viva Voce inspection
- Full CSV and JSON export endpoints
"""

import os
import time
import json
import sqlite3
import pandas as pd
import numpy as np

INSTANCE_DIR = os.path.join(os.path.dirname(__file__), "instance")
DB_PATH = os.path.join(INSTANCE_DIR, "smart_freight.db")


def get_db_connection():
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


DIMENSION_MAP = {
    # Geography Hierarchy
    "market": {"col": "dg.market", "label": "Market", "table": "DimGeography", "level": 1},
    "region": {"col": "dg.order_region", "label": "Region", "table": "DimGeography", "level": 2},
    "country": {"col": "dg.order_country", "label": "Country", "table": "DimGeography", "level": 3},
    "state": {"col": "dg.order_state", "label": "State", "table": "DimGeography", "level": 4},
    "city": {"col": "dg.order_city", "label": "City", "table": "DimGeography", "level": 5},

    # Time Hierarchy
    "year": {"col": "dd.year", "label": "Year", "table": "DimDate", "level": 1},
    "quarter": {"col": "dd.quarter", "label": "Quarter", "table": "DimDate", "level": 2},
    "month": {"col": "dd.month_name", "label": "Month", "table": "DimDate", "level": 3},
    "weekday": {"col": "dd.weekday_name", "label": "Weekday", "table": "DimDate", "level": 4},
    "hour": {"col": "dd.hour", "label": "Hour", "table": "DimDate", "level": 5},

    # Product Hierarchy
    "department": {"col": "dp.department_name", "label": "Department", "table": "DimProduct", "level": 1},
    "category": {"col": "dp.category_name", "label": "Category", "table": "DimProduct", "level": 2},

    # Shipping
    "shipping_mode": {"col": "ds.shipping_mode", "label": "Shipping Mode", "table": "DimShipping", "level": 1},

    # Customer
    "customer_segment": {"col": "dc.customer_segment", "label": "Customer Segment", "table": "DimCustomer", "level": 1}
}

MEASURE_MAP = {
    "order_count": {
        "sql": "COUNT(*)",
        "alias": "order_count",
        "label": "Order Count",
        "format": "{:,}"
    },
    "total_sales": {
        "sql": "ROUND(SUM(fo.sales), 2)",
        "alias": "total_sales",
        "label": "Total Sales ($)",
        "format": "${:,.2f}"
    },
    "avg_actual_shipping_days": {
        "sql": "ROUND(AVG(fo.actual_shipping_days), 2)",
        "alias": "avg_actual_shipping_days",
        "label": "Avg Actual Days",
        "format": "{:.2f}"
    },
    "avg_scheduled_shipping_days": {
        "sql": "ROUND(AVG(fo.scheduled_shipping_days), 2)",
        "alias": "avg_scheduled_shipping_days",
        "label": "Avg Scheduled Days",
        "format": "{:.2f}"
    },
    "avg_order_quantity": {
        "sql": "ROUND(AVG(fo.quantity), 2)",
        "alias": "avg_order_quantity",
        "label": "Avg Quantity",
        "format": "{:.2f}"
    },
    "avg_discount": {
        "sql": "ROUND(AVG(fo.discount), 2)",
        "alias": "avg_discount",
        "label": "Avg Discount ($)",
        "format": "${:.2f}"
    },
    "delayed_order_count": {
        "sql": "SUM(CASE WHEN fo.actual_shipping_days > fo.scheduled_shipping_days THEN 1 ELSE 0 END)",
        "alias": "delayed_order_count",
        "label": "Delayed Orders",
        "format": "{:,}"
    },
    "delay_rate": {
        "sql": "ROUND(AVG(CASE WHEN fo.actual_shipping_days > fo.scheduled_shipping_days THEN 1.0 ELSE 0.0 END) * 100, 1)",
        "alias": "delay_rate",
        "label": "Delay Rate (%)",
        "format": "{:.1f}%"
    }
}

HIERARCHIES = {
    "geography": ["market", "region", "country", "state", "city"],
    "time": ["year", "quarter", "month", "weekday", "hour"],
    "product": ["department", "category"]
}


_cached_dimension_members = None


def get_dimension_members() -> dict:
    """
    Fetches distinct unique members for all OLAP dimensions from the SQLite warehouse tables.
    """
    global _cached_dimension_members
    if _cached_dimension_members is not None:
        return _cached_dimension_members

    conn = get_db_connection()
    cursor = conn.cursor()
    members = {}

    queries = {
        "market": "SELECT DISTINCT market FROM DimGeography WHERE market != 'Unknown' ORDER BY market",
        "region": "SELECT DISTINCT order_region FROM DimGeography WHERE order_region != 'Unknown' ORDER BY order_region LIMIT 30",
        "country": "SELECT DISTINCT order_country FROM DimGeography WHERE order_country != 'Unknown' ORDER BY order_country LIMIT 40",
        "year": "SELECT DISTINCT year FROM DimDate ORDER BY year",
        "quarter": "SELECT DISTINCT quarter FROM DimDate ORDER BY quarter",
        "month": "SELECT DISTINCT month_name FROM DimDate ORDER BY month",
        "weekday": "SELECT DISTINCT weekday_name FROM DimDate ORDER BY weekday",
        "department": "SELECT DISTINCT department_name FROM DimProduct WHERE department_name != 'Unknown' ORDER BY department_name",
        "category": "SELECT DISTINCT category_name FROM DimProduct WHERE category_name != 'Unknown' ORDER BY category_name",
        "shipping_mode": "SELECT DISTINCT shipping_mode FROM DimShipping WHERE shipping_mode != 'Unknown' ORDER BY shipping_mode",
        "customer_segment": "SELECT DISTINCT customer_segment FROM DimCustomer WHERE customer_segment != 'Unknown' ORDER BY customer_segment"
    }

    for dim_key, sql in queries.items():
        try:
            cursor.execute(sql)
            members[dim_key] = [r[0] for r in cursor.fetchall() if r[0] is not None]
        except Exception:
            members[dim_key] = []

    conn.close()
    _cached_dimension_members = members
    return _cached_dimension_members


def build_olap_sql(
    dimensions: list,
    filters: dict = None,
    measures: list = None,
    sort_by: str = None,
    sort_dir: str = "DESC",
    limit: int = 100
) -> tuple[str, list, list]:
    """
    Constructs parameterized Star-Schema SQL query joining FactOrders to relevant dimension tables.
    """
    if not dimensions:
        dimensions = ["market", "shipping_mode"]

    # Filter out invalid dimensions
    valid_dims = [d for d in dimensions if d in DIMENSION_MAP]
    if not valid_dims:
        valid_dims = ["market"]

    if not measures:
        measures = list(MEASURE_MAP.keys())
    valid_measures = [m for m in measures if m in MEASURE_MAP]
    if not valid_measures:
        valid_measures = ["order_count", "total_sales", "avg_actual_shipping_days", "delayed_order_count"]

    # Collect required tables to join
    joined_tables = set()
    select_dims = []
    group_by_cols = []

    for d in valid_dims:
        info = DIMENSION_MAP[d]
        joined_tables.add(info["table"])
        select_dims.append(f"{info['col']} AS {d}")
        group_by_cols.append(info["col"])

    select_measures = [f"{MEASURE_MAP[m]['sql']} AS {m}" for m in valid_measures]

    # Build FROM clause with dynamic JOINs
    from_clauses = ["FactOrders fo"]
    if "DimGeography" in joined_tables:
        from_clauses.append("JOIN DimGeography dg ON fo.geography_key = dg.geography_key")
    if "DimDate" in joined_tables:
        from_clauses.append("JOIN DimDate dd ON fo.date_key = dd.date_key")
    if "DimProduct" in joined_tables:
        from_clauses.append("JOIN DimProduct dp ON fo.product_key = dp.product_key")
    if "DimCustomer" in joined_tables:
        from_clauses.append("JOIN DimCustomer dc ON fo.customer_key = dc.customer_key")
    if "DimShipping" in joined_tables:
        from_clauses.append("JOIN DimShipping ds ON fo.shipping_key = ds.shipping_key")

    # Build WHERE clause for Slice and Dice
    where_clauses = []
    params = []

    if filters:
        for f_dim, f_val in filters.items():
            if f_dim in DIMENSION_MAP and f_val is not None and f_val != "":
                col = DIMENSION_MAP[f_dim]["col"]
                table = DIMENSION_MAP[f_dim]["table"]
                # Ensure filter table is joined
                if table not in joined_tables:
                    if table == "DimGeography":
                        from_clauses.append("JOIN DimGeography dg ON fo.geography_key = dg.geography_key")
                    elif table == "DimDate":
                        from_clauses.append("JOIN DimDate dd ON fo.date_key = dd.date_key")
                    elif table == "DimProduct":
                        from_clauses.append("JOIN DimProduct dp ON fo.product_key = dp.product_key")
                    elif table == "DimCustomer":
                        from_clauses.append("JOIN DimCustomer dc ON fo.customer_key = dc.customer_key")
                    elif table == "DimShipping":
                        from_clauses.append("JOIN DimShipping ds ON fo.shipping_key = ds.shipping_key")
                    joined_tables.add(table)

                if isinstance(f_val, list):
                    # Dice multi-member selection
                    if len(f_val) > 0:
                        placeholders = ", ".join(["?"] * len(f_val))
                        where_clauses.append(f"{col} IN ({placeholders})")
                        params.extend([str(v) for v in f_val])
                else:
                    # Single value slice
                    where_clauses.append(f"{col} = ?")
                    params.append(str(f_val))

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    select_all = ", ".join(select_dims + select_measures)
    from_sql = "\n    ".join(from_clauses)
    group_sql = ", ".join(group_by_cols)

    order_sql = ""
    if sort_by and (sort_by in valid_measures or sort_by in valid_dims):
        direction = "ASC" if str(sort_dir).upper() == "ASC" else "DESC"
        order_sql = f"ORDER BY {sort_by} {direction}"
    else:
        order_sql = "ORDER BY order_count DESC"

    limit_sql = f"LIMIT {int(limit)}" if limit > 0 else ""

    sql = f"""SELECT 
    {select_all}
FROM {from_sql}
{where_sql}
GROUP BY {group_sql}
{order_sql}
{limit_sql};"""

    return sql, params, valid_dims


def execute_olap_query(
    dimensions: list = None,
    filters: dict = None,
    measures: list = None,
    sort_by: str = None,
    sort_dir: str = "DESC",
    limit: int = 100,
    operation: str = "query"
) -> dict:
    """
    Executes an OLAP query over the warehouse tables and returns tabular data, summary KPIs, and SQL explanation.
    """
    start_time = time.time()
    sql, params, valid_dims = build_olap_sql(
        dimensions=dimensions,
        filters=filters,
        measures=measures,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit
    )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    raw_rows = [dict(r) for r in cursor.fetchall()]

    exec_time_ms = round((time.time() - start_time) * 1000, 2)

    # Compute overall cube summary totals for top KPIs
    total_orders = sum(r.get("order_count", 0) for r in raw_rows)
    total_sales = round(sum(r.get("total_sales", 0.0) for r in raw_rows), 2)
    delayed_orders = sum(r.get("delayed_order_count", 0) for r in raw_rows)
    
    # Safely compute avg actual shipping days if present in result columns
    has_actual_days = any("avg_actual_shipping_days" in r for r in raw_rows)
    if has_actual_days and total_orders > 0 and raw_rows:
        weights = [r.get("order_count", 1) for r in raw_rows]
        vals = [r.get("avg_actual_shipping_days", 0.0) for r in raw_rows]
        avg_actual_days = round(float(np.average(vals, weights=weights)), 2)
    else:
        avg_actual_days = 0.0

    delay_rate = round((delayed_orders / total_orders) * 100, 1) if (total_orders > 0 and delayed_orders > 0) else 0.0

    conn.close()

    # Determine operation name if not provided
    op_name = operation
    if filters and len(filters) > 1 and op_name == "query":
        op_name = "Dice Sub-Cube"
    elif filters and len(filters) == 1 and op_name == "query":
        op_name = "Slice Dimension"
    elif op_name == "query":
        op_name = "Multi-Dimensional Aggregation"

    return {
        "status": "success",
        "operation": op_name,
        "dimensions": valid_dims,
        "filters": filters or {},
        "records_count": len(raw_rows),
        "execution_time_ms": exec_time_ms,
        "summary": {
            "total_orders": total_orders,
            "total_sales": total_sales,
            "avg_actual_days": avg_actual_days,
            "delayed_orders": delayed_orders,
            "delay_rate": delay_rate
        },
        "data": raw_rows,
        "rows": raw_rows,
        "sql_query": sql,
        "parameters": params
    }


def execute_olap_pivot(
    row_dimension: str = "market",
    col_dimension: str = "shipping_mode",
    measure: str = "avg_actual_shipping_days",
    filters: dict = None
) -> dict:
    """
    Computes a 2D cross-tab matrix of a measure across row and column dimensions.
    """
    start_time = time.time()
    row_dim = row_dimension if row_dimension in DIMENSION_MAP else "market"
    col_dim = col_dimension if col_dimension in DIMENSION_MAP else "shipping_mode"
    msr = measure if measure in MEASURE_MAP else "avg_actual_shipping_days"

    res = execute_olap_query(
        dimensions=[row_dim, col_dim],
        filters=filters,
        measures=[msr, "order_count"],
        limit=500,
        operation="Pivot Cross-Tab"
    )

    df = pd.DataFrame(res["data"])
    if df.empty:
        return {
            "status": "success",
            "operation": "Pivot Summary",
            "row_dimension": row_dim,
            "col_dimension": col_dim,
            "measure": msr,
            "pivot_columns": [],
            "pivot_rows": [],
            "execution_time_ms": round((time.time() - start_time) * 1000, 2)
        }

    # Clean pivot matrix
    pivot_df = df.pivot(index=row_dim, columns=col_dim, values=msr).fillna(0.0).round(2)
    col_headers = list(pivot_df.columns)
    
    rows_output = []
    for row_name, row_series in pivot_df.iterrows():
        row_dict = {"_row_label": str(row_name)}
        vals = []
        for col_name in col_headers:
            val = float(row_series[col_name])
            row_dict[str(col_name)] = val
            if val > 0:
                vals.append(val)
        row_dict["_row_average"] = round(float(np.mean(vals)), 2) if vals else 0.0
        row_dict["_row_total"] = round(float(np.sum(vals)), 2) if vals else 0.0
        rows_output.append(row_dict)

    # Column averages
    col_summaries = {}
    for col_name in col_headers:
        c_str = str(col_name)
        c_vals = [float(r[c_str]) for r in rows_output if float(r.get(c_str, 0)) > 0]
        col_summaries[c_str] = round(float(np.mean(c_vals)), 2) if c_vals else 0.0

    exec_time_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "status": "success",
        "operation": f"Pivot Cross-Tab: {DIMENSION_MAP[row_dim]['label']} vs {DIMENSION_MAP[col_dim]['label']}",
        "row_dimension": row_dim,
        "row_label": DIMENSION_MAP[row_dim]["label"],
        "col_dimension": col_dim,
        "col_label": DIMENSION_MAP[col_dim]["label"],
        "measure": msr,
        "measure_label": MEASURE_MAP[msr]["label"],
        "columns": [str(c) for c in col_headers],
        "rows": rows_output,
        "column_summaries": col_summaries,
        "sql_query": res["sql_query"],
        "execution_time_ms": exec_time_ms
    }


def export_olap_data(
    dimensions: list = None,
    filters: dict = None,
    measures: list = None,
    format_type: str = "csv"
) -> str:
    """
    Exports OLAP aggregation results as CSV or JSON string.
    """
    res = execute_olap_query(
        dimensions=dimensions,
        filters=filters,
        measures=measures,
        limit=1000,
        operation="Export"
    )
    df = pd.DataFrame(res["data"])
    if df.empty:
        df = pd.DataFrame(columns=dimensions or ["market"])

    if format_type.lower() == "json":
        return df.to_json(orient="records", indent=2)
    return df.to_csv(index=False)
