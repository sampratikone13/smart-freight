import React from 'react';

export default function MetricCard({ title, value, subtitle, icon: Icon, color = 'blue' }) {
  const colorMap = {
    blue: 'bg-blue-50 text-blue-600 border border-blue-100/80',
    amber: 'bg-amber-50 text-amber-600 border border-amber-100/80',
    emerald: 'bg-emerald-50 text-emerald-600 border border-emerald-100/80',
    rose: 'bg-rose-50 text-rose-600 border border-rose-100/80',
    indigo: 'bg-indigo-50 text-indigo-600 border border-indigo-100/80',
    slate: 'bg-slate-50 text-slate-600 border border-slate-200/60',
  };

  const iconClasses = colorMap[color] || colorMap.blue;

  return (
    <div className="bg-white rounded-2xl border border-[#E5EAF0] p-5 shadow-[0_1px_3px_0_rgba(16,24,40,0.04),0_1px_2px_0_rgba(16,24,40,0.02)] transition-all hover:border-slate-300">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-[#64748B] uppercase tracking-wider">{title}</p>
        {Icon && (
          <div className={`p-2 rounded-xl ${iconClasses}`}>
            <Icon className="h-4 w-4" />
          </div>
        )}
      </div>
      <div className="mt-3">
        <p className="text-2xl font-extrabold text-[#172033] tracking-tight">{value}</p>
        {subtitle && <p className="mt-1 text-xs text-[#64748B] font-medium leading-normal">{subtitle}</p>}
      </div>
    </div>
  );
}
