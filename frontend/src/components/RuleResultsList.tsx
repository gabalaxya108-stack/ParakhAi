import React, { useState } from 'react';
import { RuleEvaluationResult, ComplianceStatus } from '../types';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  Scale,
  Crosshair,
  UserCheck,
  ChevronRight
} from 'lucide-react';

interface RuleResultsListProps {
  results: RuleEvaluationResult[];
  onSelectEvidenceBox: (box: any) => void;
  onSubmitOverride: (ruleId: string, overrideVerdict: ComplianceStatus, reason: string) => Promise<void>;
}

export const RuleResultsList: React.FC<RuleResultsListProps> = ({
  results,
  onSelectEvidenceBox,
  onSubmitOverride
}) => {
  const [overrideModalRule, setOverrideModalRule] = useState<RuleEvaluationResult | null>(null);
  const [overrideVerdict, setOverrideVerdict] = useState<ComplianceStatus>('PASS');
  const [overrideReason, setOverrideReason] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleSaveOverride = async () => {
    if (!overrideModalRule || !overrideReason.trim()) {
      alert('Please provide a mandatory justification reason for the inspector override.');
      return;
    }
    try {
      setIsSubmitting(true);
      await onSubmitOverride(overrideModalRule.rule_id, overrideVerdict, overrideReason);
      setOverrideModalRule(null);
      setOverrideReason('');
    } catch (err) {
      alert('Failed to save override: ' + err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-3 p-1">
      <div className="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-800">
        <span>Deterministic Rule Engine Scorecard ({results.length} rules)</span>
        <span>Version: PCR 2011 / 2023.1</span>
      </div>

      <div className="space-y-3">
        {results.map(rule => {
          const effStatus = rule.override_verdict || rule.status;
          const isPass = effStatus === 'PASS';
          const isFail = effStatus === 'FAIL';
          const isWarning = effStatus === 'WARNING';

          let borderClass = 'border-slate-800/80 bg-slate-900/50';
          let statusBadge = (
            <span className="flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">
              <HelpCircle className="w-3.5 h-3.5" /> Manual Check
            </span>
          );

          if (isPass) {
            borderClass = 'border-emerald-500/30 bg-emerald-950/20';
            statusBadge = (
              <span className="flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/400/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-3.5 h-3.5" /> Compliant
              </span>
            );
          } else if (isFail) {
            borderClass = 'border-rose-500/50 bg-rose-950/25 ring-1 ring-rose-500/20';
            statusBadge = (
              <span className="flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-rose-50 dark:bg-rose-950/400/20 text-rose-400 border border-rose-500/30 animate-pulse">
                <XCircle className="w-3.5 h-3.5" /> Violation
              </span>
            );
          } else if (isWarning) {
            borderClass = 'border-amber-500/40 bg-amber-950/20';
            statusBadge = (
              <span className="flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/400/10 text-amber-400 border border-amber-500/20">
                <AlertTriangle className="w-3.5 h-3.5" /> Warning
              </span>
            );
          }

          return (
            <div key={rule.rule_id} className={`p-4 rounded-xl border transition-all ${borderClass}`}>
              {/* Top Header */}
              <div className="flex items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-800 text-blue-400 border border-slate-700">
                    {rule.rule_id}
                  </span>
                  <span className="text-xs font-medium text-slate-400 truncate max-w-[260px]">
                    {rule.legal_reference}
                  </span>
                </div>
                {statusBadge}
              </div>

              {/* Title */}
              <h4 className="font-semibold text-sm text-slate-100 mb-1.5">{rule.rule_title}</h4>

              {/* Violation reason or finding */}
              {isFail && rule.violation_reason && (
                <div className="bg-rose-950/40 border border-rose-500/30 p-2.5 rounded-lg mb-2 text-xs text-rose-300 font-medium">
                  <strong>Non-Compliance Finding:</strong> {rule.violation_reason}
                </div>
              )}

              {isWarning && rule.violation_reason && (
                <div className="bg-amber-950/40 border border-amber-500/30 p-2.5 rounded-lg mb-2 text-xs text-amber-300">
                  <strong>Notice:</strong> {rule.violation_reason}
                </div>
              )}

              {/* Legal citation & recommended action */}
              <p className="text-[11px] text-slate-400 leading-relaxed mb-3">
                <Scale className="w-3 h-3 inline mr-1 text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500" />
                {rule.legal_citation}
              </p>

              {/* Evidence and Inspector Override footer */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-xs">
                {rule.evidence_boxes && rule.evidence_boxes.length > 0 ? (
                  <button
                    onClick={() => onSelectEvidenceBox(rule.evidence_boxes[0])}
                    className="flex items-center gap-1.5 text-blue-400 hover:text-blue-300 font-medium transition"
                  >
                    <Crosshair className="w-3.5 h-3.5" />
                    Locate Evidence on Label
                  </button>
                ) : (
                  <span className="text-[11px] text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">No spatial region required</span>
                )}

                <button
                  onClick={() => {
                    setOverrideModalRule(rule);
                    setOverrideVerdict(rule.status === 'FAIL' ? 'PASS' : 'FAIL');
                  }}
                  className="flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
                >
                  <UserCheck className="w-3.5 h-3.5 text-indigo-400" />
                  Override Verdict
                </button>
              </div>

              {/* Override Banner if overridden */}
              {rule.inspector_override && (
                <div className="mt-2.5 p-2 rounded-lg bg-indigo-950/40 border border-indigo-500/30 text-[11px] text-indigo-300">
                  <strong>Inspector Override ({rule.override_verdict}):</strong> {rule.override_reason}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Override Modal Dialog */}
      {overrideModalRule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-bold text-slate-100 flex items-center gap-2 text-base">
                <UserCheck className="w-4 h-4 text-indigo-400" />
                Inspector Compliance Override
              </h3>
              <span className="text-xs px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/400/20 text-indigo-300 border border-indigo-500/30 font-mono">
                {overrideModalRule.rule_id}
              </span>
            </div>

            <p className="text-xs text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">
              You are manually adjusting the statutory verdict for <strong>"{overrideModalRule.rule_title}"</strong>.
              All overrides are cryptographically logged in the official audit trail.
            </p>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">New Inspector Verdict:</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setOverrideVerdict('PASS')}
                  className={`p-2.5 rounded-xl border text-xs font-bold transition-all ${
                    overrideVerdict === 'PASS'
                      ? 'bg-emerald-600 text-white border-emerald-500 shadow-md'
                      : 'bg-slate-950 text-slate-400 border-slate-800 hover:bg-slate-800'
                  }`}
                >
                  Mark as COMPLIANT (PASS)
                </button>
                <button
                  type="button"
                  onClick={() => setOverrideVerdict('FAIL')}
                  className={`p-2.5 rounded-xl border text-xs font-bold transition-all ${
                    overrideVerdict === 'FAIL'
                      ? 'bg-rose-600 text-white border-rose-500 shadow-md'
                      : 'bg-slate-950 text-slate-400 border-slate-800 hover:bg-slate-800'
                  }`}
                >
                  Mark as VIOLATION (FAIL)
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Mandatory Inspector Justification & Evidence Reference:
              </label>
              <textarea
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                placeholder="e.g. Physical package label verified under 10x gauge; meets Schedule II table tolerances under Rule 24 exemption."
                rows={3}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-slate-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setOverrideModalRule(null)}
                className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-200"
              >
                Cancel
              </button>
              <button
                disabled={isSubmitting || !overrideReason.trim()}
                onClick={handleSaveOverride}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-50 dark:bg-indigo-950/400 text-white shadow-lg shadow-indigo-500/20 disabled:opacity-50"
              >
                {isSubmitting ? 'Recording...' : 'Commit Override to Audit'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
