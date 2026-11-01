import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight, FileSpreadsheet, Cpu, Clock, CheckCircle2, ShieldCheck,
  Zap, Package, MapPin, Truck, ChevronRight, BarChart3
} from 'lucide-react';

export default function HomePage() {
  return (
    <div className="relative overflow-hidden">
      {/* Subtle background ambient gradients (restrained, SaaS style) */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 bg-gradient-to-b from-blue-50/60 via-slate-50/30 to-transparent pointer-events-none -z-10" />

      {/* Hero Section */}
      <section className="pt-16 pb-12 md:pt-24 md:pb-20 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Subtle pill badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50 border border-blue-200/80 text-blue-700 text-xs font-semibold uppercase tracking-wider mb-8 shadow-2xs">
          <Zap className="h-3.5 w-3.5 text-blue-600" />
          Production-Grade Logistics Regression
        </div>

        {/* Main Headings */}
        <h1 className="text-4xl sm:text-6xl font-black text-slate-900 tracking-tight leading-tight md:leading-none">
          Smart Freight
        </h1>
        
        <p className="mt-4 text-xl sm:text-2xl font-semibold text-blue-600 tracking-tight">
          Intelligent Shipping Duration Prediction
        </p>

        {/* Concise Professional Description */}
        <p className="mt-6 text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
          Predict the expected shipping duration of any order using machine learning trained on historical logistics data and real-world delivery patterns.
        </p>

        {/* Primary and Secondary CTA Buttons */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/predict"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 transition shadow-sm hover:shadow text-sm sm:text-base group"
          >
            Predict Shipping Days
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
          <Link
            to="/dashboard"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-white border border-slate-300 text-slate-700 font-semibold hover:bg-slate-50 hover:text-slate-900 transition shadow-2xs text-sm sm:text-base"
          >
            <BarChart3 className="h-4 w-4 text-slate-500" />
            Explore Dashboard
          </Link>
        </div>
      </section>

      {/* Visual Prediction Engine Concept with Rich Depth */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 sm:p-8">
          <div className="text-center mb-8">
            <h2 className="text-xs uppercase tracking-widest font-bold text-slate-400">
              End-to-End Prediction Pipeline
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative items-center">
            {/* Step 1: Order Information */}
            <div className="relative bg-slate-50/80 rounded-xl border border-slate-200 p-6 flex flex-col items-center text-center">
              <div className="h-12 w-12 rounded-xl bg-white border border-slate-200 text-blue-600 flex items-center justify-center mb-4 shadow-2xs">
                <Package className="h-6 w-6" />
              </div>
              <h3 className="font-bold text-slate-900 text-base">Order Information</h3>
              <p className="mt-2 text-xs text-slate-500 leading-normal">
                Scheduled SLA days, shipping mode, destination market, category, and payment type.
              </p>
              <div className="mt-4 flex flex-wrap justify-center gap-1.5 text-2xs font-medium text-slate-600">
                <span className="px-2 py-0.5 rounded bg-white border border-slate-200">Standard Class</span>
                <span className="px-2 py-0.5 rounded bg-white border border-slate-200">Western Europe</span>
                <span className="px-2 py-0.5 rounded bg-white border border-slate-200">SLA: 4d</span>
              </div>
            </div>

            {/* Step 2: Prediction Engine */}
            <div className="relative bg-gradient-to-b from-blue-50/60 to-slate-50/80 rounded-xl border border-blue-200/80 p-6 flex flex-col items-center text-center shadow-xs">
              <div className="h-12 w-12 rounded-xl bg-blue-600 text-white flex items-center justify-center mb-4 shadow-sm">
                <Cpu className="h-6 w-6" />
              </div>
              <h3 className="font-bold text-slate-900 text-base">Prediction Engine</h3>
              <p className="mt-2 text-xs text-slate-500 leading-normal">
                Production Random Forest pipeline with 20 pre-shipment features and zero leakage.
              </p>
              <div className="mt-4 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-100/70 text-blue-800 text-2xs font-semibold">
                <Zap className="h-3 w-3 text-blue-600" />
                Random Forest Regressor
              </div>
            </div>

            {/* Step 3: Estimated Shipping Duration */}
            <div className="relative bg-slate-50/80 rounded-xl border border-slate-200 p-6 flex flex-col items-center text-center">
              <div className="h-12 w-12 rounded-xl bg-white border border-slate-200 text-emerald-600 flex items-center justify-center mb-4 shadow-2xs">
                <Clock className="h-6 w-6" />
              </div>
              <h3 className="font-bold text-slate-900 text-base">Estimated Shipping Duration</h3>
              <p className="mt-2 text-xs text-slate-500 leading-normal">
                Clear whole-day arrival estimate paired with automated SLA delay-risk detection.
              </p>
              <div className="mt-4 flex items-center gap-2">
                <span className="text-xl font-black text-slate-900">4 Days</span>
                <span className="px-2 py-0.5 rounded-full text-2xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                  On Schedule
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Highlights Grid */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pb-20">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs">
            <div className="h-9 w-9 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
              <CheckCircle2 className="h-5 w-5" />
            </div>
            <h4 className="text-sm font-bold text-slate-900">Whole-Day Deliveries</h4>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Operational transit predictions formatted cleanly as full days for carrier dispatch and customer SLA communication.
            </p>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs">
            <div className="h-9 w-9 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <h4 className="text-sm font-bold text-slate-900">Pre-Shipment Parameters</h4>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Relies strictly on attributes available prior to parcel dispatch, guaranteeing zero data leakage or unrealistic features.
            </p>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs">
            <div className="h-9 w-9 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center mb-3">
              <Truck className="h-5 w-5" />
            </div>
            <h4 className="text-sm font-bold text-slate-900">Batch Manifest Ingestion</h4>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Process hundreds of shipments at once via CSV upload with instant validation, table previews, and enriched CSV exports.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
