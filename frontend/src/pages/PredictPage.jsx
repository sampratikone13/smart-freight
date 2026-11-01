import React, { useState, useEffect } from 'react';
import PageHeader from '../components/PageHeader';
import PredictionResult from '../components/PredictionResult';
import { fetchHierarchy, predictShipping } from '../services/api';
import { Calculator, RotateCcw, AlertCircle, Sparkles, Calendar, Clock, MapPin, Truck, HelpCircle } from 'lucide-react';

export default function PredictPage() {
  const [hierarchy, setHierarchy] = useState(null);
  const [loadingHierarchy, setLoadingHierarchy] = useState(true);
  const [hierarchyError, setHierarchyError] = useState(null);

  // Cascading lists
  const [regions, setRegions] = useState([]);
  const [countries, setCountries] = useState([]);
  const [categories, setCategories] = useState([]);

  // Form State — Exactly the 20 features expected by the active Random Forest model
  const [formData, setFormData] = useState({
    // 01 — Shipping Details
    'Days for shipment (scheduled)': 4,
    'Shipping Mode': 'Standard Class',
    'Type': 'DEBIT',
    'Customer Segment': 'Consumer',

    // 02 — Customer & Destination
    'Market': 'Europe',
    'Order Region': '',
    'Order Country': '',

    // 03 — Product & Order Details
    'Department Name': '',
    'Category Name': '',
    'Order Item Quantity': 1,
    'Product Price': 180.0,
    'Sales': 180.0,
    'Order Item Discount': 0.0,

    // 04 — Date / Order Information
    'order_date': '2026-05-15',
    'order_hour': 14,
    'order_month': 5,
    'order_day': 15,
    'order_weekday': 4,
    'is_weekend': 0,
    'Latitude': 18.25,
    'Longitude': -66.03,
  });

  const [submitting, setSubmitting] = useState(false);
  const [predictionResult, setPredictionResult] = useState(null);
  const [lastSubmittedPayload, setLastSubmittedPayload] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Load Hierarchy on Mount
  useEffect(() => {
    async function load() {
      try {
        setLoadingHierarchy(true);
        const data = await fetchHierarchy();
        setHierarchy(data);

        const defaultMarket = 'Europe';
        const defaultDept = data.departments?.[0] || 'Fitness';
        
        let initialRegion = '';
        let initialCountry = '';
        if (data.market_regions?.[defaultMarket]?.length) {
          initialRegion = data.market_regions[defaultMarket][0];
          setRegions(data.market_regions[defaultMarket]);

          if (data.region_countries?.[initialRegion]?.length) {
            setCountries(data.region_countries[initialRegion]);
            initialCountry = data.region_countries[initialRegion][0];
          }
        }

        let initialCategory = '';
        if (defaultDept && data.dept_categories?.[defaultDept]?.length) {
          setCategories(data.dept_categories[defaultDept]);
          initialCategory = data.dept_categories[defaultDept][0];
        }

        setFormData(prev => ({
          ...prev,
          'Market': defaultMarket,
          'Order Region': initialRegion,
          'Order Country': initialCountry,
          'Department Name': defaultDept,
          'Category Name': initialCategory,
        }));
      } catch (err) {
        setHierarchyError(err.message);
      } finally {
        setLoadingHierarchy(false);
      }
    }
    load();
  }, []);

  // Cascading Market change
  const handleMarketChange = (e) => {
    const market = e.target.value;
    const availableRegions = hierarchy?.market_regions?.[market] || [];
    setRegions(availableRegions);
    const newRegion = availableRegions[0] || '';

    const availableCountries = hierarchy?.region_countries?.[newRegion] || [];
    setCountries(availableCountries);
    const newCountry = availableCountries[0] || '';

    setFormData(prev => ({
      ...prev,
      'Market': market,
      'Order Region': newRegion,
      'Order Country': newCountry
    }));
  };

  // Cascading Region change
  const handleRegionChange = (e) => {
    const region = e.target.value;
    const availableCountries = hierarchy?.region_countries?.[region] || [];
    setCountries(availableCountries);
    const newCountry = availableCountries[0] || '';

    setFormData(prev => ({
      ...prev,
      'Order Region': region,
      'Order Country': newCountry
    }));
  };

  // Cascading Department change
  const handleDeptChange = (e) => {
    const dept = e.target.value;
    const availableCats = hierarchy?.dept_categories?.[dept] || [];
    setCategories(availableCats);
    const newCat = availableCats[0] || '';

    setFormData(prev => ({
      ...prev,
      'Department Name': dept,
      'Category Name': newCat
    }));
  };

  // Date change handler to auto-derive month, day, weekday, is_weekend
  const handleDateChange = (dateStr) => {
    if (!dateStr) return;
    const d = new Date(dateStr);
    const month = d.getMonth() + 1;
    const day = d.getDate();
    const weekday = d.getDay(); // 0 is Sunday, 6 is Saturday
    const isWeekend = weekday === 0 || weekday === 6 ? 1 : 0;

    setFormData(prev => ({
      ...prev,
      'order_date': dateStr,
      'order_month': month,
      'order_day': day,
      'order_weekday': weekday,
      'is_weekend': isWeekend
    }));
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage(null);
    setSubmitting(true);

    try {
      const payload = {
        'Days for shipment (scheduled)': Number(formData['Days for shipment (scheduled)']),
        'Shipping Mode': formData['Shipping Mode'],
        'Type': formData['Type'],
        'Customer Segment': formData['Customer Segment'],
        'Market': formData['Market'],
        'Order Region': formData['Order Region'],
        'Order Country': formData['Order Country'],
        'Category Name': formData['Category Name'],
        'Department Name': formData['Department Name'],
        'Order Item Quantity': Number(formData['Order Item Quantity']),
        'Product Price': Number(formData['Product Price']),
        'Sales': Number(formData['Sales']),
        'Order Item Discount': Number(formData['Order Item Discount']),
        'Latitude': Number(formData['Latitude']),
        'Longitude': Number(formData['Longitude']),
        'order_month': Number(formData['order_month']),
        'order_day': Number(formData['order_day']),
        'order_weekday': Number(formData['order_weekday']),
        'order_hour': Number(formData['order_hour']),
        'is_weekend': Number(formData['is_weekend']),
      };

      const result = await predictShipping(payload);
      setPredictionResult(result);
      setLastSubmittedPayload(payload);
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleReset = () => {
    setPredictionResult(null);
    setErrorMessage(null);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <PageHeader
        title="Predict Shipping Duration"
        description="Estimate whole-day delivery duration with carrier SLA variance and delay risk classification using the production Random Forest regression model."
      />

      {hierarchyError && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-2">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>Failed to connect to data hierarchy: {hierarchyError}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Form (7 cols) */}
        <div className="lg:col-span-7">
          <div className="bg-white rounded-2xl border border-slate-200/90 p-6 sm:p-8 shadow-sm">
            <form onSubmit={handleSubmit} className="space-y-8">

              {/* 01 — Shipping Details */}
              <div>
                <div className="flex items-center gap-2.5 pb-2.5 mb-4 border-b border-slate-100">
                  <span className="h-6 w-6 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-2xs">
                    01
                  </span>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                    Shipping Details & SLA
                  </h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Days for Shipment (Scheduled) *
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="15"
                      required
                      value={formData['Days for shipment (scheduled)']}
                      onChange={(e) => handleInputChange('Days for shipment (scheduled)', e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition"
                    />
                    <span className="text-2xs text-slate-400 mt-1 block">SLA delivery commitment</span>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Shipping Mode *
                    </label>
                    <select
                      value={formData['Shipping Mode']}
                      onChange={(e) => handleInputChange('Shipping Mode', e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition bg-white"
                      required
                    >
                      {hierarchy?.shipping_modes?.map((mode) => (
                        <option key={mode} value={mode}>{mode}</option>
                      ))}
                    </select>
                    <span className="text-2xs text-slate-400 mt-1 block">Carrier fulfillment tier</span>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Payment / Order Type *
                    </label>
                    <select
                      value={formData['Type']}
                      onChange={(e) => handleInputChange('Type', e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition bg-white"
                      required
                    >
                      {hierarchy?.types?.map((t) => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                    <span className="text-2xs text-slate-400 mt-1 block">Transaction clearance method</span>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Customer Segment *
                    </label>
                    <select
                      value={formData['Customer Segment']}
                      onChange={(e) => handleInputChange('Customer Segment', e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition bg-white"
                      required
                    >
                      {hierarchy?.customer_segments?.map((seg) => (
                        <option key={seg} value={seg}>{seg}</option>
                      ))}
                    </select>
                    <span className="text-2xs text-slate-400 mt-1 block">Account classification</span>
                  </div>
                </div>
              </div>

              {/* 02 — Customer & Destination */}
              <div>
                <div className="flex items-center gap-2.5 pb-2.5 mb-4 border-b border-slate-100">
                  <span className="h-6 w-6 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-2xs">
                    02
                  </span>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                    Customer & Destination Geography
                  </h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Market *
                    </label>
                    <select
                      value={formData['Market']}
                      onChange={handleMarketChange}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition bg-white"
                      required
                    >
                      {hierarchy?.markets?.map((m) => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                    <span className="text-2xs text-slate-400 mt-1 block">Continental zone</span>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Order Region *
                    </label>
                    <select
                      value={formData['Order Region']}
                      onChange={handleRegionChange}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition bg-white"
                      required
                    >
                      {regions.map((r) => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                    </select>
                    <span className="text-2xs text-slate-400 mt-1 block">Cascading sub-market</span>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Order Country *
                    </label>
                    <select
                      value={formData['Order Country']}
                      onChange={(e) => handleInputChange('Order Country', e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition bg-white"
                      required
                    >
                      {countries.map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                    <span className="text-2xs text-slate-400 mt-1 block">Destination country</span>
                  </div>
                </div>
              </div>

              {/* 03 — Product & Order Details */}
              <div>
                <div className="flex items-center gap-2.5 pb-2.5 mb-4 border-b border-slate-100">
                  <span className="h-6 w-6 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-2xs">
                    03
                  </span>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                    Product & Commercial Details
                  </h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Department Name *
                    </label>
                    <select
                      value={formData['Department Name']}
                      onChange={handleDeptChange}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition bg-white"
                      required
                    >
                      {hierarchy?.departments?.map((dep) => (
                        <option key={dep} value={dep}>{dep}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Category Name *
                    </label>
                    <select
                      value={formData['Category Name']}
                      onChange={(e) => handleInputChange('Category Name', e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition bg-white"
                      required
                    >
                      {categories.map((cat) => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Item Quantity *
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="20"
                      required
                      value={formData['Order Item Quantity']}
                      onChange={(e) => handleInputChange('Order Item Quantity', e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Product Unit Price ($) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      required
                      value={formData['Product Price']}
                      onChange={(e) => {
                        const val = e.target.value;
                        handleInputChange('Product Price', val);
                        handleInputChange('Sales', val);
                      }}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Sales Total ($) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      required
                      value={formData['Sales']}
                      onChange={(e) => handleInputChange('Sales', e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Order Item Discount ($)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      value={formData['Order Item Discount']}
                      onChange={(e) => handleInputChange('Order Item Discount', e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition"
                    />
                  </div>
                </div>
              </div>

              {/* 04 — Date / Order Information */}
              <div>
                <div className="flex items-center gap-2.5 pb-2.5 mb-4 border-b border-slate-100">
                  <span className="h-6 w-6 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold text-xs shadow-2xs">
                    04
                  </span>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                    Date & Origin Coordinates
                  </h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Order Dispatch Date *
                    </label>
                    <input
                      type="date"
                      required
                      value={formData['order_date']}
                      onChange={(e) => handleDateChange(e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition bg-white"
                    />
                    <span className="text-2xs text-slate-400 mt-1 block">Derives month, day, weekend</span>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Order Hour (0–23) *
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="23"
                      required
                      value={formData['order_hour']}
                      onChange={(e) => handleInputChange('order_hour', e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition"
                    />
                    <span className="text-2xs text-slate-400 mt-1 block">Dispatch clearance hour</span>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Warehouse Origin Lat / Lon
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="number"
                        step="0.01"
                        value={formData['Latitude']}
                        onChange={(e) => handleInputChange('Latitude', e.target.value)}
                        className="w-1/2 px-2.5 py-2 text-xs rounded-lg border border-slate-300"
                        title="Latitude"
                      />
                      <input
                        type="number"
                        step="0.01"
                        value={formData['Longitude']}
                        onChange={(e) => handleInputChange('Longitude', e.target.value)}
                        className="w-1/2 px-2.5 py-2 text-xs rounded-lg border border-slate-300"
                        title="Longitude"
                      />
                    </div>
                    <span className="text-2xs text-slate-400 mt-1 block">Default: PR Hub (18.25, -66.03)</span>
                  </div>
                </div>
              </div>

              {/* Submit / Reset Actions */}
              <div className="pt-4 flex items-center gap-3">
                <button
                  type="submit"
                  disabled={submitting || loadingHierarchy}
                  className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50 transition shadow-sm hover:shadow text-sm"
                >
                  <Calculator className="h-4 w-4" />
                  {submitting ? 'Running Regression Model...' : 'Predict Shipping Duration'}
                </button>
                <button
                  type="button"
                  onClick={handleReset}
                  className="p-3.5 rounded-xl border border-slate-300 text-slate-600 hover:bg-slate-50 transition shadow-2xs"
                  title="Clear result"
                >
                  <RotateCcw className="h-4 w-4" />
                </button>
              </div>

            </form>
          </div>
        </div>

        {/* Right Result Column (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {errorMessage && (
            <div className="p-5 rounded-2xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-3 shadow-2xs">
              <AlertCircle className="h-5 w-5 shrink-0 mt-0.5 text-red-600" />
              <div>
                <p className="font-bold text-sm">Prediction Request Failed</p>
                <p className="mt-1 text-xs text-red-600 leading-relaxed">{errorMessage}</p>
              </div>
            </div>
          )}

          {predictionResult ? (
            <PredictionResult result={predictionResult} submittedData={lastSubmittedPayload} />
          ) : (
            <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-8 text-center text-slate-400 shadow-2xs">
              <div className="h-12 w-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-4">
                <Truck className="h-6 w-6" />
              </div>
              <h4 className="text-sm font-bold text-slate-800">Ready for Regression Prediction</h4>
              <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto leading-relaxed">
                Provide order parameters across the 4 numbered sections and click <strong>Predict Shipping Duration</strong> to calculate whole-day delivery expectations.
              </p>
            </div>
          )}

          {/* Model Specification Card */}
          <div className="bg-white rounded-2xl border border-slate-200/90 p-6 shadow-2xs">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 pb-2 border-b border-slate-100">
              Active Regression Architecture
            </h4>
            <div className="space-y-2.5 text-xs text-slate-600">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Model Algorithm</span>
                <span className="font-semibold text-slate-800">RandomForestRegressor (100 trees)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Pre-Shipment Features</span>
                <span className="font-semibold text-slate-800">20 Parameters (Pre-dispatch)</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Preprocessing</span>
                <span className="font-semibold text-slate-800">ColumnTransformer + OneHotEncoder</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-400">Target Metric</span>
                <span className="font-semibold text-slate-800">Days for shipping (real)</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Evaluation Benchmark</span>
                <span className="font-semibold text-blue-600">MAE 0.887d | RMSE 1.192d | R² 0.472</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
