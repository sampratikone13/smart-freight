"""
Smart Freight Flask Application – Phase 1 Integrity-Audited Version
All metrics, model names, and row counts are read from model_metadata.json.
No hardcoded values in templates or route handlers.
"""

import io
import os
import pandas as pd
import json
import sqlite3

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, Response,
)
from werkzeug.security import generate_password_hash, check_password_hash

import data_pipeline
import train_model
import db_manager
import academic_runner
import data_profiler
import warehouse_etl
import classification_pipeline
import classification_runner
import regression_pipeline
import regression_runner
import clustering
import association_rules
import olap_engine
import college_labs

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "smart_freight_secret_2026_v2")

# Initialise SQLite on startup
db_manager.init_db()
classification_runner.init_classification_db()
regression_runner.init_regression_db()

# Temp store for last batch result
_last_batch_df: pd.DataFrame | None = None


# ── Health Check ──────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    checks = {}
    overall = "ok"

    # 1. Dataset loaded
    try:
        df = data_pipeline.load_data()
        checks["dataset_loaded"] = {
            "status": "ok",
            "rows": len(df),
            "columns": df.shape[1],
        }
    except Exception as e:
        checks["dataset_loaded"] = {"status": "error", "detail": str(e)}
        overall = "degraded"

    # 2. Model pipeline loaded
    try:
        _ = train_model.get_loaded_pipeline()
        checks["model_pipeline_loaded"] = {"status": "ok"}
    except Exception as e:
        checks["model_pipeline_loaded"] = {"status": "error", "detail": str(e)}
        overall = "degraded"

    # 3. SQLite connection
    try:
        conn = db_manager.get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        checks["sqlite_connection"] = {"status": "ok", "db": db_manager.DB_PATH}
    except Exception as e:
        checks["sqlite_connection"] = {"status": "error", "detail": str(e)}
        overall = "degraded"

    # 4. Model metadata
    try:
        meta = train_model.get_metadata()
        checks["model_metadata_loaded"] = {
            "status": "ok",
            "selected_model": meta.get("selected_final_model"),
            "rmse": meta.get("metrics", {}).get("rmse"),
            "mae": meta.get("metrics", {}).get("mae"),
            "r2": meta.get("metrics", {}).get("r2"),
        }
    except Exception as e:
        checks["model_metadata_loaded"] = {"status": "error", "detail": str(e)}
        overall = "degraded"

    # 5. Warehouse status
    try:
        wh_meta = warehouse_etl.get_warehouse_metadata()
        checks["warehouse_status"] = {
            "status": "ok",
            "fact_orders_rows": wh_meta.get("table_counts", {}).get("FactOrders"),
            "fact_matches_source": wh_meta.get("validation", {}).get("fact_matches_source"),
            "last_loaded": wh_meta.get("load_timestamp")
        }
    except Exception as e:
        checks["warehouse_status"] = {"status": "error", "detail": str(e)}
        overall = "degraded"

    # 6. Profile cache status
    try:
        prof_cache = data_profiler.get_profile_cache()
        checks["profile_cache_status"] = {
            "status": "ok",
            "cached_tables": len(prof_cache.get("tables", {})),
            "generated_at": prof_cache.get("generated_at")
        }
    except Exception as e:
        checks["profile_cache_status"] = {"status": "error", "detail": str(e)}
        overall = "degraded"

    # 7. Regression suite status (Lab 6)
    try:
        reg_suite = regression_runner.get_regression_benchmark_suite()
        checks["regression_status"] = {
            "status": "ok",
            "models_benchmarked": len(reg_suite.get("benchmark_table", [])),
            "best_model": reg_suite.get("best_model", {}).get("display_name"),
            "best_rmse": reg_suite.get("best_model", {}).get("rmse")
        }
    except Exception as e:
        checks["regression_status"] = {"status": "error", "detail": str(e)}
        overall = "degraded"

    return jsonify({"status": overall, "checks": checks}), (200 if overall == "ok" else 503)


