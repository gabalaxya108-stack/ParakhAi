import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, HelpCircle, Loader2 } from 'lucide-react';

export type ComplianceStatus = 
  | 'COMPLIANT' 
  | 'CONFIRMED_VIOLATION' 
  | 'NON_COMPLIANT'
  | 'POTENTIAL_VIOLATION' 
  | 'NEEDS_REVIEW' 
  | 'MANUAL_REVIEW' 
  | 'PROCESSING'
  | 'NOT_APPLICABLE' 
  | string;

interface StatusBadgeProps {
  status: ComplianceStatus;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  showIcon = true,
}) => {
  const norm = status?.toUpperCase() || 'UNKNOWN';

  let label = 'Unknown';
  let classes = 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700';
  let icon = <HelpCircle className={size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} />;

  if (norm === 'COMPLIANT' || norm === 'DETECTED' || norm === 'PASS') {
    label = 'Compliant';
    classes = 'bg-emerald-50 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800 font-semibold';
    icon = <CheckCircle2 className={`${size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} text-emerald-600 dark:text-emerald-400`} />;
  } else if (norm === 'CONFIRMED_VIOLATION' || norm === 'NON_COMPLIANT' || norm === 'VIOLATION' || norm === 'FAIL' || norm === 'POTENTIAL_VIOLATION') {
    label = 'Confirmed Violation';
    classes = 'bg-rose-50 dark:bg-rose-950/80 text-rose-800 dark:text-rose-300 border-rose-200 dark:border-rose-800 font-semibold';
    icon = <XCircle className={`${size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} text-rose-600 dark:text-rose-400`} />;
  } else if (norm === 'NEEDS_REVIEW' || norm === 'MANUAL_REVIEW' || norm === 'UNCLEAR' || norm === 'REVIEW_PENDING' || norm === 'WARNING') {
    label = 'Needs Review';
    classes = 'bg-amber-50 dark:bg-amber-950/80 text-amber-900 dark:text-amber-300 border-amber-200 dark:border-amber-800 font-semibold';
    icon = <AlertTriangle className={`${size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} text-amber-600 dark:text-amber-400`} />;
  } else if (norm === 'PROCESSING') {
    label = 'Processing...';
    classes = 'bg-blue-50 dark:bg-blue-950/80 text-blue-800 dark:text-blue-300 border-blue-200 dark:border-blue-800 font-medium';
    icon = <Loader2 className={`${size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} text-blue-600 dark:text-blue-400 animate-spin`} />;
  } else if (norm === 'NOT_APPLICABLE') {
    label = 'Not Applicable';
    classes = 'bg-slate-100 dark:bg-slate-800/80 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700';
    icon = <HelpCircle className={`${size === 'sm' ? 'w-3 h-3' : size === 'lg' ? 'w-4 h-4' : 'w-3.5 h-3.5'} text-slate-400 dark:text-slate-500`} />;
  }

  const sizeClass = size === 'sm' 
    ? 'px-2 py-0.5 text-[11px]' 
    : size === 'lg'
    ? 'px-3 py-1.5 text-sm'
    : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md border tracking-tight shadow-2xs ${classes} ${sizeClass}`}>
      {showIcon && icon}
      <span>{label}</span>
    </span>
  );
};
