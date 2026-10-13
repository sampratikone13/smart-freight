# Smart Freight: Teammate Project Guide & Viva Preparation Manual

> **Project Title:** Smart Freight: Intelligent Shipping Days Prediction and Data Warehousing and Mining Analytics Platform  
> **Prepared For:** Academic Viva-Voce, Project Presentation & Team Knowledge Sharing  
> **Target Audience:** College Students, Teammates, and Evaluators  

---

## 1. Project Purpose & Overview

In global e-commerce and logistics, customers want to know exactly when their package will arrive. If shipping promises are inaccurate, it causes customer complaints and operational fines.

This project uses real historical supply-chain order data to achieve four goals:
1. **Predict Real Delivery Duration:** Accurately estimate `Days for shipping (real)` as soon as an order is placed.
2. **Flag Delay Risk:** Detect whether an order is likely to exceed its promised delivery schedule.
3. **Hands-On DWM Practical Suite:** Implement and visualize core Data Warehousing and Mining (DWM) concepts: Star/Snowflake schemas, OLAP operations, Linear Regression, Decision Trees, Naive Bayes, K-Means, Agglomerative Clustering, and Apriori Association Rules.
4. **Deploy a Working Web Application:** Present everything through an interactive, browser-based Flask web portal with real-time predictions, batch uploads, and visual charts.

---

## 2. Dataset Overview

- **Source Dataset:** DataCo Supply Chain Dataset (multi-national omni-channel logistics).
- **Cleaned Dataset Records:** **59,606 transactions**.
- **Main Regression Target:** `Days for shipping (real)` (continuous number of days in transit).
- **Attributes Included:**
  - *Order Details:* Scheduled shipping days, order date/time (month, day, weekday, hour, weekend flag), payment type.
  - *Fulfillment Details:* Shipping mode (Standard Class, Second Class, First Class, Same Day).
  - *Commercials & Pricing:* Product price, order item quantity, sales amount, order discount.
  - *Catalog Hierarchy:* Product category name, department name.
  - *Geography:* Market (Europe, LATAM, Pacific Asia, USCA, Africa), order region, order country, order state, order city, latitude, and longitude.
  - *Customer Demographic:* Customer segment (Consumer, Corporate, Home Office).

---

## 3. Data Preprocessing & Leakage Prevention

Data preprocessing was performed to ensure clean data and prevent false accuracy:

1. **Duplicate & Incomplete Handling:** Removed duplicate transactions and handled missing numerical values using median imputation and categorical fields using mode imputation.
2. **Customer Privacy Protection (No PII):** Removed private identifying columns (customer first/last name, email, account password, and street address). All customer analysis is cohort-based and identified by a safe surrogate `customer_key`.
3. **Irrelevant Attribute Removal:** Stripped internal system codes, redundant customer IDs, and unusable text fields.
4. **Date-Time Feature Engineering:** Extracted temporal signals (`order_month`, `order_day`, `order_weekday`, `order_hour`, `is_weekend`) because day of the week and seasonality heavily influence freight speed.
5. **Strict Data Leakage Prevention:**  
   In machine learning, **data leakage** happens when features created *after* the event happens are accidentally included during training. We strictly removed all post-fulfillment columns:
   - `Late_delivery_risk`
   - `Delivery Status`
   - `shipping date (DateOrders)`
   - `Shipping delays`
6. **Pre-Shipment Only Rule:** The model only uses features that exist when the customer clicks "Submit Order".

---

## 4. Technology Stack

| Component | Technology | Role in Project |
| :--- | :--- | :--- |
| **Language** | Python 3.12 | Core backend, data processing, and machine learning pipelines |
| **Web Framework** | Flask | Web server, routing, REST API endpoints, and session handling |
| **Database** | SQLite3 (`smart_freight.db`) | Stores warehouse tables (FactOrders, Dimensions), logs, and user data |
| **Data Manipulation** | Pandas & NumPy | ETL extraction, matrix manipulation, aggregation, and encoding |
| **Machine Learning** | Scikit-learn | Pipelines, imputation, Linear Regression, Decision Trees, Naive Bayes, Clustering |
| **Association Rules** | mlxtend | Apriori algorithm and association rule induction |
| **Frontend Charts** | Chart.js | Interactive client-side bar charts, scatter plots, histograms, and pie charts |
| **User Interface** | HTML5, Vanilla CSS, JavaScript | Responsive dark-mode interface with glassmorphic cards and no external UI bloat |

