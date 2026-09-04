import React from 'react';

interface ConfidenceIndicatorProps {
  confidence: number; // 0.0 to 1.0 or 0 to 100
  showLabel?: boolean;
  size?: 'sm' | 'md';
}

export const ConfidenceIndicator: React.FC<ConfidenceIndicatorProps> = ({
  confidence,
  showLabel = true,
  size = 'md',
}) => {
  const normalized = confidence > 1 ? confidence / 100 : confidence;
  const pct = Math.round(normalized * 100);

  let category = 'High';
  let badgeColor = 'bg-emerald-50 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800';
  let barColor = 'bg-emerald-600';

  if (normalized < 0.60) {
    category = 'Needs Review';
    badgeColor = 'bg-rose-50 dark:bg-rose-950 text-rose-800 dark:text-rose-300 border-rose-200 dark:border-rose-800';
    barColor = 'bg-rose-600';
  } else if (normalized < 0.85) {
    category = 'Medium';
    badgeColor = 'bg-amber-50 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border-amber-200 dark:border-amber-800';
    barColor = 'bg-amber-600';
  }

  return (
    <div
      className="inline-flex items-center gap-2"
      title="Confidence indicates extraction reliability, not legal certainty."
    >
      <div className="w-10 h-1.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden shrink-0">
        <div
          className={`h-full rounded-full ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={`font-mono font-medium ${size === 'sm' ? 'text-[11px]' : 'text-xs'} text-slate-700 dark:text-slate-300`}>
        {pct}%
      </span>
      {showLabel && (
        <span className={`px-1.5 py-0.5 rounded border text-[10px] font-medium tracking-tight ${badgeColor}`}>
          {category}
        </span>
      )}
    </div>
  );
};
