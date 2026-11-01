import React from 'react';
import { NavLink } from 'react-router-dom';
import { Truck, Calculator, LayoutDashboard, Layers, GraduationCap } from 'lucide-react';

export default function Navbar() {
  const navItems = [
    { to: '/', label: 'Home', icon: Truck, end: true },
    { to: '/predict', label: 'Predict Shipping', icon: Calculator },
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/batch', label: 'Batch Prediction', icon: Layers },
    { to: '/college-labs', label: 'College Lab Mode', icon: GraduationCap },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#111827] border-b border-[#1F2937] shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <NavLink to="/" className="flex items-center gap-3 group">
            <div className="h-9 w-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-xs transition group-hover:bg-blue-500">
              <Truck className="h-5 w-5" />
            </div>
            <div className="flex items-center">
              <span className="text-base sm:text-lg font-bold tracking-tight text-white">Smart Freight</span>
              <span className="hidden sm:inline-block ml-2.5 text-2xs font-semibold text-slate-300 bg-[#1F2937] border border-slate-700/80 px-2 py-0.5 rounded-md">
                ML Analytics
              </span>
            </div>
          </NavLink>

          {/* Navigation Links */}
          <nav className="flex items-center gap-1 sm:gap-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-blue-600 text-white font-semibold shadow-xs'
                        : 'text-slate-300 hover:text-white hover:bg-slate-800/70'
                    }`
                  }
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className="hidden md:inline">{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}