# ── Cascading Dropdown API ────────────────────────────────────────────────────

@app.route("/api/hierarchy")
def api_hierarchy():
    """Returns the full cascading dropdown hierarchy as JSON."""
    return jsonify(data_pipeline.get_dropdown_hierarchy())


@app.route("/api/hierarchy/regions")
def api_regions_for_market():
    market = request.args.get("market", "")
    h = data_pipeline.get_dropdown_hierarchy()
    return jsonify(h.get("market_regions", {}).get(market, []))


@app.route("/api/hierarchy/countries")
def api_countries_for_region():
    region = request.args.get("region", "")
    h = data_pipeline.get_dropdown_hierarchy()
    return jsonify(h.get("region_countries", {}).get(region, []))


@app.route("/api/hierarchy/states")
def api_states_for_country():
    country = request.args.get("country", "")
    h = data_pipeline.get_dropdown_hierarchy()
    return jsonify(h.get("country_states", {}).get(country, []))


@app.route("/api/hierarchy/categories")
def api_categories_for_department():
    dept = request.args.get("department", "")
    h = data_pipeline.get_dropdown_hierarchy()
    return jsonify(h.get("dept_categories", {}).get(dept, []))


# ── Public Application Routes ─────────────────────────────────────────────────

@app.route("/")
def index():
    overview = data_pipeline.get_dataset_overview()
    metadata = train_model.get_metadata()
    return render_template("index.html", overview=overview, metadata=metadata)


@app.route("/predict", methods=["GET", "POST"])
@app.route("/predict_page", methods=["GET", "POST"])
def predict_page():
    h = data_pipeline.get_dropdown_hierarchy()
    prediction_result = None
    form_values = {}
    geo_error = None

    if request.method == "POST":
        form_values = request.form.to_dict()

        # Geography validation
        market = form_values.get("Market", "")
        region = form_values.get("Order Region", "")
        country = form_values.get("Order Country", "")
        state = form_values.get("Order State", "")

        is_valid, error_msg = data_pipeline.validate_geo_combination(
            market, region, country, state
        )

        if not is_valid:
            geo_error = error_msg
            flash(f"Invalid geography combination: {error_msg}", "danger")
        else:
            try:
                prediction_result = train_model.predict_single(form_values)
                user_id = session.get("user_id")
                db_manager.save_prediction(
                    form_values, prediction_result,
                    user_id=user_id, source="manual"
                )
                flash(
                    "Prediction generated and logged to database history.",
                    "success"
                )
            except Exception as e:
                flash(f"Prediction error: {str(e)}", "danger")

    return render_template(
        "predict.html",
        h=h,
        prediction=prediction_result,
        form_values=form_values,
        geo_error=geo_error,
    )


@app.route("/batch_predict", methods=["GET", "POST"])
def batch_predict():
    global _last_batch_df
    batch_results = None
    batch_total = 0

    if request.method == "POST":
        if "batch_file" not in request.files:
            flash("No file part in request.", "danger")
            return redirect(request.url)

        file = request.files["batch_file"]
        if not file.filename:
            flash("No file selected.", "danger")
            return redirect(request.url)

        try:
            df_upload = pd.read_csv(file)
            df_enriched = train_model.predict_batch(df_upload)
            _last_batch_df = df_enriched
            batch_total = len(df_enriched)
            batch_results = df_enriched.head(50).to_dict(orient="records")

            user_id = session.get("user_id")
            for _, row in df_enriched.head(10).iterrows():
                r_dict = row.to_dict()
                res = {
                    "predicted_shipping_days": r_dict.get("predicted_shipping_days", 3.0),
                    "speed_category": r_dict.get("shipping_speed_category", "Standard Duration"),
                    "is_delayed_risk": bool(
                        r_dict.get("predicted_shipping_days", 3.0)
                        > float(r_dict.get("Days for shipment (scheduled)", 4) or 4)
                    ),
                }
                db_manager.save_prediction(r_dict, res, user_id=user_id, source="batch")

            flash(
                f"Processed {batch_total:,} orders. Previewing top 50 below.",
                "success"
            )
        except Exception as e:
            flash(f"Batch processing error: {str(e)}", "danger")

    return render_template(
        "batch_predict.html",
        batch_results=batch_results,
        batch_total=batch_total,
    )


