import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import PageHeader from '../components/PageHeader';
import MetricCard from '../components/MetricCard';
import { fetchDashboardData } from '../services/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import {
  BarChart3, Clock, AlertTriangle, Cpu, Download, GraduationCap,
  CheckCircle, ArrowRight, RefreshCw, AlertCircle, TrendingUp, Layers, Sliders
} from 'lucide-react';

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetchDashboardData();
      setData(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <RefreshCw className="h-8 w-8 animate-spin mx-auto text-blue-600 mb-3" />
        <p className="text-sm font-semibold text-slate-700">Loading supply-chain dashboard...</p>
        <p className="text-xs text-slate-400 mt-1">Aggregating real operational predictions and model metrics</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="p-6 rounded-2xl bg-red-50 border border-red-200 text-red-700 max-w-lg mx-auto shadow-sm">
          <div className="flex items-center gap-2 font-bold text-base">
            <AlertCircle className="h-5 w-5 text-red-600" />
            <span>Dashboard Data Retrieval Failed</span>
          </div>
          <p className="mt-2 text-xs text-red-600">{error}</p>
          <button
            onClick={loadData}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg text-xs font-semibold hover:bg-red-700 transition"
          >
            Retry Loading
          </button>
        </div>
      </div>
    );
  }

  const kpis = data?.kpis || {};
  const metadata = data?.model_metadata || {};
  const durationDist = data?.duration_distribution || [];
  const watchlist = data?.watchlist || [];
  const history = data?.history || [];
  const comparisons = metadata.model_comparison || [];
  const featureImportances = metadata.top_feature_importances || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <PageHeader
        title="Supply Chain Analytics & Model Insights"
        description="Real operational predictions, duration variance distributions, delayed shipment watchlist, and Random Forest feature importance."
      >
        <a
          href="/dashboard/export_csv"
          download
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-slate-300 text-slate-700 text-xs font-semibold hover:bg-slate-50 transition shadow-2xs"
        >
          <Download className="h-3.5 w-3.5" />
          Export Predictions CSV
        </a>
      </PageHeader>

      {/* Prominent College Lab Mode Banner Card */}
      <div className="relative overflow-hidden bg-gradient-to-r from-blue-900 via-indigo-900 to-slate-900 rounded-2xl p-6 sm:p-7 text-white shadow-md">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-300 text-2xs font-extrabold uppercase tracking-widest">
              COLLEGE CURRICULUM
            </div>
            <h2 className="text-xl sm:text-2xl font-black tracking-tight text-white">
              College Lab Mode
            </h2>
            <p className="text-xs text-slate-300 max-w-xl leading-relaxed">
              Explore the complete Data Warehousing & Mining laboratory curriculum across <strong>Labs 1–10</strong> with empirical experimental outputs, schemas, and implementation procedures.
            </p>
          </div>

          <Link
            to="/college-labs"
            className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-white text-slate-900 text-xs font-bold hover:bg-blue-50 transition shadow-sm shrink-0"
          >
            <GraduationCap className="h-4 w-4 text-blue-600" />
            Enter College Labs 1–10
            <ArrowRight className="h-3.5 w-3.5 text-slate-400" />
          </Link>
        </div>
      </div>

      {/* Real Data KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Predictions"
          value={kpis.total_predictions ?? 0}
          subtitle="Processed via Interactive & Batch API"
          icon={BarChart3}
          color="blue"
        />
        <MetricCard
          title="Average Predicted Duration"
          value={`${kpis.avg_predicted_days ?? 0} Days`}
          subtitle="Whole-day mean logistics duration"
          icon={Clock}
          color="indigo"
        />
        <MetricCard
          title="Longest Predicted Duration"
          value={`${kpis.max_predicted_days ?? 5} Days`}
          subtitle="Peak transit duration logged"
          icon={TrendingUp}
          color="amber"
        />
        <MetricCard
          title="Active Model Architecture"
          value="Random Forest"
          subtitle={`MAE 0.887d | RMSE 1.192d | R² 0.472`}
          icon={Cpu}
          color="slate"
        />
      </div>

      {/* Prediction Distribution & Feature Importance Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left: Duration Distribution Bar Chart (7 cols) */}
        <div className="lg:col-span-7 bg-white rounded-2xl border border-slate-200/90 p-6 sm:p-7 shadow-sm">
          <div className="flex items-center justify-between mb-6 pb-2 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">Shipping Duration Distribution</h3>
              <p className="text-xs text-slate-500 mt-0.5">Real histogram of predicted transit days across order logs</p>
            </div>
            <span className="text-2xs font-bold uppercase tracking-wider px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md border border-blue-100">
              Live DB Predictions
            </span>
          </div>

          <div className="h-64 w-full">
            {durationDist.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={durationDist} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                  <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={{ stroke: '#cbd5e1' }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64748b' }} axisLine={{ stroke: '#cbd5e1' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '10px', fontSize: '12px' }}
                    cursor={{ fill: '#f8fafc' }}
                  />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {durationDist.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.days >= 5 ? '#f59e0b' : '#2563eb'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                No prediction history available yet.
              </div>
            )}
          </div>
        </div>

        {/* Right: Feature Importance (5 cols) */}
        <div className="lg:col-span-5 bg-white rounded-2xl border border-slate-200/90 p-6 sm:p-7 shadow-sm">
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">Model Feature Importance</h3>
              <p className="text-xs text-slate-500 mt-0.5">Random Forest Gini importance weights</p>
            </div>
            <Sliders className="h-4 w-4 text-slate-400" />
          </div>

          <div className="space-y-3 pt-1">
            {featureImportances.slice(0, 6).map((item, idx) => {
              const pct = (item.importance * 100).toFixed(1);
              const label = item.feature.replace('Shipping Mode_', 'Mode: ');
              return (
                <div key={idx} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-700 truncate max-w-[200px]" title={item.feature}>
                      {label}
                    </span>
                    <span className="font-mono text-slate-500 font-medium">{pct}%</span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-blue-600 h-full rounded-full transition-all duration-500"
                      style={{ width: `${Math.max(Number(pct), 3)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <p className="text-2xs text-slate-400 mt-4 text-center">
            Computed deterministically from the production scikit-learn Random Forest regressor.
          </p>
        </div>
      </div>

      {/* Held-out Regression Benchmark Comparison */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 sm:p-7 shadow-sm">
        <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-900">Model Evaluation Benchmarks</h3>
            <p className="text-xs text-slate-500 mt-0.5">Held-out test dataset performance (Lowest RMSE selected for production)</p>
          </div>
          <span className="text-2xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
            Validated Metrics
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {comparisons.map((m, idx) => {
            const isSelected = m.name.includes('Random Forest');
            return (
              <div
                key={idx}
                className={`p-4 rounded-xl border text-xs transition ${
                  isSelected
                    ? 'bg-blue-50/70 border-blue-200 ring-2 ring-blue-500/20'
                    : 'bg-slate-50/50 border-slate-200'
                }`}
              >
                <div className="flex items-center justify-between mb-2 pb-2 border-b border-slate-200/60">
                  <span className={`font-bold ${isSelected ? 'text-blue-900' : 'text-slate-800'}`}>
                    {m.name}
                  </span>
                  {isSelected && (
                    <span className="text-2xs bg-blue-600 text-white px-2 py-0.5 rounded font-extrabold uppercase tracking-wider">
                      Selected
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-2 text-center pt-1">
                  <div>
                    <span className="text-2xs uppercase text-slate-400 block">RMSE</span>
                    <span className="font-extrabold text-slate-800 text-sm">{m.rmse}d</span>
                  </div>
                  <div>
                    <span className="text-2xs uppercase text-slate-400 block">MAE</span>
                    <span className="font-bold text-slate-700 text-sm">{m.mae}d</span>
                  </div>
                  <div>
                    <span className="text-2xs uppercase text-slate-400 block">R²</span>
                    <span className="font-bold text-slate-700 text-sm">{m.r2}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Orders Requiring Attention (High-Duration Watchlist) */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 sm:p-7 shadow-sm">
        <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="h-7 w-7 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
              <AlertTriangle className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Orders Requiring Attention</h3>
              <p className="text-xs text-slate-500">Shipments predicted to require 5 or more days transit time</p>
            </div>
          </div>

          <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
            {watchlist.length} Flagged
          </span>
        </div>

        {watchlist.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="text-2xs uppercase tracking-wider text-slate-400 bg-slate-50/80 border-y border-slate-100">
                <tr>
                  <th className="px-4 py-3 font-semibold">Order ID</th>
                  <th className="px-4 py-3 font-semibold">Predicted Days</th>
                  <th className="px-4 py-3 font-semibold">Scheduled SLA</th>
                  <th className="px-4 py-3 font-semibold">Shipping Mode</th>
                  <th className="px-4 py-3 font-semibold">Market / Region</th>
                  <th className="px-4 py-3 font-semibold">Status Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {watchlist.map((row) => (
                  <tr key={row.id} className="hover:bg-slate-50/80 transition">
                    <td className="px-4 py-3 font-mono font-medium text-slate-400">#{row.id}</td>
                    <td className="px-4 py-3 font-black text-amber-700">{row.predicted_days} Days</td>
                    <td className="px-4 py-3 text-slate-600">{row.scheduled_days} Days</td>
                    <td className="px-4 py-3 font-medium text-slate-800">{row.shipping_mode}</td>
                    <td className="px-4 py-3 text-slate-600">{row.market} &bull; {row.order_region}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded-full text-2xs font-bold bg-amber-100 text-amber-800 border border-amber-200">
                        {row.speed_category}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center text-slate-400 text-xs">
            <CheckCircle className="h-6 w-6 text-emerald-500 mx-auto mb-2" />
            <p className="font-semibold text-slate-700">No Orders Currently Flagged for Extended Transit</p>
            <p className="mt-0.5 text-slate-400">All recent shipments are tracking within standard delivery timelines.</p>
          </div>
        )}
      </div>

      {/* Recent Predictions Table */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 sm:p-7 shadow-sm">
        <div className="flex items-center justify-between mb-4 pb-2 border-b border-slate-100">
          <div>
            <h3 className="text-base font-bold text-slate-900">Recent Prediction Log</h3>
            <p className="text-xs text-slate-500 mt-0.5">Logged predictions from interactive form and batch manifest jobs</p>
          </div>
          <span className="text-xs font-semibold text-slate-400">
            {history.length} Total Logged
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="text-2xs uppercase tracking-wider text-slate-400 bg-slate-50 border-y border-slate-100">
              <tr>
                <th className="px-4 py-3 font-semibold">ID</th>
                <th className="px-4 py-3 font-semibold">Predicted</th>
                <th className="px-4 py-3 font-semibold">Scheduled</th>
                <th className="px-4 py-3 font-semibold">SLA Variance</th>
                <th className="px-4 py-3 font-semibold">Shipping Mode</th>
                <th className="px-4 py-3 font-semibold">Market</th>
                <th className="px-4 py-3 font-semibold">Category</th>
                <th className="px-4 py-3 font-semibold">Source</th>
                <th className="px-4 py-3 font-semibold">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {history.slice(0, 15).map((row) => {
                const diff = (row.predicted_days || 0) - (row.scheduled_days || 0);
                return (
                  <tr key={row.id} className="hover:bg-slate-50/80 transition">
                    <td className="px-4 py-3 font-mono text-slate-400">#{row.id}</td>
                    <td className="px-4 py-3 font-extrabold text-slate-900">{row.predicted_days}d</td>
                    <td className="px-4 py-3 text-slate-600">{row.scheduled_days}d</td>
                    <td className="px-4 py-3">
                      {diff > 0 ? (
                        <span className="text-amber-600 font-bold">+{diff}d</span>
                      ) : diff < 0 ? (
                        <span className="text-emerald-600 font-bold">{diff}d</span>
                      ) : (
                        <span className="text-slate-400 font-medium">0d (exact)</span>
                      )}
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-800">{row.shipping_mode}</td>
                    <td className="px-4 py-3 text-slate-600">{row.market}</td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-0.5 rounded text-2xs font-semibold bg-slate-100 text-slate-700">
                        {row.speed_category}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="uppercase text-2xs font-bold text-slate-400 tracking-wider">
                        {row.source || 'ui'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400 font-mono text-2xs">
                      {row.created_at ? row.created_at.replace('T', ' ').substring(0, 16) : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
