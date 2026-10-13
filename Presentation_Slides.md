# Smart Freight: Intelligent Shipping Days Prediction & DWM Analytics Platform
## Final Academic Presentation Content (10 Slides)

---

### Slide 1: Title Slide

- **Slide Title:** Smart Freight — Intelligent Shipping Days Prediction & DWM Analytics Platform
- **Bullet Points:**
  - An end-to-end machine learning and data warehousing platform for global supply chain logistics.
  - Predicts real shipment duration using pre-fulfillment order data.
  - Covers practical DWM modules: warehousing schemas, OLAP cubes, classification, regression, clustering, and association rules.
  - Built with Python, Flask, Scikit-learn, and SQLite.
- **Suggested Visual / Screenshot:** Smart Freight landing page (`/`) showing the hero banner, navigation bar, and key metrics overview.
- **Speaker Notes:**  
  "Good morning, everyone. Today we present Smart Freight, a logistics intelligence platform that combines predictive machine learning with a full Data Warehousing and Mining laboratory suite to solve shipment delay estimation."

---

### Slide 2: Problem Statement & Objective

- **Slide Title:** Problem Statement & Project Objectives
- **Bullet Points:**
  - Inaccurate shipping estimates cause supply chain bottlenecks and customer dissatisfaction.
  - Naive models suffer from data leakage by accidentally training on post-shipment status fields.
  - **Objective 1:** Build a leakage-safe regression model to predict `Days for shipping (real)`.
  - **Objective 2:** Build an academic DWM suite (Labs 0–10) covering schemas, OLAP, and mining algorithms.
  - **Objective 3:** Deploy an interactive web application for single/batch predictions and real-time analytics.
- **Suggested Visual / Screenshot:** Leakage Boundary Card from the Unified Dashboard (`/academic`) highlighting quarantined post-fulfillment columns.
- **Speaker Notes:**  
  "Logistics teams need to know true delivery turnaround when an order is placed. Our objective was to predict actual shipping duration using only pre-shipment data, while building a complete academic warehouse and data mining environment."

---

### Slide 3: Dataset & Preprocessing

- **Slide Title:** Supply Chain Dataset & Data Preprocessing
- **Bullet Points:**
  - **Dataset Size:** 59,606 cleaned logistics records across 36 attributes.
  - **Leakage Prevention:** Quarantined post-delivery columns (`Late_delivery_risk`, `Delivery Status`, `shipping date`).
  - **Handling Missing Values:** Median imputation for continuous metrics; mode imputation for categorical attributes.
  - **Categorical Encoding:** One-Hot Encoding with frequency pruning (`min_frequency=20`) to prevent high dimensionality.
  - **Data Profiling (Lab 0):** Automated audit caching missingness, skewness, moments, and cardinalities in `profile_cache.json`.
- **Suggested Visual / Screenshot:** Data Quality & Ingestion Audit table from Lab 0 (`/academic/lab-0`).
- **Speaker Notes:**  
  "We used a cleaned supply-chain dataset of 59,606 transactions. Before modeling, we cleaned missing values, one-hot encoded categories, and strictly quarantined all post-fulfillment columns to prevent data leakage."

---

### Slide 4: System Architecture & Technology Stack

- **Slide Title:** System Architecture & Technology Stack
- **Bullet Points:**
  - **Backend & Web Server:** Python 3.12 and lightweight Flask REST API framework.
  - **Data Processing & ML:** Pandas, NumPy, Scikit-learn, Imbalanced-learn, and MLxtend.
  - **Data Warehouse & Storage:** Embedded SQLite database (`smart_freight.db`) storing facts, dimensions, and experiment runs.
  - **Frontend UI & Visualization:** Vanilla HTML/CSS with Chart.js for interactive client-side plots.
  - **Model Persistence:** Serialized Scikit-learn pipelines saved via `joblib` alongside `model_metadata.json`.
- **Suggested Visual / Screenshot:** System architecture diagram or the live Health Check endpoint (`/health`) displaying component status.
- **Speaker Notes:**  
  "Our architecture is built on Python and Flask, backed by SQLite for both relational operations and dimensional warehousing. Frontend charts run on Chart.js, and models are bundled into reusable Scikit-learn pipelines."