@app.route("/batch_predict/sample")
def download_sample_batch_csv():
    df = data_pipeline.load_data()
    sample = df[data_pipeline.FEATURE_COLUMNS].head(15).copy()
    buf = io.StringIO()
    sample.to_csv(buf, index=False)
    buf.seek(0)
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment;filename=smart_freight_sample_orders.csv"
        },
    )


@app.route("/batch_predict/download")
def download_enriched_batch_csv():
    global _last_batch_df
    if _last_batch_df is None or _last_batch_df.empty:
        flash("No batch predictions to download yet.", "danger")
        return redirect(url_for("batch_predict"))
    buf = io.StringIO()
    _last_batch_df.to_csv(buf, index=False)
    buf.seek(0)
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment;filename=enriched_shipping_predictions.csv"
        },
    )


@app.route("/dashboard")
def dashboard():
    kpis = db_manager.get_prediction_kpis()
    history = db_manager.get_recent_predictions(limit=50)
    metadata = train_model.get_metadata()
    return render_template(
        "dashboard.html", kpis=kpis, history=history, metadata=metadata
    )


@app.route("/dashboard/export_csv")
def export_history_csv():
    history = db_manager.get_recent_predictions(limit=500)
    if not history:
        flash("No prediction history recorded yet.", "info")
        return redirect(url_for("dashboard"))
    df_h = pd.DataFrame(history)
    buf = io.StringIO()
    df_h.to_csv(buf, index=False)
    buf.seek(0)
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment;filename=smart_freight_prediction_history.csv"
        },
    )


# ── College Lab Mode (Labs 1 to 10) ─────────────────────────────────────────

@app.route("/college-labs")
def college_labs_index():
    return redirect(url_for("college_lab_page", lab_id=1))


@app.route("/college-labs/<int:lab_id>")
def college_lab_page(lab_id):
    if lab_id < 1 or lab_id > 10:
        lab_id = 1
    lab = college_labs.get_college_lab(lab_id)
    catalog = college_labs.get_all_college_labs_catalog()
    return render_template(
        "college_lab.html",
        lab=lab,
        catalog=catalog
    )


@app.route("/api/college-labs/<int:lab_id>")
def api_college_lab(lab_id):
    if lab_id < 1 or lab_id > 10:
        return jsonify({"error": "Lab ID must be between 1 and 10"}), 400
    lab = college_labs.get_college_lab(lab_id)
    return jsonify(lab)


# ── Academic Laboratory (Phase 2: Lab 0 & Labs 1–3) ─────────────────────────

@app.route("/academic")
def academic_lab():
    lab_id = request.args.get("lab_id", default=10, type=int)
    catalog = academic_runner.get_lab_catalog()
    current_lab_info = next((l for l in catalog if l["id"] == lab_id), catalog[-1])

    lab_data = None
    if lab_id == 0:
        lab_data = academic_runner.run_lab_0()

    warehouse_health = db_manager.get_warehouse_health_summary()
    recent_history = db_manager.get_recent_experiment_history(limit=12)
    model_metadata = train_model.get_metadata()
    overview = data_pipeline.get_dataset_overview()
    viva_qa = academic_runner.get_viva_voce_guide()
    tech_details = academic_runner.get_academic_technical_details()

    return render_template(
        "academic.html",
        catalog=catalog,
        selected_lab=lab_id,
        current_lab_info=current_lab_info,
        lab_data=lab_data,
        warehouse_health=warehouse_health,
        recent_history=recent_history,
        model_metadata=model_metadata,
        overview=overview,
        viva_qa=viva_qa,
        tech_details=tech_details
    )


