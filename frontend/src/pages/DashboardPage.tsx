import { BACKEND_SERVER_ORIGIN } from '../api/client';
import React, { useEffect, useState } from 'react';
import {
  FileCheck2,
  AlertTriangle,
  AlertOctagon,
  ArrowRight,
  UploadCloud,
  CheckCircle2,
  RefreshCw,
  Package,
  Layers,
  ShieldCheck
} from 'lucide-react';
import { inspectionApi } from '../api/inspection';
import { DashboardMetrics } from '../types/dashboard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { MetricCard } from '../components/ui/MetricCard';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';

interface DashboardPageProps {
  onNavigate: (tab: string) => void;
  onSelectInspection: (inspectionId: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onNavigate,
  onSelectInspection,
}) => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardMetrics = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await inspectionApi.getDashboardMetrics();
      setMetrics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load dashboard records');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardMetrics();
  }, []);

  const total = metrics?.total_inspections ?? 0;
  const potentialViolations = metrics?.potential_violations_count ?? 0;
  const manualReviews = metrics?.manual_review_count ?? 0;
  const compliantCount = metrics?.compliant_count ?? 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Page Header with One Obvious Primary Action */}
      <PageHeader
        title="Inspection Overview"
        subtitle="Monitor product inspections and potential compliance issues under the Legal Metrology Rules."
        primaryAction={
          <button
            onClick={() => onNavigate('scan')}
            className="px-3.5 py-1.5 rounded bg-blue-900 hover:bg-blue-950 text-white text-xs font-semibold shadow-xs transition flex items-center gap-1.5 cursor-pointer"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Scan a Product</span>
          </button>
        }
        secondaryAction={
          <button
            onClick={() => onNavigate('batch')}
            className="px-3 py-1.5 rounded border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-medium transition flex items-center gap-1.5 cursor-pointer"
          >
            <Layers className="w-3.5 h-3.5 text-slate-500 dark:text-slate-400" />
            <span>Batch Scan</span>
          </button>
        }
      />

      {/* Error alert if any */}
      {error && (
        <div className="p-3.5 rounded border border-rose-200 dark:border-rose-900 bg-rose-50 dark:bg-rose-950/40 text-xs text-rose-800 dark:text-rose-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertOctagon className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={fetchDashboardMetrics}
            className="text-xs font-semibold text-rose-700 hover:underline cursor-pointer"
          >
            Retry
          </button>
        </div>
      )}

      {/* Top Compact Summary Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        <MetricCard
          label="Total Inspections"
          value={loading ? '—' : total}
          icon={<FileCheck2 className="w-4 h-4" />}
          hint="All verified label scans"
          onClick={() => onNavigate('history')}
        />
        <MetricCard
          label="Potential Issues"
          value={loading ? '—' : potentialViolations}
          icon={<AlertOctagon className="w-4 h-4" />}
          variant="danger"
          hint="Mandatory declaration issues"
          onClick={() => onNavigate('history')}
        />
        <MetricCard
          label="Needs Review"
          value={loading ? '—' : manualReviews}
          icon={<AlertTriangle className="w-4 h-4" />}
          variant="warning"
          hint="Low confidence or micro-print"
          onClick={() => onNavigate('history')}
        />
        <MetricCard
          label="Products Checked"
          value={loading ? '—' : (compliantCount || total)}
          icon={<ShieldCheck className="w-4 h-4" />}
          variant="success"
          hint="Verified compliant commodities"
          onClick={() => onNavigate('history')}
        />
      </div>

      {/* Recent Inspections Table Card */}
      <Card padding="none" className="overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/40">
          <div>
            <h2 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">Recent Inspections</h2>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 dark:text-slate-500">Chronological record of recent product inspections.</p>
          </div>
          <button
            onClick={() => onNavigate('history')}
            className="text-xs font-medium text-blue-900 dark:text-blue-400 hover:underline flex items-center gap-1 transition cursor-pointer"
          >
            <span>View all inspections</span>
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        {loading ? (
          <div className="py-12 text-center space-y-2">
            <div className="w-6 h-6 border-2 border-blue-900 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-xs text-slate-500 font-medium">Loading inspections...</p>
          </div>
        ) : metrics && metrics.recent_inspections && metrics.recent_inspections.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-medium">
                  <th className="py-2.5 px-4">Product</th>
                  <th className="py-2.5 px-3">Manufacturer</th>
                  <th className="py-2.5 px-3">Result</th>
                  <th className="py-2.5 px-3">Risk</th>
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {metrics.recent_inspections.map((insp: any) => {
                  const summary = (insp.compliance_summary || {}) as any;
                  const status = summary.overall_status || 'NOT_EVALUATED';
                  const risk = summary.risk_score || 0;
                  const productName = summary.product_name || insp.filename;
                  const manufacturer = summary.manufacturer || insp.product?.manufacturer || '—';

                  return (
                    <tr
                      key={insp.inspection_id}
                      onClick={() => onSelectInspection(insp.inspection_id)}
                      className="hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition"
                    >
                      <td className="py-2.5 px-4 font-medium text-slate-900 dark:text-white">
                        <div className="flex items-center gap-2.5">
                          <img
                            src={insp.image_url ? (insp.image_url.startsWith('http') ? insp.image_url : `${BACKEND_SERVER_ORIGIN}${insp.image_url.startsWith('/') ? '' : '/'}${insp.image_url}`) : ''}
                            alt={insp.filename}
                            className="w-7 h-7 rounded border border-slate-200 dark:border-slate-700 object-cover bg-slate-100 dark:bg-slate-800 shrink-0"
                            onError={(e) => {
                              (e.target as HTMLElement).style.display = 'none';
                            }}
                          />
                          <div className="truncate max-w-[220px]">
                            <span className="block font-semibold text-slate-900 dark:text-white truncate">
                              {productName}
                            </span>
                            <span className="text-[10px] text-slate-400 font-mono block truncate">
                              {insp.inspection_id}
                            </span>
                          </div>
                        </div>
                      </td>

                      <td className="py-2.5 px-3 text-slate-600 dark:text-slate-400 truncate max-w-[180px]">
                        {manufacturer}
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

                      <td className="py-2.5 px-3 text-slate-500 dark:text-slate-400 font-mono text-[11px]">
                        {insp.created_at ? new Date(insp.created_at).toLocaleDateString() : '—'}
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
            icon={Package}
            title="No inspections yet"
            description="Scan your first packaged commodity to begin automated compliance screening."
            actionLabel="Scan a product"
            onAction={() => onNavigate('scan')}
          />
        )}
      </Card>
    </div>
  );
};
