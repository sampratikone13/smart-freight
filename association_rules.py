"""
Smart Freight Association Rule Mining Engine (Lab 8)
Implements true order-level Transaction Basket Analysis:
- Groups transactions directly by real 'Order Id' from the raw source dataset:
    baskets = raw_df.groupby("Order Id")["Category Name"].apply(list)
- Strictly avoids grouping by geography, date, hour, or shipping mode.
- Does not expose customer PII anywhere in the pipeline or UI.
- Evaluates Support, Confidence, Lift, Conviction, and Leverage using mlxtend.
"""

import os
import json
import numpy as np
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CACHE_FILE = os.path.join(DATA_DIR, "association_rules_cache.json")

RAW_DATA_PATHS = [
    os.path.join(DATA_DIR, "order_baskets_raw.csv"),
    os.path.join(DATA_DIR, "order_baskets_raw.parquet"),
    os.path.join(DATA_DIR, "DataCoSupplyChainDataset.csv"),
    "/Users/samprati/Downloads/DataCoSupplyChainDataset.csv",
    "/Users/samprati/Downloads/archive/DataCoSupplyChainDataset.csv"
]

_cached_raw_df = None
_cached_encoded_matrices = {}
_cached_validation_metrics = {}


def load_raw_order_data() -> pd.DataFrame:
    """
    Loads order transaction items strictly using Order Id, Category Name, and Product Name.
    No customer PII (names, emails, addresses) is loaded or processed.
    """
    global _cached_raw_df
    if _cached_raw_df is not None:
        return _cached_raw_df

    for path in RAW_DATA_PATHS:
        if os.path.exists(path):
            if path.endswith(".csv"):
                try:
                    _cached_raw_df = pd.read_csv(
                        path,
                        usecols=["Order Id", "Category Name", "Product Name"],
                        encoding="latin1"
                    )
                except UnicodeDecodeError:
                    _cached_raw_df = pd.read_csv(
                        path,
                        usecols=["Order Id", "Category Name", "Product Name"],
                        encoding="utf-8"
                    )
                return _cached_raw_df
            elif path.endswith(".parquet"):
                try:
                    _cached_raw_df = pd.read_parquet(path)
                    return _cached_raw_df
                except Exception:
                    continue
                return _cached_raw_df

    raise FileNotFoundError(
        "Raw dataset with 'Order Id' not found in expected locations. "
        "Please provide DataCoSupplyChainDataset.csv or order_baskets_raw.parquet in data/."
    )


def get_order_baskets(item_level: str = "Category Name"):
    """
    Extracts real order-level transaction baskets using:
        baskets = raw_df.groupby("Order Id")[col_name].apply(list)
    """
    global _cached_encoded_matrices, _cached_validation_metrics
    col_name = "Product Name" if item_level == "Product Name" else "Category Name"

    if col_name in _cached_encoded_matrices:
        return (
            _cached_encoded_matrices[col_name]["baskets"],
            _cached_encoded_matrices[col_name]["df_trans"],
            _cached_validation_metrics[col_name]
        )

    raw_df = load_raw_order_data()

    # Required real order grouping
    baskets_series = raw_df.groupby("Order Id", observed=True)[col_name].apply(list)

    total_orders = int(len(baskets_series))
    avg_basket_size = round(float(baskets_series.apply(len).mean()), 2)
    unique_items = int(raw_df[col_name].nunique())

    # Build unique item lists per order for market basket representation
    baskets = [
        sorted(list(set(str(it).strip() for it in items if pd.notna(it) and str(it).strip() != "")))
        for items in baskets_series
    ]
    # Filter empty
    baskets = [b for b in baskets if len(b) > 0]

    multi_item_orders = sum(1 for b in baskets if len(b) >= 2)
    multi_item_pct = round((multi_item_orders / total_orders) * 100, 1) if total_orders > 0 else 0.0

    validation_card = {
        "total_orders": total_orders,
        "multi_distinct_orders": multi_item_orders,
        "multi_distinct_pct": multi_item_pct,
        "avg_basket_size": avg_basket_size,
        "unique_categories": unique_items,
        "item_level": col_name
    }

    # One-hot encode the category lists
    te = TransactionEncoder()
    te_ary = te.fit(baskets).transform(baskets)
    df_trans = pd.DataFrame(te_ary, columns=te.columns_)

    _cached_encoded_matrices[col_name] = {
        "baskets": baskets,
        "df_trans": df_trans
    }
    _cached_validation_metrics[col_name] = validation_card

    return baskets, df_trans, validation_card