@app.route("/academic/lab-0")
def academic_lab_0():
    table_key = request.args.get("table", "source_dataset")
    cache = data_profiler.get_profile_cache()
    catalog = cache.get("table_catalog", [])
    profile = cache.get("tables", {}).get(table_key)
    if not profile:
        table_key = "source_dataset"
        profile = cache.get("tables", {}).get(table_key)
    academic = cache.get("academic_interpretation", {})
    return render_template(
        "lab_0.html",
        catalog=catalog,
        selected_table_key=table_key,
        profile=profile,
        academic=academic,
    )


@app.route("/academic/labs/schema-explorer")
@app.route("/academic/schema-explorer")
def schema_explorer():
    meta = warehouse_etl.get_warehouse_metadata()
    return render_template("schema_explorer.html", meta=meta)


# ── Profiling & Warehouse APIs ────────────────────────────────────────────────

@app.route("/api/academic/profile")
def api_academic_profile():
    table_key = request.args.get("table")
    cache = data_profiler.get_profile_cache()
    if not table_key:
        return jsonify({
            "catalog": cache.get("table_catalog"),
            "generated_at": cache.get("generated_at"),
            "table_keys": cache.get("table_keys")
        })
    profile = cache.get("tables", {}).get(table_key)
    if not profile:
        return jsonify({
            "error": f"Table '{table_key}' not found",
            "valid_tables": cache.get("table_keys")
        }), 404
    return jsonify(profile)


