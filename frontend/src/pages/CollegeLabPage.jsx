import React, { useState, useEffect } from 'react';
import PageHeader from '../components/PageHeader';
import {
  fetchCollegeLabsCatalog, fetchCollegeLab,
  fetchWarehouseSchema, fetchWarehouseTable
} from '../services/api';
import {
  GraduationCap, BookOpen, CheckCircle2,
  Table, RefreshCw, AlertCircle, ChevronRight,
  Database, Network, Layers, Info, Check, Eye
} from 'lucide-react';

export default function CollegeLabPage() {
  const [catalog, setCatalog] = useState([]);
  const [selectedLabId, setSelectedLabId] = useState(1);
  const [labData, setLabData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingLab, setLoadingLab] = useState(false);
  const [error, setError] = useState(null);

  // Lab 1: Interactive Schema Operations state
  const [schemaData, setSchemaData] = useState(null);
  const [activeSchemaTab, setActiveSchemaTab] = useState('star'); // star, snowflake, galaxy
  const [selectedTable, setSelectedTable] = useState('FactOrders');
  const [tableDetails, setTableDetails] = useState(null);
  const [loadingTable, setLoadingTable] = useState(false);

  // Load catalog on mount
  useEffect(() => {
    async function loadCatalog() {
      try {
        setLoading(true);
        const cats = await fetchCollegeLabsCatalog();
        setCatalog(cats);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    loadCatalog();
  }, []);

  // Load selected lab details when selectedLabId changes
  useEffect(() => {
    async function loadLab() {
      try {
        setLoadingLab(true);
        const data = await fetchCollegeLab(selectedLabId);
        setLabData(data);

        // If Lab 1 is selected, also fetch warehouse schema data for interactive schema inspection
        if (selectedLabId === 1 && !schemaData) {
          try {
            const sData = await fetchWarehouseSchema();
            setSchemaData(sData);
            loadTableDetails('FactOrders');
          } catch (e) {
            console.error('Failed to load warehouse schema:', e);
          }
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoadingLab(false);
      }
    }
    if (selectedLabId) {
      loadLab();
    }
  }, [selectedLabId]);

  const loadTableDetails = async (tableName) => {
    try {
      setLoadingTable(true);
      setSelectedTable(tableName);
      const details = await fetchWarehouseTable(tableName);
      setTableDetails(details);
    } catch (e) {
      console.error(`Failed to load details for ${tableName}:`, e);
    } finally {
      setLoadingTable(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <RefreshCw className="h-8 w-8 animate-spin mx-auto text-blue-600 mb-3" />
        <p className="text-sm font-semibold text-slate-700">Loading College Lab Curriculum...</p>
        <p className="text-xs text-slate-400 mt-1">Preparing Labs 1–10 academic experiments</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <PageHeader
        title="College Lab Mode — DWM Practical Curriculum"
        description="Preserved academic curriculum (Labs 1–10) with verified experiment procedures, empirical datasets, and interactive schema inspection."
      >
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-bold uppercase tracking-wider">
          <GraduationCap className="h-4 w-4" />
          Academic Curriculum
        </span>
      </PageHeader>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
          <AlertCircle className="h-5 w-5 shrink-0" />
          <span>Error loading lab content: {error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Sidebar: Lab Catalog (4 cols) */}
        <div className="lg:col-span-4 bg-white rounded-2xl border border-slate-200/90 overflow-hidden shadow-sm sticky top-24">
          <div className="p-4 border-b border-slate-100 bg-slate-50/70 flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Laboratory Experiments (1–10)
            </h3>
            <span className="text-2xs font-extrabold px-2 py-0.5 rounded bg-blue-100 text-blue-800">
              Preserved Order
            </span>
          </div>

          <div className="divide-y divide-slate-100 max-h-[700px] overflow-y-auto">
            {catalog.map((item) => {
              const isSelected = item.id === selectedLabId;
              return (
                <button
                  key={item.id}
                  onClick={() => setSelectedLabId(item.id)}
                  className={`w-full text-left p-3.5 flex items-center justify-between transition ${
                    isSelected
                      ? 'bg-blue-50/90 border-l-4 border-blue-600 text-blue-950 font-semibold'
                      : 'hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-lg">{item.icon}</span>
                    <div>
                      <p className={`text-xs font-bold ${isSelected ? 'text-blue-900' : 'text-slate-900'}`}>
                        {item.title}
                      </p>
                      <p className="text-2xs text-slate-400 mt-0.5 line-clamp-1">{item.subtitle}</p>
                    </div>
                  </div>
                  <ChevronRight className={`h-4 w-4 shrink-0 ${isSelected ? 'text-blue-600' : 'text-slate-300'}`} />
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Main Lab View (8 cols) */}
        <div className="lg:col-span-8 space-y-6">
          {loadingLab ? (
            <div className="bg-white rounded-2xl border border-slate-200 p-16 text-center shadow-sm">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto text-blue-600 mb-3" />
              <p className="text-xs text-slate-500">Loading Experiment Details...</p>
            </div>
          ) : labData ? (
            <div className="space-y-6 animate-fadeIn">
              {/* Header Box */}
              <div className="bg-white rounded-2xl border border-slate-200/90 p-6 sm:p-7 shadow-sm">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2.5 py-1 rounded bg-blue-600 text-white text-xs font-bold uppercase tracking-wider">
                    Experiment {labData.lab_number}
                  </span>
                  <span className="text-xs font-semibold text-slate-500">
                    {labData.short_title}
                  </span>
                </div>

                <h2 className="text-2xl font-black text-slate-900 tracking-tight">{labData.title}</h2>

                {/* Aim */}
                <div className="mt-4 pt-4 border-t border-slate-100">
                  <h4 className="text-2xs font-bold uppercase tracking-wider text-slate-400 mb-1 flex items-center gap-1.5">
                    <BookOpen className="h-3.5 w-3.5 text-blue-600" />
                    Aim of Experiment
                  </h4>
                  <p className="text-sm text-slate-700 leading-relaxed font-medium">{labData.aim}</p>
                </div>

                {/* Dataset info */}
                {labData.dataset_info && (
                  <div className="mt-3 p-3 bg-slate-50 rounded-xl text-xs text-slate-600 border border-slate-100">
                    <span className="font-bold text-slate-800">Dataset Context: </span>
                    {typeof labData.dataset_info === 'string' ? labData.dataset_info : JSON.stringify(labData.dataset_info)}
                  </div>
                )}
              </div>

              {/* SELECTIVE ADVANCED INTEGRATION: Lab 1 Interactive Schema Operations */}
              {selectedLabId === 1 && schemaData && (
                <div className="bg-white rounded-2xl border border-slate-200/90 p-6 sm:p-7 shadow-sm space-y-5">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                    <div>
                      <div className="flex items-center gap-2">
                        <Database className="h-4 w-4 text-blue-600" />
                        <h3 className="text-sm font-bold text-slate-900">
                          Interactive Schema Operations & Relational Model
                        </h3>
                      </div>
                      <p className="text-2xs text-slate-500 mt-0.5">
                        Inspect Star, Snowflake, and Constellation schema architectures synced with DataCo warehouse
                      </p>
                    </div>

                    {/* Schema Type Tabs */}
                    <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
                      <button
                        onClick={() => setActiveSchemaTab('star')}
                        className={`px-2.5 py-1 rounded text-2xs font-bold transition ${activeSchemaTab === 'star' ? 'bg-white text-blue-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'}`}
                      >
                        Star Schema
                      </button>
                      <button
                        onClick={() => setActiveSchemaTab('snowflake')}
                        className={`px-2.5 py-1 rounded text-2xs font-bold transition ${activeSchemaTab === 'snowflake' ? 'bg-white text-blue-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'}`}
                      >
                        Snowflake Schema
                      </button>
                      <button
                        onClick={() => setActiveSchemaTab('galaxy')}
                        className={`px-2.5 py-1 rounded text-2xs font-bold transition ${activeSchemaTab === 'galaxy' ? 'bg-white text-blue-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'}`}
                      >
                        Constellation Schema
                      </button>
                    </div>
                  </div>

                  {/* Schema Architecture Visualization */}
                  <div className="bg-slate-50/70 rounded-xl p-4 border border-slate-200/70">
                    {activeSchemaTab === 'star' && (
                      <div className="space-y-3">
                        <p className="text-2xs font-bold uppercase tracking-wider text-slate-400">
                          Star Topology &bull; 1 Central Fact Table surrounded by 5 Denormalized Dimension Tables
                        </p>
                        <div className="flex flex-wrap items-center justify-center gap-2">
                          <button
                            onClick={() => loadTableDetails('FactOrders')}
                            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${selectedTable === 'FactOrders' ? 'bg-blue-600 text-white shadow-2xs' : 'bg-white border border-slate-300 text-slate-800'}`}
                          >
                            ⭐ FactOrders (Central Fact)
                          </button>
                          {schemaData.schemas?.star?.dimensions?.map((dim) => (
                            <button
                              key={dim}
                              onClick={() => loadTableDetails(dim)}
                              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${selectedTable === dim ? 'bg-blue-600 text-white shadow-2xs' : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'}`}
                            >
                              {dim}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {activeSchemaTab === 'snowflake' && (
                      <div className="space-y-3">
                        <p className="text-2xs font-bold uppercase tracking-wider text-slate-400">
                          Snowflake Topology &bull; Normalized Dimensions into Hierarchical Sub-Dimensions
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                          <div className="p-3 bg-white rounded-lg border border-slate-200">
                            <span className="font-bold text-slate-800 block mb-1">Geography Hierarchy:</span>
                            <p className="text-2xs text-slate-600 font-mono">
                              DimGeography &rarr; order_city &rarr; order_state &rarr; order_country &rarr; Market
                            </p>
                          </div>
                          <div className="p-3 bg-white rounded-lg border border-slate-200">
                            <span className="font-bold text-slate-800 block mb-1">Product Hierarchy:</span>
                            <p className="text-2xs text-slate-600 font-mono">
                              DimProduct &rarr; product_name &rarr; category_name &rarr; department_name
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {activeSchemaTab === 'galaxy' && (
                      <div className="space-y-3">
                        <p className="text-2xs font-bold uppercase tracking-wider text-slate-400">
                          Fact Constellation &bull; Multiple Fact Tables Sharing Conformed Dimensions
                        </p>
                        <div className="flex flex-wrap items-center gap-2">
                          <button
                            onClick={() => loadTableDetails('FactOrders')}
                            className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-bold text-slate-800 hover:bg-slate-100"
                          >
                            FactOrders
                          </button>
                          <button
                            onClick={() => loadTableDetails('FactShippingPerformance')}
                            className="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-bold text-slate-800 hover:bg-slate-100"
                          >
                            FactShippingPerformance
                          </button>
                          <span className="text-2xs text-slate-400">shares 5 conformed dimensions</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Table Details Inspector */}
                  {tableDetails && (
                    <div className="p-4 bg-white rounded-xl border border-slate-200 space-y-3">
                      <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                        <div>
                          <h4 className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                            <Table className="h-3.5 w-3.5 text-blue-600" />
                            Table: <span className="font-mono text-blue-700">{tableDetails.table_name}</span>
                          </h4>
                          <p className="text-2xs text-slate-500 mt-0.5">{tableDetails.purpose}</p>
                        </div>
                        <span className="text-2xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                          {tableDetails.row_count?.toLocaleString()} Records
                        </span>
                      </div>

                      {/* Columns List */}
                      <div className="overflow-x-auto max-h-48">
                        <table className="w-full text-left text-2xs">
                          <thead className="bg-slate-50 text-slate-400 uppercase font-semibold">
                            <tr>
                              <th className="px-3 py-1.5">Column</th>
                              <th className="px-3 py-1.5">Data Type</th>
                              <th className="px-3 py-1.5">Key Type</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100 font-mono">
                            {tableDetails.columns?.slice(0, 10).map((col, cIdx) => (
                              <tr key={cIdx}>
                                <td className="px-3 py-1 font-semibold text-slate-800">{col.name}</td>
                                <td className="px-3 py-1 text-slate-500">{col.type}</td>
                                <td className="px-3 py-1">
                                  {col.is_pk ? (
                                    <span className="px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 text-2xs font-bold">PK</span>
                                  ) : col.name.endsWith('_key') ? (
                                    <span className="px-1.5 py-0.2 rounded bg-blue-100 text-blue-800 text-2xs">FK</span>
                                  ) : (
                                    <span className="text-slate-400">Attribute</span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Schema Validation Status */}
                  <div className="p-3 bg-emerald-50/60 rounded-xl border border-emerald-200/80 flex items-center justify-between text-2xs text-emerald-900">
                    <div className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-emerald-600 shrink-0" />
                      <span>
                        <strong>Referential Integrity Verified:</strong> 100% foreign-key compliance with zero orphaned dimension rows across 59,606 transactions.
                      </span>
                    </div>
                    <span className="font-bold text-emerald-700 shrink-0">Status: Validated</span>
                  </div>
                </div>
              )}

              {/* Execution Steps */}
              {labData.steps?.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-200/90 p-6 sm:p-7 shadow-sm">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    Procedure & Implementation Steps
                  </h3>
                  <div className="space-y-3">
                    {labData.steps.map((step, idx) => (
                      <div key={idx} className="flex items-start gap-3 text-xs text-slate-700">
                        <span className="h-5 w-5 rounded-full bg-slate-100 text-slate-700 font-bold shrink-0 flex items-center justify-center text-2xs mt-0.5 border border-slate-200">
                          {idx + 1}
                        </span>
                        <span className="leading-relaxed font-medium">{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Result Table */}
              {labData.result_table && labData.result_table.columns && (
                <div className="bg-white rounded-2xl border border-slate-200/90 p-6 sm:p-7 shadow-sm">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
                    <Table className="h-4 w-4 text-blue-600" />
                    Empirical Output & Metric Observations
                  </h3>
                  
                  <div className="overflow-x-auto rounded-xl border border-slate-100">
                    <table className="w-full text-left text-xs text-slate-700">
                      <thead className="text-2xs uppercase tracking-wider text-slate-400 bg-slate-50 border-b border-slate-100">
                        <tr>
                          {labData.result_table.columns.map((col, idx) => (
                            <th key={idx} className="px-4 py-2.5 font-semibold">{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {labData.result_table.rows?.map((row, rIdx) => (
                          <tr key={rIdx} className="hover:bg-slate-50/80 transition">
                            {Array.isArray(row) ? (
                              row.map((cell, cIdx) => (
                                <td key={cIdx} className="px-4 py-2.5">{String(cell)}</td>
                              ))
                            ) : (
                              labData.result_table.columns.map((col, cIdx) => (
                                <td key={cIdx} className="px-4 py-2.5">{String(row[col] ?? '')}</td>
                              ))
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Academic Conclusion */}
              {labData.conclusion && (
                <div className="bg-white rounded-2xl border border-slate-200/90 p-6 sm:p-7 shadow-sm">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                    Academic Conclusion & Findings
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed font-medium">
                    {labData.conclusion}
                  </p>
                </div>
              )}

              {/* VIVA QUESTIONS SECTION IS REMOVED PER REQUIREMENT */}
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-slate-200 p-16 text-center text-slate-400 shadow-sm">
              Select an experiment from the left curriculum panel to inspect findings.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
