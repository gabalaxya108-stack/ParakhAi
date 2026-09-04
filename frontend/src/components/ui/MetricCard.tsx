import React from 'react';

interface MetricCardProps {
  label: string;
  value: number | string;
  icon: React.ReactNode;
  variant?: 'default' | 'warning' | 'danger' | 'success';
  hint?: string;
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  icon,
  variant = 'default',
  hint,
  onClick,
}) => {
  const borderVariants = {
    default: 'border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700',
    warning: 'border-amber-200 dark:border-amber-900 bg-amber-50/20 dark:bg-amber-950/20 hover:border-amber-300 dark:hover:border-amber-800',
    danger: 'border-rose-200 dark:border-rose-900 bg-rose-50/20 dark:bg-rose-950/20 hover:border-rose-300 dark:hover:border-rose-800',
    success: 'border-emerald-200 dark:border-emerald-900 bg-emerald-50/20 dark:bg-emerald-950/20 hover:border-emerald-300 dark:hover:border-emerald-800',
  };

  const iconVariants = {
    default: 'text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 border-slate-200 dark:border-slate-700',
    warning: 'text-amber-800 dark:text-amber-300 bg-amber-50 dark:bg-amber-950 border-amber-200 dark:border-amber-800',
    danger: 'text-rose-800 dark:text-rose-300 bg-rose-50 dark:bg-rose-950 border-rose-200 dark:border-rose-800',
    success: 'text-emerald-800 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950 border-emerald-200 dark:border-emerald-800',
  };

  return (
    <div
      onClick={onClick}
      className={`p-3.5 rounded-lg border bg-white dark:bg-slate-900 shadow-xs transition ${borderVariants[variant]} ${
        onClick ? 'cursor-pointer hover:shadow-sm' : ''
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-slate-600 dark:text-slate-400 tracking-tight">
          {label}
        </span>
        <div className={`w-7 h-7 rounded border flex items-center justify-center shrink-0 ${iconVariants[variant]}`}>
          {icon}
        </div>
      </div>

      <div className="mt-1.5 flex items-baseline gap-2">
        <span className="text-xl font-bold tracking-tight text-slate-900 dark:text-white font-mono">
          {value}
        </span>
      </div>

      {hint && (
        <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 truncate">
          {hint}
        </p>
      )}
    </div>
  );
};