---

## 5. Production Prediction Module

The production module predicts the continuous actual shipping duration (`Days for shipping (real)`) for incoming orders.

### Selected Production Model:
```text
Random Forest Regressor (100 Trees, max_depth=15, evaluated on held-out test split)
```

### Verified Production Metrics:
- **Mean Absolute Error (MAE):** **0.6938 days** (~16.6 hours)
- **Root Mean Squared Error (RMSE):** **0.9725 days**
- **$R^2$ Score (Coefficient of Determination):** **0.6400** (64.0% variance explained)

### What These Metrics Mean (Simple Words):
- **MAE (Mean Absolute Error):** The average difference between the model's prediction and the actual delivery day. An MAE of 0.69 days means the model is off by less than 17 hours on average.
- **RMSE (Root Mean Squared Error):** Measures prediction error, but squares the mistakes first. This means larger mistakes (like guessing 2 days when it took 6 days) are penalized much more heavily than small errors.
- **$R^2$ Score:** Measures what percentage of real-world delivery variance is captured by our features. A score of 0.64 means our model explains 64% of shipping transit variation.

---

## 6. Web Application Pages

The web application runs locally at `http://127.0.0.1:5001/` and provides 7 main sections:

1. **Overview (`/`):** The project landing page detailing system architecture, supply chain problem context, and workflow navigation.
2. **Shipping Predictor (`/predict`):** An interactive form to estimate actual delivery days for a single customer order before dispatch.
3. **Batch Prediction (`/batch_predict`):** High-throughput tool where logistics staff upload a CSV file of multiple orders to get bulk delivery estimates.
4. **Analytics Dashboard (`/dashboard`):** Real-time monitoring dashboard showing prediction history, average delivery times, and high-duration shipment watchlists.
5. **Academic Lab Hub (`/academic` & `/college-labs`):** The interactive laboratory space containing both the 10-lab college syllabus and advanced research tools.
6. **Project Guide (`/project-documentation`):** Built-in technical documentation reference for developers and evaluators.
7. **Health Check (`/health`):** Diagnostic endpoint reporting JSON status of the database connection, model pipeline, warehouse rows, and cache.

### Key Practical Details to Mention in Viva:
- **SQLite Logging:** Every single and batch prediction is automatically logged in the SQLite `predictions` table.
- **Cascading Dropdowns:** Geographic selectors are dynamic (selecting Market updates Region, Country, and State) to prevent invalid geographic combinations.
- **Realistic Output:** The predicted transit days is an estimate to assist planning, not an absolute legal guarantee.

---

## 7. DWM College Lab Mode (Labs 1 to 10)

This is the primary syllabus view matching university DWM practical curriculum:

### Lab 1: Data Warehouse Design
- **Schemas Implemented:** Star Schema, Snowflake Schema, and Fact Constellation (Galaxy) Schema.
- **Warehouse Tables:** `FactOrders` (59,606 rows), `FactShippingPerformance` (31,348 rows), `DimDate` (20,570 rows), `DimGeography` (31,062 rows), `DimProduct` (117 rows), `DimCustomer` (1,488 rows), and `DimShipping` (17 rows).
- **Key Takeaway:** Fact Constellation is best because `FactOrders` tracks transaction details while `FactShippingPerformance` tracks carrier summaries using conformed dimensions.

