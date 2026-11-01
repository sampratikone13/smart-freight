import React from 'react';

export default function PageHeader({ title, description, children }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8 pb-5 border-b border-[#E5EAF0]">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#172033]">{title}</h1>
        {description && <p className="mt-1.5 text-xs sm:text-sm text-[#64748B] max-w-2xl leading-relaxed">{description}</p>}
      </div>
      {children && <div className="flex items-center gap-3 shrink-0">{children}</div>}
    </div>
  );
}
