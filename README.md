<h1 align="center">🚚 Smart Freight</h1>
<h3 align="center">Intelligent Shipping Days Prediction & Data Warehousing and Mining Analytics Platform</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Flask-3.x-black?style=for-the-badge&logo=flask&logoColor=white"/>
  <img src="https://img.shields.io/badge/Scikit--Learn-ML-orange?style=for-the-badge&logo=scikit-learn&logoColor=white"/>
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
  <img src="https://img.shields.io/badge/Chart.js-Visualization-FF6384?style=for-the-badge&logo=chart.js&logoColor=white"/>
</p>

<p align="center">
  A full-stack machine learning web application that predicts real shipping durations using pre-shipment order data, built on a 59,606-record global supply chain dataset — with a complete 10-lab DWM practical suite.
</p>

---

## 📌 Table of Contents

- [Project Overview](#-project-overview)
- [Live Features](#-live-features)
- [Tech Stack](#-tech-stack)
- [Machine Learning Models](#-machine-learning-models)
- [DWM Lab Suite](#-dwm-lab-suite-10-labs)
- [Project Structure](#-project-structure)
- [Setup & Installation](#-setup--installation)
- [Dataset](#-dataset)
- [Key Results](#-key-results)
- [Academic Context](#-academic-context)

---

## 🎯 Project Overview

In global e-commerce and logistics, inaccurate delivery promises cause customer complaints and operational fines. **Smart Freight** solves this by:

1. **Predicting Real Delivery Duration** — Estimating `Days for shipping (real)` the moment an order is placed using only pre-shipment data.
2. **Flagging Delay Risk** — Classifying whether a shipment will exceed its promised schedule.
3. **DWM Practical Suite** — Implementing Star/Snowflake/Galaxy schemas, OLAP operations, regression, classification, clustering, and association rules.
4. **Interactive Web App** — Delivering everything through a dark-mode Flask portal with real-time predictions, batch uploads, and Chart.js visualizations.

---

## ✨ Live Features

| Page | Route | Description |
|:---|:---|:---|
| 🏠 Overview | `/` | Project landing page with architecture & workflow |
| 🔮 Predictor | `/predict` | Single-order shipping duration estimator |
| 📦 Batch Upload | `/batch_predict` | CSV upload for bulk order predictions |
| 📊 Dashboard | `/dashboard` | Real-time analytics, averages, and watchlists |
| 🎓 Lab Hub | `/college-labs` | Complete 10-lab DWM academic suite |
| 📖 Docs | `/project-documentation` | Built-in technical reference |
| ❤️ Health | `/health` | JSON diagnostic endpoint |

---

## 🛠 Tech Stack

| Layer | Technology | Role |
|:---|:---|:---|
| **Language** | Python 3.12 | Backend, data processing, ML pipelines |
| **Web Framework** | Flask | REST API, routing, session handling |
| **Database** | SQLite3 | Warehouse tables, prediction logs |
| **Data** | Pandas & NumPy | ETL, matrix ops, aggregation, encoding |
| **ML** | Scikit-learn | All ML pipelines and model training |
| **Association Rules** | mlxtend | Apriori algorithm & rule induction |
| **Charts** | Chart.js | Bar, pie, scatter, histogram, heatmap |
| **UI** | HTML5 + Vanilla CSS + JS | Dark-mode glassmorphic interface |

---

## 🤖 Machine Learning Models

### Production Model
> **Random Forest Regressor** — 100 trees, `max_depth=15`

| Metric | Score |
|:---|:---|
| MAE | **0.6938 days** (~16.6 hours) |
| RMSE | **0.9725 days** |
| R² Score | **0.64** (64% variance explained) |

### Full Model Benchmark

| Type | Model | Key Metric |
|:---|:---|:---|
| Regression | Random Forest ⭐ | MAE = 0.69d, R² = 0.64 |
| Regression | Decision Tree | RMSE = 1.23d, R² = 0.42 |
| Regression | Multiple Linear | R² = 0.42 |
| Regression | Simple Linear | R² = 0.29 |
| Regression | Lasso / Ridge / Elastic Net | Regularized linear baselines |
| Classification | Decision Tree | 69.4% Accuracy |
| Classification | Naive Bayes | 65.2% Accuracy |
| Classification | Balanced Random Forest | ROC-AUC = 0.8683 |
| Clustering | K-Means (k=4) | WCSS Elbow = 3,301.4 |
| Clustering | Agglomerative (Ward's) | Hierarchical dendrogram |
| Association | Apriori | Lift > 1.3 rules on 65,752 baskets |

---

## 🎓 DWM Lab Suite (10 Labs)

| Lab | Topic | Key Implementation |
|:---|:---|:---|
| Lab 1 | Data Warehouse Design | Star, Snowflake & Galaxy (Fact Constellation) Schemas |
| Lab 2 | OLAP Operations | Roll-up, Drill-down, Slice, Dice, Pivot |
| Lab 3 | Data Visualization | Bar, Pie, Histogram, Scatter, Heatmap |
| Lab 4 | Linear Regression | SLR (R²=0.29) & MLR (R²=0.42) |
| Lab 5 | Decision Tree | 3-class duration classifier, 69.4% accuracy |
| Lab 6 | Naive Bayes | Gaussian NB, 65.2% accuracy |
| Lab 7 | K-Means Clustering | 4 customer personas via Elbow method |
| Lab 8 | Agglomerative Clustering | Ward's linkage dendrogram |
| Lab 9 | Apriori Association Rules | `{Cleats} => {Men's Footwear}` Lift=1.374 |
| Lab 10 | Mini Project Summary | End-to-end synthesis & comparison table |

### Warehouse Tables (SQLite)

| Table | Rows |
|:---|:---|
| `FactOrders` | 59,606 |
| `FactShippingPerformance` | 31,348 |
| `DimDate` | 20,570 |
| `DimGeography` | 31,062 |
| `DimProduct` | 117 |
| `DimCustomer` | 1,488 |
| `DimShipping` | 17 |

---

## 📁 Project Structure

```
smart-freight/
│
├── app.py                      # Flask application entry point
├── train_model.py              # Model training & serialization
├── requirements.txt            # Python dependencies
│
├── # Core Pipelines
├── data_pipeline.py            # ETL & feature engineering
├── regression_pipeline.py      # Regression model pipeline
├── classification_pipeline.py  # Classification model pipeline
├── clustering.py               # K-Means & Agglomerative
├── association_rules.py        # Apriori rule mining
├── olap_engine.py              # OLAP cube operations
├── warehouse_etl.py            # SQLite warehouse loader
├── db_manager.py               # Database connection manager
├── data_profiler.py            # Dataset profiling
│
├── # Runners
├── academic_runner.py          # Academic lab computation runner
├── regression_runner.py        # Regression experiment runner
├── classification_runner.py    # Classification experiment runner
├── college_labs.py             # 10-lab curriculum logic
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── predict.html
│   ├── batch_predict.html
│   ├── dashboard.html
│   ├── college_lab.html
│   └── ...
│
├── static/                     # CSS & JavaScript
│   ├── css/style.css
│   └── js/main.js
│
├── data/                       # JSON cache files
├── models/                     # Saved model metadata & benchmarks
├── backend/                    # App config & DB models
│
└── # Documentation
    ├── README.md
    ├── TEAMMATE_PROJECT_GUIDE.md
    ├── Project_Documentation.md
    └── Presentation_Slides.md
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.12+
- pip

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/smart-freight.git
cd smart-freight
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add the dataset

Download the **DataCo Supply Chain Dataset** and place it as:
```
DataCo_Cleaned-2.csv   (in the project root)
```

> 📎 The dataset is not included in this repo due to its size (~18 MB). Contact the team or download from [Kaggle - DataCo Smart Supply Chain](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis).

### 5. Train the model & initialize the warehouse

```bash
python train_model.py
python warehouse_etl.py
```

### 6. Run the application

```bash
python app.py
```

Open your browser at: **[http://127.0.0.1:5001](http://127.0.0.1:5001)**

---

## 📂 Dataset

| Property | Value |
|:---|:---|
| **Source** | DataCo Supply Chain Dataset |
| **Records** | 59,606 cleaned transactions |
| **Regression Target** | `Days for shipping (real)` |
| **Features Used** | 36 pre-shipment attributes |
| **Leakage Removed** | `Late_delivery_risk`, `Delivery Status`, `shipping date`, `Shipping delays` |
| **PII Removed** | Customer names, email, password, address |

---

## 📈 Key Results

```
Production Prediction (Random Forest):
  ✅ MAE  = 0.6938 days  (~16.6 hours average error)
  ✅ RMSE = 0.9725 days
  ✅ R²   = 0.64

Best Delay Classifier (Balanced Random Forest):
  ✅ ROC-AUC  = 0.8683
  ✅ Accuracy = 74.53%
  ✅ F1-Score = 74.74%

Top Association Rule:
  {Cleats} => {Men's Footwear}
  Support: 1.51% | Confidence: 23.6% | Lift: 1.374
```

---

## 🏫 Academic Context

This project was developed as part of the **Data Warehousing and Mining (DWM)** practical curriculum.

- **Dataset:** 59,606 global supply chain orders
- **Algorithms Covered:** Linear Regression, Decision Tree, Naive Bayes, K-Means, Agglomerative Clustering, Apriori
- **Warehouse Concepts:** Star Schema, Snowflake Schema, Fact Constellation, OLAP (Roll-up, Drill-down, Slice, Dice, Pivot)
- **Privacy:** All customer analysis is cohort-based — zero PII exposed

---

## 👥 Team

> Academic project submitted for DWM practical evaluation.

---

<p align="center">Made with ❤️ | Smart Freight © 2026</p>