---

### Slide 5: Data Warehouse Design: Star, Snowflake, Galaxy

- **Slide Title:** Dimensional Modeling: Star, Snowflake & Galaxy Schemas
- **Bullet Points:**
  - **Fact Constellation (Galaxy Schema):** Two fact tables — `FactOrders` (59,606 rows) and `FactShippingPerformance` (31,348 rows).
  - **Shared Conformed Dimensions:** `DimDate` (20,570 rows), `DimGeography` (31,062 rows), and `DimShipping` (17 rows).
  - **Product & Customer Dimensions:** `DimProduct` (117 rows) and `DimCustomer` (1,488 rows).
  - **Star vs. Snowflake:** Compares denormalized star schemas for fast analytical queries against normalized hierarchies for storage efficiency.
  - **Privacy Enforcement:** `DimCustomer` stores only non-PII localized geographic cohorts using warehouse surrogate `customer_key`.
- **Suggested Visual / Screenshot:** Schema Explorer diagram and SQL query comparator from Labs 1–3 (`/academic/labs/schema-explorer`).
- **Speaker Notes:**  
  "In Labs 1 to 3, we designed a Fact Constellation schema in SQLite. `FactOrders` tracks line-item transactions, while `FactShippingPerformance` pre-aggregates carrier performance, sharing common conformed dimensions without exposing any customer PII."

---

### Slide 6: Shipping-Days Regression Modeling & Results

- **Slide Title:** Shipping Days Prediction & Model Benchmarks
- **Bullet Points:**
  - **Regression Target:** `Days for shipping (real)` (continuous delivery days).
  - **Production Model:** Random Forest Regressor (100 estimators, max depth 15).
  - **Production Test Performance:** MAE = 0.6938 days (~16.6 hours), RMSE = 0.9725 days, $R^2$ = 0.6400.
  - **Academic 7-Model Suite (Lab 6):** Evaluated Simple Linear, Multiple Linear, Lasso, Ridge, ElasticNet, Decision Tree, and Random Forest.
  - **Academic Benchmark Winner:** Decision Tree Regressor achieved RMSE = 1.2292 days and $R^2$ = 0.4249 on pre-shipment features.
- **Suggested Visual / Screenshot:** Model comparison bar chart and Actual vs. Predicted scatter plot from Lab 6 (`/academic/labs/regression`).
- **Speaker Notes:**  
  "For continuous shipping duration, our production Random Forest model achieved an MAE of 0.69 days and an R-squared of 0.64. In our academic comparison suite, tree-based models consistently outperformed linear models by capturing nonlinear transit patterns."

---

### Slide 7: Delay-Risk Classification Results

- **Slide Title:** Supervised Delay Classification & Imbalance Handling
- **Bullet Points:**
  - **Classification Target:** `delivery_delay_class` (1 if actual shipping days > scheduled days, else 0; 57.3% delayed).
  - **Evaluated Algorithms (Exactly 4):** Random Forest, Decision Tree, Gaussian Naive Bayes, and Logistic Regression.
  - **Imbalance Strategies:** Evaluated Baseline (unweighted), Balanced class weights, and SMOTENC (training-fold only).
  - **Ranking Rule:** Primary ranking by ROC-AUC, secondary ranking by F1-Score.
  - **Primary Classification Winner:** Balanced Random Forest achieved **ROC-AUC = 0.8683**, Accuracy = 74.53%, and F1 = 74.74% (Decision Tree baseline had highest F1 of 0.7641, but lower ROC-AUC of 0.8204).
- **Suggested Visual / Screenshot:** ROC-AUC and Precision-Recall curve charts from Labs 4–5 (`/academic/labs/classification`).
- **Speaker Notes:**  
  "In Labs 4 and 5, we framed shipping delay as a binary classification problem. Ranked primarily by ROC-AUC, Balanced Random Forest won with an AUC of 0.8683, proving strong discrimination between delayed and on-time shipments across thresholds."

