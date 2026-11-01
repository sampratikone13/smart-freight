import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import PredictPage from './pages/PredictPage';
import DashboardPage from './pages/DashboardPage';
import BatchPredictPage from './pages/BatchPredictPage';
import CollegeLabPage from './pages/CollegeLabPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#F6F8FB] flex flex-col text-[#172033]">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/predict" element={<PredictPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/batch" element={<BatchPredictPage />} />
            <Route path="/college-labs" element={<CollegeLabPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        
        {/* Footer */}
        <footer className="border-t border-[#E5EAF0] bg-white py-6 mt-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#64748B]">
            <p>Smart Freight &copy; 2026. Production Shipping Duration Analytics Platform.</p>
            <p className="flex items-center gap-4">
              <span>Random Forest ML Pipeline</span>
              <span>&bull;</span>
              <span>Pre-Shipment Parameters</span>
              <span>&bull;</span>
              <span>College DWM Curriculum</span>
            </p>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}
