import React, { useState } from 'react';
import PageHeader from '../components/PageHeader';
import { uploadBatchPrediction } from '../services/api';
import {
  Upload, FileText, Download, CheckCircle, AlertCircle, RefreshCw,
  Layers, ArrowRight, Table, CheckCircle2
} from 'lucide-react';

export default function BatchPredictPage() {
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [resultsData, setResultsData] = useState(null);
  const [error, setError] = useState(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith('.csv')) {
        setFile(droppedFile);
        setError(null);
        setResultsData(null);
      } else {
        setError('Please drop a valid .csv file format.');
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResultsData(null);
    }
  };

  const handleUploadAndPredict = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a CSV file first.');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      const res = await uploadBatchPrediction(file);
      setResultsData(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <PageHeader
        title="Batch Shipping Manifest Prediction"
        description="Upload multi-order CSV manifests to generate automated whole-day shipping duration estimates and delay risk classifications."
      >
        <a
          href="/batch_predict/sample"
          download
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-slate-300 text-slate-700 text-xs font-semibold hover:bg-slate-50 transition shadow-2xs"
        >
          <Download className="h-3.5 w-3.5" />
          Download Sample CSV
        </a>
      </PageHeader>

      {/* Visual Workflow Steps */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
        <div className={`p-3 rounded-xl border flex items-center gap-2.5 ${file ? 'bg-blue-50/70 border-blue-200 text-blue-900 font-semibold' : 'bg-white border-slate-200 text-slate-600'}`}>
          <span className="h-5 w-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-2xs font-bold shrink-0">1</span>
          <span>Upload CSV</span>
        </div>
        <div className={`p-3 rounded-xl border flex items-center gap-2.5 ${file && !resultsData ? 'bg-blue-50/70 border-blue-200 text-blue-900 font-semibold' : resultsData ? 'bg-slate-50 border-slate-200 text-slate-500' : 'bg-white border-slate-200 text-slate-400'}`}>
          <span className="h-5 w-5 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center text-2xs font-bold shrink-0">2</span>
          <span>Preview File</span>
        </div>
        <div className={`p-3 rounded-xl border flex items-center gap-2.5 ${uploading ? 'bg-blue-50/70 border-blue-200 text-blue-900 font-semibold' : 'bg-white border-slate-200 text-slate-400'}`}>
          <span className="h-5 w-5 rounded-full bg-slate-200 text-slate-700 flex items-center justify-center text-2xs font-bold shrink-0">3</span>
          <span>Generate Predictions</span>
        </div>
        <div className={`p-3 rounded-xl border flex items-center gap-2.5 ${resultsData ? 'bg-emerald-50/80 border-emerald-200 text-emerald-900 font-semibold' : 'bg-white border-slate-200 text-slate-400'}`}>
          <span className="h-5 w-5 rounded-full bg-emerald-600 text-white flex items-center justify-center text-2xs font-bold shrink-0">4</span>
          <span>Download Output</span>
        </div>
      </div>

      {/* Upload Drag & Drop Card */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-6 sm:p-8 shadow-sm">
        <form onSubmit={handleUploadAndPredict} className="space-y-6">
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-10 text-center transition-all ${
              dragActive 
                ? 'border-blue-500 bg-blue-50/50 scale-[1.005]' 
                : file 
                  ? 'border-blue-400/80 bg-blue-50/20' 
                  : 'border-slate-300 bg-slate-50/50 hover:border-slate-400'
            }`}
          >
            <div className="h-12 w-12 rounded-2xl bg-white border border-slate-200 text-blue-600 flex items-center justify-center mx-auto mb-4 shadow-2xs">
              <Upload className="h-6 w-6" />
            </div>

            <p className="text-base font-bold text-slate-800">
              {file ? file.name : 'Select or drag & drop a logistics CSV manifest'}
            </p>

            <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
              {file 
                ? `${(file.size / 1024).toFixed(1)} KB &bull; Ready to process through Random Forest pipeline` 
                : 'Accepts standard DataCo pre-shipment columns with scheduled SLA days, mode, market, and pricing.'}
            </p>
            
            <input
              type="file"
              accept=".csv"
              id="csvFileInput"
              onChange={handleFileChange}
              className="hidden"
            />
            
            <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
              <label
                htmlFor="csvFileInput"
                className="cursor-pointer inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white border border-slate-300 text-slate-700 text-xs font-semibold hover:bg-slate-50 transition shadow-2xs"
              >
                <FileText className="h-4 w-4" />
                {file ? 'Choose Different File' : 'Browse Local Files'}
              </label>

              {file && (
                <button
                  type="submit"
                  disabled={uploading}
                  className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition shadow-sm disabled:opacity-50"
                >
                  {uploading ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      Running Batch Regression...
                    </>
                  ) : (
                    <>
                      <Layers className="h-4 w-4" />
                      Generate Batch Predictions
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </form>

        {error && (
          <div className="mt-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-start gap-3 shadow-2xs">
            <AlertCircle className="h-5 w-5 shrink-0 text-red-600 mt-0.5" />
            <div>
              <p className="font-bold text-sm">Batch Ingestion Error</p>
              <p className="mt-0.5 text-red-600">{error}</p>
            </div>
          </div>
        )}
      </div>

      {/* Results Section */}
      {resultsData && (
        <div className="space-y-6 animate-fadeIn">
          {/* Summary Row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-2xs">
              <p className="text-2xs font-bold uppercase tracking-wider text-slate-400">Total Rows Ingested</p>
              <p className="text-2xl font-black text-slate-900 mt-1">{resultsData.total}</p>
            </div>
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-2xs">
              <p className="text-2xs font-bold uppercase tracking-wider text-slate-400">Previewed Sample</p>
              <p className="text-2xl font-black text-slate-900 mt-1">{resultsData.previewed}</p>
            </div>
            <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-2xs flex items-center justify-between">
              <div>
                <p className="text-2xs font-bold uppercase tracking-wider text-slate-400">Enriched Manifest</p>
                <p className="text-xs font-bold text-emerald-700 mt-1 flex items-center gap-1">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" /> Whole-day predictions ready
                </p>
              </div>
              <a
                href="/batch_predict/download"
                download
                className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 transition shadow-sm"
              >
                <Download className="h-3.5 w-3.5" />
                Download CSV
              </a>
            </div>
          </div>

          {/* Results Table */}
          <div className="bg-white rounded-2xl border border-slate-200/90 overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h3 className="font-bold text-slate-900 text-sm">Batch Output Preview (First {resultsData.previewed} Records)</h3>
              <span className="text-2xs font-semibold text-slate-400">Whole-day integer duration</span>
            </div>

            <div className="overflow-x-auto max-h-96">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="text-2xs uppercase tracking-wider text-slate-400 bg-slate-50 border-b border-slate-100 sticky top-0">
                  <tr>
                    <th className="px-4 py-3 font-semibold">Row</th>
                    <th className="px-4 py-3 font-semibold">Predicted Duration</th>
                    <th className="px-4 py-3 font-semibold">Scheduled SLA</th>
                    <th className="px-4 py-3 font-semibold">Shipping Speed</th>
                    <th className="px-4 py-3 font-semibold">Shipping Mode</th>
                    <th className="px-4 py-3 font-semibold">Market</th>
                    <th className="px-4 py-3 font-semibold">Order Region</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {resultsData.results?.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/80 transition">
                      <td className="px-4 py-2.5 font-mono text-slate-400">#{idx + 1}</td>
                      <td className="px-4 py-2.5 font-black text-blue-600">
                        {row.predicted_shipping_days} Days
                      </td>
                      <td className="px-4 py-2.5 text-slate-600">
                        {row['Days for shipment (scheduled)'] || '—'} Days
                      </td>
                      <td className="px-4 py-2.5">
                        <span className="px-2 py-0.5 rounded text-2xs font-semibold bg-slate-100 text-slate-700">
                          {row.shipping_speed_category || 'Standard'}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 font-medium text-slate-800">{row['Shipping Mode'] || '—'}</td>
                      <td className="px-4 py-2.5 text-slate-600">{row['Market'] || '—'}</td>
                      <td className="px-4 py-2.5 text-slate-500">{row['Order Region'] || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