def mine_association_rules(
    min_support: float = 0.01,
    min_confidence: float = 0.15,
    item_level: str = "Category Name",
    max_len: int = 4
) -> dict:
    """
    Runs Apriori on true order-level transactions and induces association rules.
    """
    min_support = max(0.001, min(0.5, float(min_support)))
    min_confidence = max(0.01, min(1.0, float(min_confidence)))
    col_name = "Product Name" if item_level == "Product Name" else "Category Name"

    baskets, df_trans, validation_card = get_order_baskets(item_level=col_name)
    total_orders = validation_card["total_orders"]

    # 1. Frequent Itemsets using Apriori
    try:
        frequent_itemsets = apriori(
            df_trans,
            min_support=min_support,
            use_colnames=True,
            max_len=max_len
        )
    except Exception as e:
        return {
            "status": "error",
            "message": f"Apriori execution failed: {str(e)}",
            "validation_card": validation_card,
            "frequent_itemsets": [],
            "rules": []
        }

    itemsets_list = []
    if not frequent_itemsets.empty:
        frequent_itemsets = frequent_itemsets.sort_values(by="support", ascending=False)
        for _, row in frequent_itemsets.iterrows():
            items = list(row["itemsets"])
            itemsets_list.append({
                "items": items,
                "itemset_str": ", ".join(items),
                "length": len(items),
                "support": round(float(row["support"]), 4),
                "support_percent": round(float(row["support"]) * 100, 2),
                "support_count": int(round(row["support"] * total_orders))
            })

    # 2. Association Rules Generation
    rules_list = []
    max_lift = 0.0
    avg_conf = 0.0

    if not frequent_itemsets.empty and len(frequent_itemsets) > 1:
        try:
            raw_rules = association_rules(
                frequent_itemsets,
                metric="confidence",
                min_threshold=min_confidence
            )

            if not raw_rules.empty:
                raw_rules = raw_rules.sort_values(by=["lift", "confidence"], ascending=[False, False])
                raw_rules["conviction"] = raw_rules["conviction"].replace([np.inf, -np.inf], 999.0).fillna(1.0)

                max_lift = round(float(raw_rules["lift"].max()), 4)
                avg_conf = round(float(raw_rules["confidence"].mean()), 4)

                for idx, r in raw_rules.iterrows():
                    ante = list(r["antecedents"])
                    cons = list(r["consequents"])
                    sup = round(float(r["support"]), 4)
                    conf = round(float(r["confidence"]), 4)
                    lift_val = round(float(r["lift"]), 4)
                    conv_val = round(float(r["conviction"]), 4)
                    lev_val = round(float(r["leverage"]), 4) if "leverage" in r else 0.0

                    ante_str = ", ".join(ante)
                    cons_str = ", ".join(cons)
                    rule_repr = f"{ante_str} ➔ {cons_str}"

                    if lift_val > 1.2:
                        narrative = f"Strong basket co-purchase: Orders containing [{ante_str}] are {lift_val:.2f}x more likely to also include [{cons_str}]."
                    elif lift_val > 1.0:
                        narrative = f"Positive affinity: Ordering [{ante_str}] moderately increases simultaneous purchase of [{cons_str}] (Lift = {lift_val:.2f})."
                    else:
                        narrative = f"Baseline / independent co-occurrence within order baskets (Lift = {lift_val:.2f})."

                    rules_list.append({
                        "id": int(idx) + 1,
                        "antecedents": ante,
                        "consequents": cons,
                        "antecedents_str": ante_str,
                        "consequents_str": cons_str,
                        "rule_repr": rule_repr,
                        "support": sup,
                        "support_percent": round(sup * 100, 2),
                        "confidence": conf,
                        "confidence_percent": round(conf * 100, 1),
                        "lift": lift_val,
                        "conviction": conv_val if conv_val < 900.0 else "Infinite",
                        "conviction_numeric": min(conv_val, 100.0),
                        "leverage": lev_val,
                        "interpretation": narrative
                    })
        except Exception:
            pass

    return {
        "status": "success",
        "parameters": {
            "min_support": min_support,
            "min_confidence": min_confidence,
            "item_level": col_name,
            "max_len": max_len
        },
        "validation_card": validation_card,
        "overview": {
            "total_orders": total_orders,
            "multi_distinct_orders": validation_card["multi_distinct_orders"],
            "multi_distinct_pct": validation_card["multi_distinct_pct"],
            "avg_basket_size": validation_card["avg_basket_size"],
            "unique_categories": validation_card["unique_categories"],
            "frequent_itemsets_count": len(itemsets_list),
            "rules_count": len(rules_list),
            "max_lift": max_lift,
            "avg_confidence": avg_conf
        },
        "frequent_itemsets": itemsets_list,
        "rules": rules_list
    }


def export_association_rules(
    min_support: float = 0.01,
    min_confidence: float = 0.15,
    item_level: str = "Category Name",
    format_type: str = "csv"
) -> str:
    """
    Exports generated order association rules as CSV or JSON.
    """
    res = mine_association_rules(min_support=min_support, min_confidence=min_confidence, item_level=item_level)
    rules_data = res.get("rules", [])

    if not rules_data:
        df_empty = pd.DataFrame(columns=[
            "Rule_ID", "Rule", "Antecedents", "Consequents",
            "Support", "Confidence", "Lift", "Conviction", "Leverage", "Interpretation"
        ])
        if format_type.lower() == "json":
            return df_empty.to_json(orient="records", indent=2)
        return df_empty.to_csv(index=False)

    df_export = pd.DataFrame([
        {
            "Rule_ID": r["id"],
            "Rule": r["rule_repr"],
            "Antecedents": r["antecedents_str"],
            "Consequents": r["consequents_str"],
            "Support": r["support"],
            "Confidence": r["confidence"],
            "Lift": r["lift"],
            "Conviction": r["conviction"],
            "Leverage": r["leverage"],
            "Interpretation": r["interpretation"]
        }
        for r in rules_data
    ])

    if format_type.lower() == "json":
        return df_export.to_json(orient="records", indent=2)
    return df_export.to_csv(index=False)