---

### Slide 8: Clustering & Association-Rule Mining

- **Slide Title:** Unsupervised Learning: Customer Cohorts & Basket Mining
- **Bullet Points:**
  - **Customer Cohort Segmentation (Lab 7):** Formed 1,487 localized geographic cohorts using RFM-style metrics (Frequency, Spend, Lead Time, Discount).
  - **Clustering Algorithms:** K-Means ($k=2..8$, optimal $k=4$, Silhouette = 0.2867, WCSS elbow = 3,301.37) and Agglomerative Linkage ($k=3$, Silhouette = 0.3679).
  - **Generated Personas:** High-Value Bulk Buyers, Frequent Express Buyers, and Discount-Driven Shoppers.
  - **Market Basket Mining (Lab 8):** Grouped real transactions by `Order Id` across 180,519 raw rows to create **65,752 order baskets** (44,563 multi-category, avg size 2.75).
  - **Apriori Results:** Extracted frequent itemsets and association rules (e.g., Cleats $\Rightarrow$ Men's Footwear, Support = 1.5%, Confidence = 23.6%, Lift = 1.374).
- **Suggested Visual / Screenshot:** 2D PCA cluster scatter plot from Lab 7 (`/academic/labs/clustering`) or the Apriori rule table from Lab 8 (`/academic/labs/association-rules`).
- **Speaker Notes:**  
  "For unsupervised learning, Lab 7 used K-Means and Agglomerative clustering on 1,487 privacy-safe customer cohorts to identify buyer personas. Lab 8 ran Apriori on 65,752 real order baskets, finding meaningful co-purchase rules like athletic apparel bundles."

---

### Slide 9: OLAP Analytics & Web Application Features

- **Slide Title:** Multidimensional OLAP Engine & Interactive Application
- **Bullet Points:**
  - **OLAP Engine (Lab 9):** Dynamic SQL queries over 59,606 `FactOrders` records executing in 15–85 ms.
  - **Dimensions & Measures:** Analyzes Time, Geography, Product, Shipping Mode, and Customer Segments across 7 aggregated measures.
  - **Interactive Operations:** Supports dynamic Roll-up, Drill-down, Slicing, Dicing, and 2D Pivot cross-tabulations.
  - **Production Web Features:** Single order delay predictor form (`/predict`), CSV batch prediction (`/batch_predict`), and history logging.
  - **Master Dashboard (Lab 10):** Unified portal (`/academic`) uniting Labs 0–10, Viva prep Q&A, and technical specifications.
- **Suggested Visual / Screenshot:** Interactive OLAP Cube console and Pivot cross-tab matrix from Lab 9 (`/academic/labs/olap`).
- **Speaker Notes:**  
  "Lab 9 provides a live OLAP analytics engine where users can slice, dice, drill down, and pivot warehouse facts directly in the browser. In addition, the platform includes a production single-order predictor and batch CSV inference interface."

---

### Slide 10: Conclusion, Limitations & Future Scope

- **Slide Title:** Project Summary, Limitations & Future Scope
- **Bullet Points:**
  - **Project Summary:** Successfully unified predictive supply chain ML with a complete 10-lab DWM practical system.
  - **Data Limitations:**
    - `DimDate` calendar values are synthesized from engineered temporal flags where exact dates were missing.
    - Customer analysis is strictly cohort-based to safeguard customer privacy.
    - Academic comparison suite and production model use separate, documented pipelines.
  - **Future Scope:**
    - Incorporate live weather and port congestion APIs to handle real-time transit shocks.
    - Migrate the analytical warehouse from SQLite to DuckDB or PostgreSQL for high-concurrency writes.
    - Implement automated alternative carrier recommendations when delay risk is detected.
- **Suggested Visual / Screenshot:** Unified Academic Dashboard header and audit status card from Lab 10 (`/academic`).
- **Speaker Notes:**  
  "To conclude, Smart Freight demonstrates how machine learning and data warehousing work together in real-world supply chains. For future work, we plan to incorporate real-time weather feeds and expand to high-concurrency database backends. Thank you!"