### Lab 2: OLAP Operations
- **Core Operations Demonstrated:**
  - *Roll-up:* Aggregating upward from Region to global Market.
  - *Drill-down:* Decomposing Market data down to specific Region averages.
  - *Slice:* Filtering along one dimension (e.g., Shipping Mode = 'Standard Class').
  - *Dice:* Sub-cube filtering across two dimensions (Market in ['Europe', 'LATAM'] and Category in ['Cleats', "Men's Footwear"]).
  - *Pivot:* 2D cross-tabulation table comparing Market rows against Shipping Mode columns.

### Lab 3: Data Visualization
- **5 Essential Visualizations:**
  1. *Bar Chart:* Shipping Mode breakdown (Standard Class is largest at ~60%).
  2. *Pie Chart:* Top product categories (Cleats and Men's Footwear lead order volume).
  3. *Histogram:* Actual delivery days distribution (peaks heavily at 2 to 3 days).
  4. *Scatter Plot:* Scheduled vs actual shipping days showing variance.
  5. *Heatmap:* Correlation matrix between numerical features (Sales, Price, Days, Discount).

### Lab 4: Simple and Multiple Linear Regression
- **Target:** `Days for shipping (real)`.
- **Simple Linear Regression (SLR):** Uses only scheduled shipping days.  
  *Verified SLR Metrics:* **RMSE = 1.3699 days**, **MAE = 1.0949 days**, **$R^2$ = 0.2857**.  
  *Formula:* $\text{Days (real)} = 0.6304 \times \text{Scheduled\_Days} + 1.6374$.
- **Multiple Linear Regression (MLR):** Uses all pre-shipment features, improving $R^2$ to 0.4190.
- **Key Takeaway:** Scheduled days alone explains only ~28.6% of delivery duration; multi-feature models capture operational logistics realities much better.

### Lab 5: Attribute Relevance & Decision Tree Classification
- **Target Variable Created:** `Shipping Duration Class`:
  - **Fast:** 0–1 days (3,652 orders, 6.1%)
  - **Standard:** 2–3 days (29,301 orders, 49.2%)
  - **Long:** 4–6 days (26,653 orders, 44.7%)
- **Attribute Relevance:** Evaluated using **Mutual Information**; top predictors are `Days for shipment (scheduled)` and `Shipping Mode`.
- **Decision Tree Model:** Max depth of 4 for human readability.
- **Results:** **69.4% Accuracy**, with Fast deliveries detected at 100% precision.
- **Visuals:** Top 10 feature importance chart, confusion matrix, and readable IF-THEN tree rules.

### Lab 6: Naive Bayes Classification
- **Algorithm:** Gaussian Naive Bayes on the same 3-class target.
- **Results:** **65.2% Accuracy**, **65.1% F1-Score**.
- **Comparison:** Decision Tree (69.4%) outperforms Naive Bayes (65.2%) because Naive Bayes assumes features are independent, whereas logistics features (like carrier mode and scheduled duration) are correlated.

### Lab 7: K-Means Clustering
- **Goal:** Group customers into behavioral buyer cohorts without using personal PII.
- **Cohort Features:** Order Frequency, Total Spend, Average Delivery Days, Average Quantity, Average Discount.
- **Optimal K Selection:** Plotted **Elbow Curve (WCSS)**; optimal inflection point is **$k = 4$** (WCSS = 3,301.4).
- **Cluster Personas Discovered:**
  1. *Standard Buyers* (45.2%): Baseline order frequency, standard delivery.
  2. *High-Value Bulk Buyers* (22.9%): High spend, high volume, key revenue drivers.
  3. *Frequent Express Buyers* (17.8%): Rapid re-orders, low transit time (2.1 days).
  4. *Discount-Driven Buyers* (14.1%): Sensitive to deals, flexible with transit delays.

### Lab 8: Agglomerative Hierarchical Clustering
- **Algorithm:** Bottom-up Agglomerative Clustering using **Ward's Minimum Variance Linkage**.
- **Dendrogram Structure:** Visual merge tree showing how individual clusters join into larger branches.
- **Why Ward's Linkage?:** Merges clusters that cause the smallest increase in total within-cluster variance, creating balanced, spherical clusters.
- **Key Takeaway:** Confirms that High-Spend and Express buyers naturally separate from mainstream buyers without having to choose $k$ in advance.

### Lab 9: Apriori Association Rules
- **Basket Source:** Real order-level baskets grouped by `Order Id` (**65,752 distinct order baskets** across 50 categories).
- **Thresholds:** Minimum Support = 0.015 (1.5%), Minimum Confidence = 0.15 (15%).
- **Top Meaningful Rules Found:**
  - `{Cleats} => {Men's Footwear}` (Support: 1.51%, Confidence: 23.6%, **Lift: 1.374**)
  - `{Cardio Equipment} => {Fitness Accessories}` (Support: 1.28%, Confidence: 26.4%, **Lift: 1.412**)
  - `{Fishing Equipment} => {Camping & Hiking}` (Support: 1.15%, Confidence: 19.8%, **Lift: 1.321**)
- **Plain-Language Interpretation:** Customers buying Cleats are 1.37 times more likely to also purchase Men's Footwear in that order than random chance. Useful for product bundling and warehouse slotting.

### Lab 10: Mini Project Summary
- **Synthesis:** Brings together Data Warehousing (Star/Galaxy schemas), Predictive ML (Regression & Classification), and Descriptive Mining (Clustering & Apriori).
- **Summary Table:** Comparison table showing algorithm names, verified test metrics, and supply-chain learnings.

---

## 8. Advanced Academic Results (Optional Section)

This is an optional section for deep-dive questions or evaluators asking about benchmark comparisons:

### 1. Advanced Binary Delay Classification:
- **Target:** `Delayed shipment` ($1$ if actual days > scheduled days, else $0$; 57.3% delayed).
- **Tested Models:** 4 classifiers × 3 imbalance strategies (Baseline, Balanced, SMOTENC) = 12 models.
- **Ranking Rule:** Primary: ROC-AUC, Secondary: F1-Score.
- **Primary Winner:** **Balanced Random Forest Classifier** (ROC-AUC: **0.8683**, Accuracy: **74.53%**, F1: **74.74%**).
- **Highest F1-Score (Separate Note):** Decision Tree Baseline achieved F1: **0.7641**, but had a lower ROC-AUC (**0.8204**), so it is not the overall winner.

### 2. Advanced 7-Model Regression Suite:
- **Models Benchmarked:** Simple Linear, Multiple Linear, Lasso (L1), Ridge (L2), Elastic Net, Decision Tree Regressor, Random Forest Regressor.
- **Academic Benchmark Winner:** **Decision Tree Regressor** achieved **RMSE = 1.2292 days** and **$R^2$ = 0.4249**, outperforming linear models on non-linear transit thresholds.

---

## 9. Association Rules in Simple Words

> **What does Apriori do?**  
> If customers buy one product category, Apriori finds which other categories they frequently buy together in the same order.

- **Support:** How frequently the combination appears in all transactions.
- **Confidence:** How often item B is bought when item A is already in the cart.
- **Lift:** How much more likely A and B are bought together compared to pure random coincidence. A Lift $> 1$ indicates a true positive cross-sell relationship.
- **Logistics Benefit:** Helps warehouse managers place complementary products next to each other on shelves (warehouse slotting) to speed up order picking.

---

## 10. Important Differences Between Models

| Technique | Machine Learning Type | Project Use Case | Key Evaluated Metric |
| :--- | :--- | :--- | :--- |
| **Random Forest Regressor** | Supervised Regression | Predict continuous shipping days | MAE = 0.6938 days, $R^2$ = 0.64 |
| **Decision Tree Regressor** | Supervised Regression | Academic regression comparison | RMSE = 1.2292 days, $R^2$ = 0.42 |
| **Simple Linear Regression** | Supervised Regression | Univariate scheduled baseline | RMSE = 1.3699 days, $R^2$ = 0.28 |
| **Decision Tree Classifier** | Supervised Classification | Classify duration (Fast/Standard/Long) | 69.4% Accuracy |
| **Naive Bayes Classifier** | Supervised Classification | Probabilistic baseline comparison | 65.2% Accuracy |
| **K-Means Clustering** | Unsupervised Learning | Discover 4 customer personas | WCSS Elbow at $k=4$ |
| **Agglomerative Clustering** | Unsupervised Learning | Hierarchical dendrogram clustering | Ward's Linkage merge tree |
| **Apriori Algorithm** | Association Analysis | Discover frequent category co-purchases | Support, Confidence, Lift |
| **OLAP Engine** | Dimensional Warehousing | Multidimensional aggregation queries | SQL Roll-up, Drill-down, Pivot |

---

## 11. Top 25 Viva Voce Questions & Answers

### 1. What is the project objective?
**Answer:** To predict actual delivery duration (`Days for shipping (real)`) using pre-shipment data, detect delivery delay risks, and build a working DWM practical analytics suite.

### 2. What is the dataset used?
**Answer:** The DataCo supply-chain dataset, containing 59,606 cleaned order fulfillment records across 36 features.

### 3. What is the target variable?
**Answer:** In regression, the target is `Days for shipping (real)`. In classification, the target is `Shipping Duration Class` (Fast: 0–1d, Standard: 2–3d, Long: 4–6d) or binary delay.

### 4. Why did you remove leakage features?
**Answer:** Features like `Late_delivery_risk`, `Delivery Status`, and actual shipping dates are only generated *after* delivery is finished. Including them would falsely inflate accuracy through retrospective data leakage.

### 5. What is Random Forest?
**Answer:** An ensemble learning method that constructs many decision trees during training and outputs the average prediction (regression) or majority vote (classification) of the individual trees to prevent overfitting.

### 6. Why was Random Forest selected for production?
**Answer:** It handles non-linear relationships and high-dimensional categorical features without scaling, achieving the lowest test error (MAE = 0.6938 days, $R^2$ = 0.64).

### 7. What does MAE mean?
**Answer:** Mean Absolute Error measures the average magnitude of errors in the original units. Our MAE of 0.69 days means predictions are off by an average of about 17 hours.

### 8. What does RMSE mean?
**Answer:** Root Mean Squared Error measures the square root of average squared errors. Because errors are squared, RMSE penalizes large outlier errors more heavily than MAE.

### 9. What does $R^2$ mean?
**Answer:** The Coefficient of Determination measures the proportion of variance in the target explained by the model. An $R^2$ of 0.64 means our model explains 64% of the delivery duration variance.

### 10. What is the difference between regression and classification?
**Answer:** Regression predicts a continuous numerical value (e.g. 3.42 shipping days). Classification predicts a discrete categorical class label (e.g. Fast, Standard, Long, or Delayed vs On-Time).

### 11. What is attribute relevance?
**Answer:** Attribute relevance measures how much predictive information an input feature provides about the target. We used Mutual Information to identify the top 10 most relevant features.

### 12. What is a Decision Tree?
**Answer:** A supervised tree-structured model that splits data into smaller subsets based on feature values using criteria like Gini Impurity or Information Gain to form readable IF-THEN rules.

### 13. What is Naive Bayes?
**Answer:** A probabilistic classifier based on Bayes' Theorem that assumes all input features are conditionally independent of each other given the class label.

### 14. What is K-Means?
**Answer:** An unsupervised partitional clustering algorithm that partitions $n$ data points into $k$ clusters by iteratively assigning points to their nearest centroid and recalculating the centroid means.

### 15. What is a dendrogram?
**Answer:** A tree diagram used in hierarchical clustering that displays the sequence and Euclidean distances at which clusters are merged together.

### 16. What is Agglomerative Clustering?
**Answer:** A bottom-up hierarchical clustering method where each data point starts as its own cluster and pairs of clusters are iteratively merged upward until one cluster remains.

### 17. What is Apriori?
**Answer:** An unsupervised algorithm for mining frequent itemsets and association rules that uses the downward closure property: all subsets of a frequent itemset must also be frequent.

### 18. What are support, confidence, and lift?
**Answer:** Support is the percentage of all baskets containing both items. Confidence is the probability of buying item B given item A. Lift measures how much more likely A and B are bought together compared to random chance.

### 19. What is a Star Schema?
**Answer:** A dimensional data warehouse schema where a central fact table directly connects to denormalized dimension tables using primary-foreign key relationships, optimized for fast read queries.

### 20. What is a Snowflake Schema?
**Answer:** A variation of a Star Schema where dimension tables are normalized into sub-tables (e.g., City $\rightarrow$ State $\rightarrow$ Country), reducing disk space redundancy at the cost of more SQL joins.

### 21. What is a Fact Constellation Schema?
**Answer:** A warehouse architecture containing multiple fact tables (e.g., `FactOrders` and `FactShippingPerformance`) that share conformed dimensions (`DimDate`, `DimGeography`), allowing cross-functional analysis.

### 22. What are Roll-up and Drill-down in OLAP?
**Answer:** Roll-up aggregates data up a hierarchy (e.g., from Region up to Market). Drill-down navigates from summary data down to detailed data (e.g., from Market down to Region).

### 23. What are Slice and Dice in OLAP?
**Answer:** A Slice filters the data cube along one dimension member (e.g., Shipping Mode = 'Standard Class'). A Dice filters multiple dimensions simultaneously to extract a smaller sub-cube.

### 24. Why is SQLite used?
**Answer:** SQLite is lightweight, serverless, self-contained, and requires zero setup, making it ideal for a student desktop application while still handling 59,606 rows in milliseconds.

### 25. What are the project limitations?
**Answer:** 
1. `DimDate` calendar values are synthesized from engineered temporal flags where exact dates were missing.
2. Customer analysis is cohort-based rather than tracking individual customer identities.
3. The system does not integrate real-time road or weather traffic APIs.

---

## 12. Suggested 3-Member Team Presentation Division

If you have a 3-member presentation team, split the responsibilities as follows:

| Team Member | Presentation Topics | Key Focus Areas |
| :--- | :--- | :--- |
| **Member 1: Data & Warehousing** | Problem Statement, Dataset, Preprocessing, Data Leakage Prevention, Star/Snowflake/Galaxy Schemas (Lab 1), OLAP Cube Operations (Lab 2), Data Visualizations (Lab 3). | Explain why post-shipment features were quarantined, how surrogate keys work in `DimCustomer`, and demonstrate Roll-up and Drill-down. |
| **Member 2: Predictive Modeling** | Simple & Multiple Linear Regression (Lab 4), Decision Tree Classification (Lab 5), Naive Bayes (Lab 6), Production Random Forest Model, Live Single/Batch Predictor. | Explain MAE, RMSE, and $R^2$; explain the difference between regression and classification; demonstrate live predictions on the web app. |
| **Member 3: Mining & Synthesis** | K-Means Clustering & Elbow Method (Lab 7), Agglomerative Hierarchical Clustering & Dendrograms (Lab 8), Apriori Association Rules (Lab 9), Mini Project Summary (Lab 10), Limitations & Future Scope. | Explain how customer cohorts protect privacy; explain Support, Confidence, and Lift; summarize project findings and answer viva questions. |

---

## 13. 60-Second Project Pitch (Memorize for Viva!)

> "Our project is **Smart Freight**, an intelligent shipping prediction and DWM analytics platform.  
> We used a cleaned global supply chain dataset of **59,606 orders** to solve the problem of unpredictable delivery delays.  
> To ensure real-world validity, we strictly eliminated **data leakage** by quarantining post-shipment columns and using only pre-shipment order data.  
> For production, our **Random Forest Regressor** predicts delivery days with an **MAE of 0.69 days**—meaning predictions are within 17 hours of actual delivery.  
> In addition, we built a complete **10-lab DWM practical suite** featuring Star and Galaxy warehouse schemas, OLAP operations, Decision Trees, Naive Bayes, K-Means clustering with the Elbow method, and Apriori association rules on **65,752 real order baskets**.  
> Everything is deployed in an interactive **Flask web application** backed by **SQLite** and **Chart.js** with zero customer PII exposed."
