import { BACKEND_SERVER_ORIGIN } from '../api/client';
import React, { useEffect, useState } from 'react';
import {
  Search,
  Filter,
  RefreshCw,
  ArrowRight,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  Calendar,
  Building,
  Package,
  Layers,
  FileCheck2
} from 'lucide-react';
import { inspectionApi } from '../api/inspection';
import { StatusBadge } from '../components/ui/StatusBadge';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';

interface InspectionHistoryPageProps {
  onSelectInspection: (inspectionId: string) => void;
  onScanNew: () => void;
}

export const InspectionHistoryPage: React.FC<InspectionHistoryPageProps> = ({
  onSelectInspection,
  onScanNew,
}) => {
  const [inspections, setInspections] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Search and Filter State
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const fetchInspections = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await inspectionApi.listInspections();
      setInspections(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to query inspection records');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInspections();
  }, []);

  const filteredInspections = inspections.filter((insp) => {
    const status = (insp.overall_status || insp.compliance_summary?.overall_status || 'NOT_EVALUATED').toUpperCase();
    const productName = (insp.product?.name || insp.compliance_summary?.product_name || insp.filename || '').toLowerCase();
    const manufacturer = (insp.product?.manufacturer || insp.compliance_summary?.manufacturer || '').toLowerCase();
    const id = (insp.inspection_id || '').toLowerCase();
    const q = searchQuery.toLowerCase().trim();

    const matchesSearch = !q || id.includes(q) || productName.includes(q) || manufacturer.includes(q);

    const isCleared = status === "COMPLIANT" || insp.review_status === "APPROVED" || insp.review_status === "HUMAN_VERIFIED";
    const isNeedsReview = (status === "MANUAL_REVIEW" || status === "NEEDS_REVIEW") && !isCleared;
    const isComplaint = status === "POTENTIAL_VIOLATION" || status === "NON_COMPLIANT" || status === "VIOLATION";

    if (statusFilter === "ALL") return matchesSearch;
    if (statusFilter === "CLEARED") return matchesSearch && isCleared;
    if (statusFilter === "REVIEW") return matchesSearch && isNeedsReview;
    if (statusFilter === "COMPLAINT") return matchesSearch && isComplaint;

    return matchesSearch;
  });

  const clearedCount = inspections.filter(i => {
    const s = (i.overall_status || i.compliance_summary?.overall_status || "").toUpperCase();
    return s === "COMPLIANT" || i.review_status === "APPROVED" || i.review_status === "HUMAN_VERIFIED";
  }).length;

  const reviewCount = inspections.filter(i => {
    const s = (i.overall_status || i.compliance_summary?.overall_status || "").toUpperCase();
    const cl = s === "COMPLIANT" || i.review_status === "APPROVED" || i.review_status === "HUMAN_VERIFIED";
    return (s === "MANUAL_REVIEW" || s === "NEEDS_REVIEW") && !cl;
  }).length;

  const complaintCount = inspections.filter(i => {
    const s = (i.overall_status || i.compliance_summary?.overall_status || "").toUpperCase();
    return s === "POTENTIAL_VIOLATION" || s === "NON_COMPLIANT" || s === "VIOLATION";
  }).length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-5">
      {/* Header */}
      <PageHeader
        title="Inspections"
        subtitle="Searchable regulatory register of packaged commodity label compliance screenings."
        primaryAction={
          <button
            onClick={onScanNew}
            className="px-3.5 py-1.5 rounded bg-blue-900 hover:bg-blue-950 text-white text-xs font-semibold shadow-xs transition flex items-center gap-1.5 cursor-pointer"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Scan Product</span>
          </button>
        }
        secondaryAction={
          <button
            onClick={fetchInspections}
            disabled={loading}
            className="px-3 py-1.5 rounded border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium transition flex items-center gap-1.5 cursor-pointer"
            title="Refresh list"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-900' : ''}`} />
            <span>Refresh</span>
          </button>
        }
      />

      {error && (
        <div className="p-3.5 rounded border border-rose-200 bg-rose-50 text-xs text-rose-800 flex items-center gap-2.5">
          <AlertOctagon className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2.5 bg-white p-2.5 rounded-lg border border-slate-200 shadow-xs">
        <div className="relative w-full sm:w-80">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by ID, product, or manufacturer..."
            className="w-full pl-8 pr-3 py-1 rounded border border-slate-200 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-900 transition"
          />
        </div>

        {/* Operational Stacks Tabs (Cleared / Needs Review / Complaints) */}
        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto text-xs">
          <button
            onClick={() => setStatusFilter('ALL')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              statusFilter === 'ALL'
                ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 shadow-xs'
                : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800'
            }`}
          >
            <span>All Register</span>
            <span className="px-1.5 py-0.2 rounded-full bg-slate-200 dark:bg-slate-700 text-[10px] font-mono">
              {inspections.length}
            </span>
          </button>

          <button
            onClick={() => setStatusFilter('CLEARED')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              statusFilter === 'CLEARED'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'text-emerald-700 hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800'
            }`}
            title="Compliant packages and inspector-certified clearances"
          >
            <span>Cleared Stack</span>
            <span className="px-1.5 py-0.2 rounded-full bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-300 text-[10px] font-mono font-bold">
              {clearedCount}
            </span>
          </button>

          <button
            onClick={() => setStatusFilter('REVIEW')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              statusFilter === 'REVIEW'
                ? 'bg-amber-600 text-white shadow-xs'
                : 'text-amber-700 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-950/40 border border-amber-200 dark:border-amber-800'
            }`}
            title="Packages with low OCR confidence or occlusions awaiting human review"
          >
            <span>Needs Review</span>
            <span className="px-1.5 py-0.2 rounded-full bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-300 text-[10px] font-mono font-bold">
              {reviewCount}
            </span>
          </button>

          <button
            onClick={() => setStatusFilter('COMPLAINT')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              statusFilter === 'COMPLAINT'
                ? 'bg-rose-600 text-white shadow-xs'
                : 'text-rose-700 hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40 border border-rose-200 dark:border-rose-800'
            }`}
            title="Confirmed non-compliant packages ready for statutory notices / prosecution"
          >
            <span>Complaint Stack</span>
            <span className="px-1.5 py-0.2 rounded-full bg-rose-100 dark:bg-rose-900/60 text-rose-800 dark:text-rose-300 text-[10px] font-mono font-bold">
              {complaintCount}
            </span>
          </button>
        </div>
      </div>

      {/* Table Card */}
      <Card padding="none" className="overflow-hidden">
        {loading ? (
          <div className="py-12 text-center space-y-2">
            <div className="w-6 h-6 border-2 border-blue-900 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-xs text-slate-500 font-medium">Loading inspections...</p>
          </div>
        ) : filteredInspections.length > 0 ? (
          <div className="overflow-x-auto max-h-[560px]">
            <table className="w-full text-left text-xs">
              <thead className="sticky top-0 bg-slate-50 border-b border-slate-200 z-10">
                <tr className="text-slate-600 font-semibold">
                  <th className="py-2.5 px-4">Inspection ID</th>
                  <th className="py-2.5 px-3">Product</th>
                  <th className="py-2.5 px-3">Manufacturer</th>
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Risk</th>
                  <th className="py-2.5 px-3">Reviewer</th>
                  <th className="py-2.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredInspections.map((insp) => {
                  const summary = (insp.compliance_summary || {}) as any;
                  const status = summary.overall_status || insp.overall_status || 'NOT_EVALUATED';
                  const risk = summary.risk_score || 0;
                  const productName = summary.product_name || insp.product?.name || insp.filename;
                  const manufacturer = summary.manufacturer || insp.product?.manufacturer || '—';

                  return (
                    <tr
                      key={insp.inspection_id}
                      onClick={() => onSelectInspection(insp.inspection_id)}
                      className="hover:bg-slate-50 cursor-pointer transition"
                    >
                      <td className="py-2.5 px-4 font-mono text-slate-800 text-[11px] font-semibold">
                        {insp.inspection_id}
                      </td>

                      <td className="py-2.5 px-3 font-medium text-slate-900 dark:text-white">
                        <div className="flex items-center gap-2">
                          <img
                            src={insp.image_url ? (insp.image_url.startsWith('http') ? insp.image_url : `${BACKEND_SERVER_ORIGIN}${insp.image_url.startsWith('/') ? '' : '/'}${insp.image_url}`) : ''}
                            alt={insp.filename}
                            className="w-6 h-6 rounded border border-slate-200 object-cover bg-slate-100 shrink-0"
                            onError={(e) => {
                              (e.target as HTMLElement).style.display = 'none';
                            }}
                          />
                          <span className="truncate max-w-[180px] block">
                            {productName}
                          </span>
                        </div>
                      </td>

                      <td className="py-2.5 px-3 text-slate-600 truncate max-w-[150px]">
                        {manufacturer}
                      </td>

                      <td className="py-2.5 px-3 text-slate-500 font-mono text-[11px]">
                        {insp.created_at ? new Date(insp.created_at).toLocaleDateString() : '—'}
                      </td>

                      <td className="py-2.5 px-3">
                        <StatusBadge status={status} size="sm" />
                      </td>

                      <td className="py-2.5 px-3">
                        <span className={`font-mono text-xs font-semibold ${
                          risk === 0
                            ? 'text-emerald-700 dark:text-emerald-400'
                            : risk < 40
                            ? 'text-amber-700 dark:text-amber-400'
                            : 'text-rose-700 dark:text-rose-400'
                        }`}>
                          {risk} <span className="text-[10px] text-slate-400 font-normal">/ 100</span>
                        </span>
                      </td>

                      <td className="py-2.5 px-3 text-slate-600 text-[11px]">
                        INS-DL-4029
                      </td>

                      <td className="py-2.5 px-4 text-right">
                        <span className="text-xs font-semibold text-blue-900 hover:underline inline-flex items-center gap-1">
                          <span>Inspect</span>
                          <ArrowRight className="w-3 h-3" />
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon={Search}
            title="No matching inspections found"
            description="Try modifying your search keywords or clearing active status filters."
            actionLabel="Scan Product"
            onAction={onScanNew}
          />
        )}
      </Card>
    </div>
  );
};
