"""
Smart Freight Customer Cohort Segmentation Module (Lab 7)
Cohorts are aggregated by non-PII geography and customer-segment attributes
because direct customer identifiers were removed for privacy.

Implements:
- Real RFM-style feature engineering from logistics data:
    1. Frequency: order count
    2. Monetary: total sales
    3. Average shipping days
    4. Average order quantity
    5. Average discount
- K-Means clustering for k = 2 to 8
- Elbow / WCSS calculation and Silhouette score analysis
- Automatic best-k selection
- Agglomerative Hierarchical Clustering
- 2D PCA dimensionality reduction for cluster scatter plots
- Dynamic cluster persona generation (High-Value Customers, Frequent Buyers,
  Discount-Driven Customers, Standard Customers) using real calculated values only.
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.decomposition import PCA
from data_pipeline import load_data

CACHE_DIR = os.path.join(os.path.dirname(__file__), "data")
CACHE_FILE = os.path.join(CACHE_DIR, "clustering_benchmark_cache.json")

_cached_rfm_df = None


def get_rfm_data() -> pd.DataFrame:
    """
    Extracts and aggregates real logistics data into customer-level RFM features.
    Grouping by Customer Segment and Geography creates 1,487 distinct customer entities,
    consistent with DimCustomer in the data warehouse.
    """
    global _cached_rfm_df
    if _cached_rfm_df is not None:
        return _cached_rfm_df.copy()

    df = load_data()
    cust_cols = ['Customer Segment', 'Customer Country', 'Customer State', 'Customer City']
    
    agg = df.groupby(cust_cols, observed=True).agg(
        order_count=('Sales', 'count'),
        total_sales=('Sales', 'sum'),
        avg_shipping_days=('Days for shipping (real)', 'mean'),
        avg_order_quantity=('Order Item Quantity', 'mean'),
        avg_discount=('Order Item Discount', 'mean')
    ).reset_index()

    # Assign warehouse surrogate customer_key (1-indexed)
    agg['customer_key'] = agg.index + 1

    # Round continuous metrics for clean display
    agg['total_sales'] = agg['total_sales'].round(2)
    agg['avg_shipping_days'] = agg['avg_shipping_days'].round(2)
    agg['avg_order_quantity'] = agg['avg_order_quantity'].round(2)
    agg['avg_discount'] = agg['avg_discount'].round(2)

    _cached_rfm_df = agg
    return _cached_rfm_df.copy()


def compute_elbow_and_silhouette(X_scaled: np.ndarray, k_min: int = 2, k_max: int = 8, random_state: int = 42):
    """
    Computes WCSS (Inertia) and Silhouette Scores across k = 2..8.
    """
    elbow_data = []
    best_k = 2
    max_silhouette = -1.0

    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = km.fit_predict(X_scaled)
        wcss = float(km.inertia_)
        sil = float(silhouette_score(X_scaled, labels))
        ch_score = float(calinski_harabasz_score(X_scaled, labels))
        db_score = float(davies_bouldin_score(X_scaled, labels))

        if sil > max_silhouette:
            max_silhouette = sil
            best_k = k

        elbow_data.append({
            "k": k,
            "wcss": round(wcss, 2),
            "silhouette": round(sil, 4),
            "calinski_harabasz": round(ch_score, 2),
            "davies_bouldin": round(db_score, 4)
        })

    return elbow_data, best_k


def assign_meaningful_personas(cluster_profiles: list) -> list:
    """
    Assigns intuitive, business-meaningful persona names based on real relative metrics:
    - High-Value Customers (highest total_sales / monetary)
    - Frequent Buyers (highest order_count / frequency)
    - Discount-Driven Customers (highest avg_discount)
    - Standard Customers (baseline or balanced)
    """
    if not cluster_profiles:
        return []

    n_clusters = len(cluster_profiles)
    
    # Identify indices of key extremes
    max_sales_idx = max(range(n_clusters), key=lambda i: cluster_profiles[i]['total_sales'])
    max_freq_idx = max(range(n_clusters), key=lambda i: cluster_profiles[i]['order_count'])
    max_disc_idx = max(range(n_clusters), key=lambda i: cluster_profiles[i]['avg_discount'])
    max_ship_idx = max(range(n_clusters), key=lambda i: cluster_profiles[i]['avg_shipping_days'])
    
    used_titles = set()
    for i, profile in enumerate(cluster_profiles):
        title = None
        badge_color = "#38bdf8"
        description = ""
        strategy = ""

        if i == max_sales_idx and "High-Value Customers" not in used_titles:
            title = "High-Value Customers"
            badge_color = "#10b981"  # Emerald
            description = "High cumulative monetary volume driving significant enterprise logistics revenue. Low price sensitivity with consistent scheduled shipment demands."
            strategy = "Prioritize priority air transit, assign dedicated account managers, and guarantee SLA turnaround."
        elif i == max_freq_idx and "Frequent Buyers" not in used_titles:
            title = "Frequent Buyers"
            badge_color = "#8b5cf6"  # Purple
            description = "High transaction cadence and repeat ordering patterns. Substantial lifetime customer value across recurring supply chains."
            strategy = "Offer automated replenishment programs, loyalty shipping credits, and batch consolidation."
        elif i == max_disc_idx and "Discount-Driven Customers" not in used_titles:
            title = "Discount-Driven Customers"
            badge_color = "#f59e0b"  # Amber
            description = "High responsiveness to price reductions and promotions. High average discount rates with moderate order values."
            strategy = "Deploy targeted promotional coupon thresholds with minimum order quantities to protect shipping margins."
        elif i == max_ship_idx and "Extended-Transit Cohort" not in used_titles and n_clusters > 4:
            title = "Extended-Transit Cohort"
            badge_color = "#ef4444"  # Rose
            description = "Customers experiencing longer-than-average delivery durations, potentially situated in peripheral shipping regions."
            strategy = "Optimize regional hub assignment and recommend premium shipping modes to prevent delayed fulfillment risk."
        else:
            # Standard or Segmented title
            idx_num = i + 1
            if "Standard Customers" not in used_titles:
                title = "Standard Customers"
                badge_color = "#06b6d4"  # Cyan
                description = "Steady, moderate order volumes with typical basket sizes and baseline discount consumption."
                strategy = "Maintain standard road and rail logistics routing with automated tracking updates."
            else:
                title = f"Segment {idx_num}: Mainstream Logistics Cohort"
                badge_color = "#64748b"  # Slate
                description = f"Cluster exhibiting balanced RFM behavior across regional distribution channels."
                strategy = "Provide regular promotional newsletters and reliable standard-class delivery."

        used_titles.add(title)
        profile['persona_title'] = title
        profile['badge_color'] = badge_color
        profile['description'] = description
        profile['strategy'] = strategy

    return cluster_profiles


def run_customer_clustering(k: int = 4, algorithm: str = 'kmeans', random_state: int = 42) -> dict:
    """
    Executes customer segmentation pipeline:
    1. Loads RFM metrics
    2. Scales features via StandardScaler
    3. Fits K-Means or Agglomerative Clustering
    4. Computes Silhouette, Calinski-Harabasz, and Davies-Bouldin scores
    5. Performs 2D PCA projection for cluster scatter visualization
    6. Formats cluster profiles and personas using real computed values.
    """
    k = max(2, min(8, int(k)))
    algorithm = 'agglomerative' if str(algorithm).lower() in ['agglomerative', 'hierarchical'] else 'kmeans'

    rfm_df = get_rfm_data()
    feature_cols = ['order_count', 'total_sales', 'avg_shipping_days', 'avg_order_quantity', 'avg_discount']
    X = rfm_df[feature_cols].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 1. Elbow curve across k=2..8
    elbow_data, best_k_silhouette = compute_elbow_and_silhouette(X_scaled, k_min=2, k_max=8, random_state=random_state)

    # 2. Fit chosen model
    if algorithm == 'agglomerative':
        model = AgglomerativeClustering(n_clusters=k, linkage='ward')
        labels = model.fit_predict(X_scaled)
        inertia_val = None
        centroids_pca = []
    else:
        model = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = model.fit_predict(X_scaled)
        inertia_val = round(float(model.inertia_), 2)

    rfm_df['cluster'] = labels

    # 3. Clustering Metrics
    sil_score = round(float(silhouette_score(X_scaled, labels)), 4)
    ch_score = round(float(calinski_harabasz_score(X_scaled, labels)), 2)
    db_score = round(float(davies_bouldin_score(X_scaled, labels)), 4)

    # 4. PCA 2D Projection
    pca = PCA(n_components=2, random_state=random_state)
    coords_pca = pca.fit_transform(X_scaled)
    var_ratio = [round(float(v) * 100, 2) for v in pca.explained_variance_ratio_]

    if algorithm == 'kmeans':
        centers_pca = pca.transform(model.cluster_centers_)
        centroids_pca = [
            {"cluster": i, "pc1": round(float(centers_pca[i, 0]), 3), "pc2": round(float(centers_pca[i, 1]), 3)}
            for i in range(k)
        ]

    # Build scatter points (sample or all 1,487 points for rich interactivity)
    scatter_points = []
    for idx, row in rfm_df.iterrows():
        scatter_points.append({
            "id": int(idx),
            "cluster": int(labels[idx]),
            "pc1": round(float(coords_pca[idx, 0]), 3),
            "pc2": round(float(coords_pca[idx, 1]), 3),
            "segment": str(row['Customer Segment']),
            "city": str(row['Customer City']),
            "state": str(row['Customer State']),
            "country": str(row['Customer Country']),
            "order_count": int(row['order_count']),
            "total_sales": float(row['total_sales']),
            "avg_shipping_days": float(row['avg_shipping_days']),
            "avg_order_quantity": float(row['avg_order_quantity']),
            "avg_discount": float(row['avg_discount'])
        })

    # 5. Cluster Profiles & Persona Generation
    total_customers = len(rfm_df)
    total_sales_all = float(rfm_df['total_sales'].sum())

    raw_profiles = []
    for c in range(k):
        c_df = rfm_df[rfm_df['cluster'] == c]
        c_count = len(c_df)
        c_sales = float(c_df['total_sales'].sum())
        
        raw_profiles.append({
            "cluster": c,
            "count": c_count,
            "pct_customers": round((c_count / total_customers) * 100, 1),
            "total_sales_sum": round(c_sales, 2),
            "pct_sales": round((c_sales / total_sales_all) * 100, 1) if total_sales_all > 0 else 0.0,
            "order_count": round(float(c_df['order_count'].mean()), 1),
            "total_sales": round(float(c_df['total_sales'].mean()), 2),
            "avg_shipping_days": round(float(c_df['avg_shipping_days'].mean()), 2),
            "avg_order_quantity": round(float(c_df['avg_order_quantity'].mean()), 2),
            "avg_discount": round(float(c_df['avg_discount'].mean()), 2),
            "top_segments": c_df['Customer Segment'].value_counts().head(2).to_dict()
        })

    personas = assign_meaningful_personas(raw_profiles)

    result = {
        "status": "success",
        "k": k,
        "best_k": best_k_silhouette,
        "algorithm": algorithm,
        "metrics": {
            "silhouette_score": sil_score,
            "calinski_harabasz": ch_score,
            "davies_bouldin": db_score,
            "wcss": inertia_val
        },
        "elbow_curve": elbow_data,
        "personas": personas,
        "centroids_pca": centroids_pca,
        "pca_scatter": scatter_points,
        "pca_variance": {
            "pc1": var_ratio[0],
            "pc2": var_ratio[1],
            "total_explained": round(var_ratio[0] + var_ratio[1], 2)
        },
        "overview": {
            "total_cohorts": total_customers,
            "total_sales": round(total_sales_all, 2),
            "total_orders": int(rfm_df['order_count'].sum()),
            "avg_shipping_days_overall": round(float(rfm_df['avg_shipping_days'].mean()), 2)
        }
    }

    return result


def export_clustering_data(k: int = 4, algorithm: str = 'kmeans', format_type: str = 'csv') -> str:
    """
    Exports customer clusters and calculated personas as CSV or JSON.
    """
    res = run_customer_clustering(k=k, algorithm=algorithm)
    rfm_df = get_rfm_data()
    
    # Map cluster to persona title
    cluster_to_persona = {p['cluster']: p['persona_title'] for p in res['personas']}
    
    # Rerun fit to assign cluster column
    feature_cols = ['order_count', 'total_sales', 'avg_shipping_days', 'avg_order_quantity', 'avg_discount']
    X = rfm_df[feature_cols].values
    X_scaled = StandardScaler().fit_transform(X)
    
    if algorithm == 'agglomerative':
        labels = AgglomerativeClustering(n_clusters=k).fit_predict(X_scaled)
    else:
        labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(X_scaled)
        
    rfm_df['cluster'] = labels
    rfm_df['persona'] = rfm_df['cluster'].map(cluster_to_persona)

    if format_type.lower() == 'json':
        return rfm_df.to_json(orient='records', indent=2)
    return rfm_df.to_csv(index=False)
