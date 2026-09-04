import React, { useState } from 'react';
import { ShieldCheck, CheckCircle2, XCircle, HelpCircle, X } from 'lucide-react';

export type InspectorDecisionType = 'COMPLIANT' | 'NON_COMPLIANT' | 'INSUFFICIENT_EVIDENCE';

interface InspectorDecisionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (decision: InspectorDecisionType, reason: string, remarks?: string) => Promise<void>;
  canonicalTitle: string;
  statutoryRule: string;
  currentStatus: string;
  detectedValue?: string | null;
  inspectorId?: string;
}

const PRESET_REASONS = [
  "Declaration clearly visible and compliant on physical package (OCR missed)",
  "Mandatory declaration confirmed absent after physical package examination",
  "Statutory tax-inclusive wording verified on label",
  "Non-standard metric unit confirmed on physical sample",
  "Image resolution/angle insufficient to determine declaration presence",
  "Other statutory finding (specified in remarks)"
];

export const InspectorDecisionModal: React.FC<InspectorDecisionModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  canonicalTitle,
  statutoryRule,
  currentStatus,
  detectedValue,
  inspectorId = 'INS-DL-4029'
}) => {
  const [decision, setDecision] = useState<InspectorDecisionType>(
    currentStatus === 'NON_COMPLIANT' || currentStatus === 'CONFIRMED_VIOLATION' 
      ? 'NON_COMPLIANT' 
      : 'COMPLIANT'
  );
  const [reason, setReason] = useState<string>(PRESET_REASONS[0]);
  const [customReason, setCustomReason] = useState<string>('');
  const [remarks, setRemarks] = useState<string>('');
  const [attested, setAttested] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    const finalReason = reason === "Other statutory finding (specified in remarks)"
      ? customReason.trim() || reason
      : reason;

    if (!attested) {
      alert("Please confirm the statutory attestation checkbox before submitting.");
      return;
    }

    try {
      setSubmitting(true);
      await onConfirm(decision, finalReason, remarks.trim() || undefined);
      onClose();
    } catch (err: any) {
      alert("Failed to record decision: " + (err.message || err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 max-w-lg w-full p-6 shadow-2xl space-y-4 animate-in">
        
        {/* Header */}
        <div className="flex items-start justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300 rounded-xl">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">Human-in-the-Loop Review</h3>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Official Inspector Override • Legal Metrology (Packaged Commodities) Rules, 2011
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-slate-700 dark:hover:text-white rounded-lg cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Audit Context Box */}
        <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700 text-xs space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-900 dark:text-slate-100">{canonicalTitle}</span>
            <span className="font-mono text-[10px] text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50 px-2 py-0.5 rounded border border-blue-200 dark:border-blue-800">
              {statutoryRule}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-2 pt-1 text-[11px] text-slate-500 border-t border-slate-200 dark:border-slate-700/60">
            <div>Inspector: <strong className="text-slate-700 dark:text-slate-300 font-mono">{inspectorId}</strong></div>
            <div>Previous AI Status: <strong className="text-amber-600 dark:text-amber-400 font-mono">{currentStatus}</strong></div>
          </div>
          {detectedValue && (
            <div className="text-[11px] text-slate-600 dark:text-slate-300 truncate pt-0.5">
              Detected by AI: <span className="font-mono text-slate-900 dark:text-slate-100 font-medium">"{detectedValue}"</span>
            </div>
          )}
        </div>

        {/* 3-Option Decision Radio Selection */}
        <div className="space-y-1.5 text-xs">
          <label className="font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider text-[10px]">
            Inspector Determination:
          </label>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => setDecision('COMPLIANT')}
              className={`p-2.5 rounded-xl border flex flex-col items-center justify-center gap-1.5 font-bold text-xs transition cursor-pointer ${
                decision === 'COMPLIANT'
                  ? 'bg-emerald-50 border-emerald-500 text-emerald-800 dark:bg-emerald-950/40 dark:border-emerald-500 dark:text-emerald-300 ring-2 ring-emerald-500/20'
                  : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50'
              }`}
            >
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Confirm Compliant</span>
            </button>

            <button
              type="button"
              onClick={() => setDecision('NON_COMPLIANT')}
              className={`p-2.5 rounded-xl border flex flex-col items-center justify-center gap-1.5 font-bold text-xs transition cursor-pointer ${
                decision === 'NON_COMPLIANT'
                  ? 'bg-rose-50 border-rose-500 text-rose-800 dark:bg-rose-950/40 dark:border-rose-500 dark:text-rose-300 ring-2 ring-rose-500/20'
                  : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50'
              }`}
            >
              <XCircle className="w-4 h-4 text-rose-600" />
              <span>Confirm Violation</span>
            </button>

            <button
              type="button"
              onClick={() => setDecision('INSUFFICIENT_EVIDENCE')}
              className={`p-2.5 rounded-xl border flex flex-col items-center justify-center gap-1.5 font-bold text-xs transition cursor-pointer ${
                decision === 'INSUFFICIENT_EVIDENCE'
                  ? 'bg-amber-50 border-amber-500 text-amber-800 dark:bg-amber-950/40 dark:border-amber-500 dark:text-amber-300 ring-2 ring-amber-500/20'
                  : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50'
              }`}
            >
              <HelpCircle className="w-4 h-4 text-amber-600" />
              <span>Insufficient Evidence</span>
            </button>
          </div>
        </div>

        {/* Reason Dropdown */}
        <div className="space-y-1.5 text-xs">
          <label className="font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider text-[10px] flex items-center justify-between">
            <span>Statutory Justification Reason: <span className="text-rose-500">*</span></span>
          </label>
          <select
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {PRESET_REASONS.map((r, i) => (
              <option key={i} value={r}>{r}</option>
            ))}
          </select>

          {reason === "Other statutory finding (specified in remarks)" && (
            <input
              type="text"
              value={customReason}
              onChange={(e) => setCustomReason(e.target.value)}
              placeholder="Specify custom statutory reason..."
              className="w-full mt-1.5 px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          )}
        </div>

        {/* Supporting Remarks */}
        <div className="space-y-1.5 text-xs">
          <label className="font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider text-[10px]">
            Supporting Remarks & Evidence Notes:
          </label>
          <textarea
            value={remarks}
            onChange={(e) => setRemarks(e.target.value)}
            rows={2}
            placeholder="e.g. Verified on physical package rear panel; text clearly readable under ambient inspection."
            className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Mandatory Statutory Attestation Checkbox */}
        <div className="p-3 bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40 rounded-xl flex items-start gap-2.5">
          <input
            id="attest-checkbox"
            type="checkbox"
            checked={attested}
            onChange={(e) => setAttested(e.target.checked)}
            className="mt-0.5 rounded border-amber-400 text-blue-600 focus:ring-blue-500 cursor-pointer"
          />
          <label htmlFor="attest-checkbox" className="text-[11px] text-amber-900 dark:text-amber-200 leading-snug cursor-pointer select-none">
            I have reviewed the physical package evidence and am recording this as an official inspector decision under the Legal Metrology (Packaged Commodities) Rules, 2011.
          </label>
        </div>

        {/* Footer Actions */}
        <div className="pt-2 flex items-center justify-end gap-2 border-t border-slate-200 dark:border-slate-800">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white rounded-xl transition cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!attested || submitting}
            className="px-5 py-2 text-xs font-bold bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl shadow transition cursor-pointer"
          >
            {submitting ? 'Recording Decision...' : 'Confirm Decision'}
          </button>
        </div>

      </div>
    </div>
  );
};