@app.route("/api/academic/profile/export")
def api_academic_profile_export():
    table_key = request.args.get("table", "source_dataset")
    fmt = request.args.get("format", "json").lower()
    cache = data_profiler.get_profile_cache()
    profile = cache.get("tables", {}).get(table_key)
    if not profile:
        return jsonify({"error": f"Table '{table_key}' not found"}), 404

    if fmt == "csv":
        rows = []
        for col in profile.get("column_profiles", []):
            num_s = col.get("numeric_stats") or {}
            cat_s = col.get("categorical_stats") or {}
            warns = "; ".join(w["label"] for w in col.get("warnings", [])) or "Clean"
            rows.append({
                "column_name": col["name"],
                "data_type": col["data_type"],
                "type_category": col["type_category"],
                "non_null_count": col["non_null_count"],
                "null_count": col["null_count"],
                "missing_percentage": col["missing_pct"],
                "unique_count": col["unique_count"],
                "mean": num_s.get("mean", ""),
                "median": num_s.get("median", ""),
                "std_dev": num_s.get("std", ""),
                "min": num_s.get("min", ""),
                "max": num_s.get("max", ""),
                "iqr": num_s.get("iqr", ""),
                "skewness": num_s.get("skewness", ""),
                "top_value": cat_s.get("top_value", ""),
                "top_count": cat_s.get("top_count", ""),
                "top_percentage": cat_s.get("top_percentage", ""),
                "warnings": warns
            })
        df_exp = pd.DataFrame(rows)
        buf = io.StringIO()
        df_exp.to_csv(buf, index=False)
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename={table_key}_profile_report.csv"}
        )
    else:
        return Response(
            json.dumps(profile, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment;filename={table_key}_profile.json"}
        )


@app.route("/api/profile_report")
def api_profile_report():
    report = academic_runner.run_lab_0()
    return jsonify(report)


@app.route("/api/warehouse/status")
def api_warehouse_status():
    meta = warehouse_etl.get_warehouse_metadata()
    return jsonify(meta)


@app.route("/api/academic/reproducibility")
def api_academic_reproducibility():
    path = os.path.join(os.path.dirname(__file__), "data", "reproducibility.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    return jsonify({"error": "reproducibility.json not found"}), 404


@app.route("/api/warehouse/refresh", methods=["GET", "POST"])
def api_warehouse_refresh():
    try:
        meta = warehouse_etl.run_etl()
        data_profiler.generate_all_profiles()
        return jsonify({
            "status": "ok",
            "message": "Warehouse ETL refreshed and profile cache updated successfully",
            "meta": meta
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/warehouse/schema")
def api_warehouse_schema():
    meta = warehouse_etl.get_warehouse_metadata()
    return jsonify({
        "status": "ok",
        "metadata": meta,
        "schemas": {
            "star": {
                "fact": "FactOrders",
                "dimensions": ["DimDate", "DimGeography", "DimProduct", "DimCustomer", "DimShipping"]
            },
            "snowflake": {
                "fact": "FactOrders",
                "hierarchies": {
                    "geography": ["DimGeography (order_city)", "order_state", "order_country", "order_region", "Market"],
                    "product": ["DimProduct (product_name)", "category_name", "department_name"]
                }
            },
            "galaxy": {
                "facts": ["FactOrders", "FactShippingPerformance"],
                "conformed_dimensions": ["DimDate", "DimGeography", "DimProduct", "DimCustomer", "DimShipping"]
            }
        }
    })


@app.route("/api/warehouse/table/<table_name>")
def api_warehouse_table(table_name):
    try:
        details = warehouse_etl.get_table_details(table_name)
        return jsonify(details)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Academic Classification Suite (Labs 4–5) ──────────────────────────────────

@app.route("/academic/labs/classification")
@app.route("/academic/classification")
def academic_labs_classification():
    initial_res = classification_runner.run_experiment(
        algorithm="random_forest",
        imbalance_strategy="baseline",
        test_size=0.20,
        random_state=42
    )
    benchmarks = classification_runner.get_benchmark_comparison_matrix()
    return render_template(
        "classification.html",
        initial_res=initial_res,
        benchmarks=benchmarks
    )


@app.route("/api/academic/classification/run", methods=["GET", "POST"])
def api_classification_run():
    if request.method == "POST":
        data = request.get_json() or {}
        algorithm = data.get("algorithm", "random_forest")
        imbalance_strategy = data.get("imbalance_strategy", "baseline")
        hyperparams = data.get("hyperparams", {})
        test_size = float(data.get("test_size", 0.20))
        random_state = int(data.get("random_state", 42))
        force_retrain = bool(data.get("force_retrain", False))
    else:
        algorithm = request.args.get("algorithm", "random_forest")
        imbalance_strategy = request.args.get("imbalance_strategy", "baseline")
        hyperparams = {}
        test_size = float(request.args.get("test_size", 0.20))
        random_state = int(request.args.get("random_state", 42))
        force_retrain = request.args.get("force_retrain", "false").lower() == "true"

    try:
        result = classification_runner.run_experiment(
            algorithm=algorithm,
            imbalance_strategy=imbalance_strategy,
            hyperparams=hyperparams,
            test_size=test_size,
            random_state=random_state,
            force_retrain=force_retrain
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/academic/classification/results")
def api_classification_results():
    limit = request.args.get("limit", default=20, type=int)
    runs = classification_runner.get_all_experiment_runs(limit=limit)
    return jsonify({"runs": runs, "count": len(runs)})


@app.route("/api/academic/classification/benchmark")
def api_classification_benchmark():
    bench = classification_runner.get_benchmark_comparison_matrix()
    return jsonify({"benchmark": bench, "count": len(bench)})


@app.route("/api/academic/classification/export")
def api_classification_export():
    fmt = request.args.get("format", "csv").lower()
    bench = classification_runner.get_benchmark_comparison_matrix()
    if fmt == "json":
        return Response(
            json.dumps(bench, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment;filename=classification_benchmark_results.json"}
        )
    else:
        df_exp = pd.DataFrame(bench)
        buf = io.StringIO()
        df_exp.to_csv(buf, index=False)
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=classification_benchmark_results.csv"}
        )


# ── Academic Regression Suite (Lab 6) ─────────────────────────────────────────

@app.route("/academic/labs/regression")
@app.route("/academic/regression")
def academic_labs_regression():
    suite = regression_runner.get_regression_benchmark_suite()
    benchmark_table = suite.get("benchmark_table", [])
    best_model = suite.get("best_model", benchmark_table[0] if benchmark_table else {})
    reg_paths = suite.get("regularization_paths", {})

    # Default to top model as initial active model
    initial_key = best_model.get("model_key", "decision_tree")
    active_res = regression_runner.run_regression_experiment(
        model_key=initial_key,
        test_size=0.20,
        random_state=42
    )

    return render_template(
        "regression.html",
        benchmark_table=benchmark_table,
        best_model=best_model,
        active_res=active_res,
        reg_paths=reg_paths
    )


@app.route("/api/academic/regression/run", methods=["GET", "POST"])
def api_regression_run():
    if request.method == "POST":
        data = request.get_json() or {}
        model_key = data.get("model_key", "random_forest")
        hyperparams = data.get("hyperparams", {})
        test_size = float(data.get("test_size", 0.20))
        random_state = int(data.get("random_state", 42))
        force_retrain = bool(data.get("force_retrain", False))
    else:
        model_key = request.args.get("model_key", "random_forest")
        hyperparams = {}
        test_size = float(request.args.get("test_size", 0.20))
        random_state = int(request.args.get("random_state", 42))
        force_retrain = request.args.get("force_retrain", "false").lower() == "true"

    try:
        result = regression_runner.run_regression_experiment(
            model_key=model_key,
            hyperparams=hyperparams,
            test_size=test_size,
            random_state=random_state,
            force_retrain=force_retrain
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/academic/regression/benchmark")
def api_regression_benchmark():
    suite = regression_runner.get_regression_benchmark_suite()
    return jsonify(suite)


@app.route("/api/academic/regression/results")
def api_regression_results():
    limit = request.args.get("limit", default=20, type=int)
    runs = regression_runner.get_all_regression_runs(limit=limit)
    return jsonify({"runs": runs, "count": len(runs)})


@app.route("/api/academic/regression/export")
def api_regression_export():
    fmt = request.args.get("format", "csv").lower()
    suite = regression_runner.get_regression_benchmark_suite()
    rows = suite.get("benchmark_table", [])

    if fmt == "json":
        return Response(
            json.dumps(suite, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment;filename=regression_benchmark_suite.json"}
        )
    else:
        df_exp = pd.DataFrame(rows)
        buf = io.StringIO()
        df_exp.to_csv(buf, index=False)
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=regression_benchmark_table.csv"}
        )


# ── Lab 7: Customer & Order Clustering ──────────────────────────────────────

@app.route("/academic/labs/clustering")
@app.route("/academic/clustering")
def academic_clustering():
    catalog = academic_runner.get_lab_catalog()
    return render_template(
        "clustering.html",
        catalog=catalog,
        selected_lab=7
    )


@app.route("/api/academic/clustering/run", methods=["GET", "POST"])
def api_clustering_run():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        k = payload.get("k", 4)
        algorithm = payload.get("algorithm", "kmeans")
        random_state = payload.get("random_state", 42)
    else:
        k = request.args.get("k", default=4, type=int)
        algorithm = request.args.get("algorithm", default="kmeans")
        random_state = request.args.get("random_state", default=42, type=int)

    try:
        res = clustering.run_customer_clustering(k=k, algorithm=algorithm, random_state=random_state)
        try:
            db_manager.save_clustering_run(
                k=res["k"],
                algorithm=res["algorithm"],
                metrics=res["metrics"],
                personas=res["personas"]
            )
        except Exception:
            pass
        return jsonify(res)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/academic/clustering/benchmark")
def api_clustering_benchmark():
    try:
        res = clustering.run_customer_clustering(k=4, algorithm="kmeans")
        return jsonify(res)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/academic/clustering/export")
def api_clustering_export():
    fmt = request.args.get("format", "csv").lower()
    k = request.args.get("k", default=4, type=int)
    algorithm = request.args.get("algorithm", default="kmeans")

    content = clustering.export_clustering_data(k=k, algorithm=algorithm, format_type=fmt)
    if fmt == "json":
        return Response(
            content,
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment;filename=customer_clustering_k{k}.json"}
        )
    return Response(
        content,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=customer_clustering_k{k}.csv"}
    )


# ── Lab 8: Association Rule Mining ──────────────────────────────────────────

@app.route("/academic/labs/association-rules")
@app.route("/academic/association-rules")
def academic_association_rules():
    catalog = academic_runner.get_lab_catalog()
    return render_template(
        "association_rules.html",
        catalog=catalog,
        selected_lab=8
    )


@app.route("/api/academic/association-rules/run", methods=["GET", "POST"])
def api_association_rules_run():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        min_support = payload.get("min_support", 0.01)
        min_confidence = payload.get("min_confidence", 0.15)
        item_level = payload.get("item_level", "Category Name")
        max_len = payload.get("max_len", 4)
    else:
        min_support = request.args.get("min_support", default=0.01, type=float)
        min_confidence = request.args.get("min_confidence", default=0.15, type=float)
        item_level = request.args.get("item_level", default="Category Name")
        max_len = request.args.get("max_len", default=4, type=int)

    try:
        res = association_rules.mine_association_rules(
            min_support=min_support,
            min_confidence=min_confidence,
            item_level=item_level,
            max_len=max_len
        )
        try:
            db_manager.save_association_rules_run(
                min_support=res["parameters"]["min_support"],
                min_confidence=res["parameters"]["min_confidence"],
                item_level=res["parameters"]["item_level"],
                overview=res["overview"],
                rules=res["rules"]
            )
        except Exception:
            pass
        return jsonify(res)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/academic/association-rules/benchmark")
def api_association_rules_benchmark():
    try:
        res = association_rules.mine_association_rules(min_support=0.01, min_confidence=0.15)
        return jsonify(res)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/academic/association-rules/export")
def api_association_rules_export():
    fmt = request.args.get("format", "csv").lower()
    min_support = request.args.get("min_support", default=0.01, type=float)
    min_confidence = request.args.get("min_confidence", default=0.15, type=float)
    item_level = request.args.get("item_level", default="Category Name")

    content = association_rules.export_association_rules(
        min_support=min_support,
        min_confidence=min_confidence,
        item_level=item_level,
        format_type=fmt
    )
    if fmt == "json":
        return Response(
            content,
            mimetype="application/json",
            headers={"Content-Disposition": "attachment;filename=association_rules.json"}
        )
    return Response(
        content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=association_rules.csv"}
    )


# ── Lab 9: OLAP Logistics Analytics ─────────────────────────────────────────

@app.route("/academic/labs/olap")
@app.route("/academic/olap")
def academic_olap():
    catalog = academic_runner.get_lab_catalog()
    return render_template(
        "olap.html",
        catalog=catalog,
        selected_lab=9
    )


@app.route("/api/academic/olap/query", methods=["GET", "POST"])
def api_olap_query():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        dimensions = payload.get("dimensions", ["market", "shipping_mode"])
        filters = dict(payload.get("filters", {}))
        if isinstance(payload.get("slices"), dict):
            filters.update(payload["slices"])
        if isinstance(payload.get("dices"), dict):
            filters.update(payload["dices"])
        measures = payload.get("measures", None)
        sort_by = payload.get("sort_by") or payload.get("order_by") or "order_count"
        sort_dir = payload.get("sort_dir") or payload.get("order_dir") or "DESC"
        limit = payload.get("limit", 100)
    else:
        dims_param = request.args.get("dimensions", "market,shipping_mode")
        dimensions = [d.strip() for d in dims_param.split(",") if d.strip()]
        filters = {}
        for k in ["market", "region", "country", "year", "month", "category", "shipping_mode", "customer_segment"]:
            val = request.args.get(k)
            if val:
                filters[k] = val
        measures = None
        sort_by = request.args.get("sort_by", "order_count")
        sort_dir = request.args.get("sort_dir", "DESC")
        limit = request.args.get("limit", default=100, type=int)

    try:
        res = olap_engine.execute_olap_query(
            dimensions=dimensions,
            filters=filters,
            measures=measures,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit
        )
        try:
            db_manager.save_olap_query(
                operation_type=res["operation"],
                dimensions=res["dimensions"],
                filters=res["filters"],
                measure="all",
                row_count=res["records_count"],
                execution_time_ms=res["execution_time_ms"]
            )
        except Exception:
            pass
        return jsonify(res)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/academic/olap/pivot", methods=["GET", "POST"])
def api_olap_pivot():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        row_dim = payload.get("row_dimension", "market")
        col_dim = payload.get("col_dimension", "shipping_mode")
        measure = payload.get("measure", "avg_actual_shipping_days")
        filters = payload.get("filters", {})
    else:
        row_dim = request.args.get("row_dimension", "market")
        col_dim = request.args.get("col_dimension", "shipping_mode")
        measure = request.args.get("measure", "avg_actual_shipping_days")
        filters = {}
        for k in ["market", "shipping_mode", "customer_segment"]:
            val = request.args.get(k)
            if val:
                filters[k] = val

    try:
        res = olap_engine.execute_olap_pivot(
            row_dimension=row_dim,
            col_dimension=col_dim,
            measure=measure,
            filters=filters
        )
        try:
            db_manager.save_olap_query(
                operation_type="Pivot Cross-Tab",
                dimensions=[row_dim, col_dim],
                filters=filters,
                measure=measure,
                row_count=len(res.get("rows", [])),
                execution_time_ms=res.get("execution_time_ms", 0.0)
            )
        except Exception:
            pass
        return jsonify(res)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/academic/olap/members")
def api_olap_members():
    try:
        members = olap_engine.get_dimension_members()
        return jsonify(members)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/academic/olap/export")
def api_olap_export():
    fmt = request.args.get("format", "csv").lower()
    dims_param = request.args.get("dimensions", "market,shipping_mode")
    dimensions = [d.strip() for d in dims_param.split(",") if d.strip()]
    filters = {}
    for k in ["market", "region", "country", "year", "month", "category", "shipping_mode", "customer_segment"]:
        val = request.args.get(k)
        if val:
            filters[k] = val

    content = olap_engine.export_olap_data(
        dimensions=dimensions,
        filters=filters,
        format_type=fmt
    )
    if fmt == "json":
        return Response(
            content,
            mimetype="application/json",
            headers={"Content-Disposition": "attachment;filename=olap_cube_export.json"}
        )
    return Response(
        content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=olap_cube_export.csv"}
    )


# ── Authentication ────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = db_manager.get_user_by_username(username)
        if user and check_password_hash(user["password_hash"], password):
            session["user"] = user["username"]
            session["user_id"] = user["id"]
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("register"))
        hashed = generate_password_hash(password)
        ok = db_manager.create_user(username, hashed)
        if ok:
            flash("Registration successful. Please sign in.", "success")
            return redirect(url_for("login"))
        flash("Username already taken.", "danger")
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("index"))


# ── JSON Prediction API ───────────────────────────────────────────────────────

@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No JSON body provided"}), 400

    market = data.get("Market", "")
    region = data.get("Order Region", "")
    country = data.get("Order Country", "")
    state = data.get("Order State", "")

    is_valid, error_msg = data_pipeline.validate_geo_combination(
        market, region, country, state
    )
    if not is_valid:
        return jsonify({"error": error_msg, "validation_failed": True}), 422

    try:
        result = train_model.predict_single(data)
        user_id = session.get("user_id")
        db_manager.save_prediction(data, result, user_id=user_id, source="api")
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
