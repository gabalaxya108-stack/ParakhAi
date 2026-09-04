import React, { useState } from 'react';
import { Download, CheckCircle2, FileWarning, ShieldAlert, Send } from 'lucide-react';
import { ComplianceStatus } from '../types';
import { api } from '../services/api';

interface InspectorActionDockProps {
  inspectionId: string;
  inspectionNumber: string;
  overallCompliance: ComplianceStatus;
  onFinalizeReview: (verdict: ComplianceStatus, notes: string) => Promise<void>;
}

export const InspectorActionDock: React.FC<InspectorActionDockProps> = ({
  inspectionId,
  inspectionNumber,
  overallCompliance,
  onFinalizeReview
}) => {
  const [notes, setNotes] = useState<string>('Verified against packaging physical declarations under Legal Metrology Act, 2009.');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const handleAction = async (verdict: ComplianceStatus) => {
    try {
      setIsSubmitting(true);
      await onFinalizeReview(verdict, notes);
      alert(`Inspection review finalized with status: ${verdict}`);
    } catch (err) {
      alert('Failed to finalize review: ' + err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const pdfUrl = api.getReportPdfUrl(inspectionId);

  return (
    <div className="bg-slate-900 border-t border-slate-800 p-4 shadow-2xl">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Officer Notes input */}
        <div className="w-full md:w-1/2 flex items-center gap-2">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Official Inspector Remarks / Remedial Directions..."
            rows={2}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:focus:ring-blue-400"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 w-full md:w-auto justify-end">
          {/* Download PDF button */}
          <a
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 transition-all shadow-md"
          >
            <Download className="w-4 h-4 text-blue-400" />
            Download PDF Report
          </a>

          {/* Issue Notice / Confirm Violations */}
          <button
            disabled={isSubmitting}
            onClick={() => handleAction('FAIL')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-50 dark:bg-rose-950/400 text-white font-semibold text-xs transition-all shadow-lg shadow-rose-500/20 disabled:opacity-50"
          >
            <FileWarning className="w-4 h-4" />
            Issue Statutory Notice
          </button>

          {/* Approve / Mark Compliant */}
          <button
            disabled={isSubmitting}
            onClick={() => handleAction('PASS')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-50 dark:bg-emerald-950/400 text-white font-semibold text-xs transition-all shadow-lg shadow-emerald-500/20 disabled:opacity-50"
          >
            <CheckCircle2 className="w-4 h-4" />
            Certify Compliant
          </button>
        </div>
      </div>
    </div>
  );
};
