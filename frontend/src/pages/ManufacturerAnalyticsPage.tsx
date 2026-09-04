import React, { useEffect, useState } from 'react';
import {
  Building2,
  AlertTriangle,
  FileCheck2,
  Layers,
  Search,
  RefreshCw,
  ArrowRight,
  Filter,
  CheckCircle2,
  AlertOctagon,
  Scale
} from 'lucide-react';
import { analyticsApi } from '../api/analytics';
import { ManufacturerAnalyticsItem } from '../types/analytics';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';
import { EmptyState } from '../components/ui/EmptyState';

interface ManufacturerAnalyticsPageProps {
  onNavigateToHistoryWithFilter?: (manufacturerName: string) => void;
}

export const ManufacturerAnalyticsPage: React.FC<ManufacturerAnalyticsPageProps> = ({
  onNavigateToHistoryWithFilter,
}) => {
  const [manufacturers, setManufacturers] = useState<ManufacturerAnalyticsItem[]>([]);
  const [totalInspections, setTotalInspections] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await analyticsApi.getManufacturerAnalytics({
        manufacturer: searchQuery.trim() || undefined,
      });
      setManufacturers(data.manufacturers);
      setTotalInspections(data.total_inspections);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to aggregate manufacturer surveillance analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchAnalytics();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-5">
      {/* Header */}
      <PageHeader
        title="Manufacturer Surveillance & Analytics"
        subtitle="Surveillance patterns and repeated declaration issues across packaged commodity brands."
        secondaryAction={
          <button
            onClick={fetchAnalytics}
            disabled={loading}
            className="px-3 py-1.5 rounded border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-medium transition flex items-center gap-1.5 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-900' : ''}`} />
            <span>Refresh data</span>
          </button>
        }
      />

      {error && (
        <div className="p-3.5 rounded border border-rose-200 bg-rose-50 text-xs text-rose-800 flex items-center gap-2.5">
          <AlertOctagon className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Search Bar */}
      <Card padding="sm">
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2.5">
          <div className="relative flex-1">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search manufacturer or brand name (e.g. Nestlé, Britannia, Parle)..."
              className="w-full pl-8 pr-3 py-1.5 rounded border border-slate-200 dark:border-slate-800 text-xs text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:border-blue-900 transition"
            />
          </div>
          <button
            type="submit"
            className="px-3.5 py-1.5 rounded bg-blue-900 hover:bg-blue-950 text-white text-xs font-semibold shadow-xs transition cursor-pointer"
          >
            Search
          </button>
        </form>
      </Card>

      {/* Manufacturer Dossier Cards */}
      {loading ? (
        <div className="py-12 text-center space-y-2">
          <div className="w-6 h-6 border-2 border-blue-900 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Analyzing historical surveillance records...</p>
        </div>
      ) : manufacturers.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {manufacturers.map((mfr) => {
            const hasPotentialIssues = mfr.potential_violations > 0;
            const repeatIssuesList = mfr.repeated_issues || [];

            return (
              <Card
                key={mfr.manufacturer_name}
                padding="md"
                className={`space-y-3 transition hover:border-slate-300 dark:border-slate-700 ${
                  hasPotentialIssues ? 'border-l-3 border-l-rose-600' : 'border-l-3 border-l-emerald-600'
                }`}
              >
                {/* Brand Header */}
                <div className="flex items-start justify-between gap-3 pb-2.5 border-b border-slate-100">
                  <div className="truncate">
                    <h3 className="font-bold text-xs text-slate-900 dark:text-white truncate" title={mfr.manufacturer_name}>
                      {mfr.manufacturer_name}
                    </h3>
                    <span className="text-[11px] text-slate-500 dark:text-slate-400 block mt-0.5 font-mono">
                      {mfr.total_inspections} package(s) inspected
                    </span>
                  </div>

                  {hasPotentialIssues ? (
                    <Badge variant="danger" size="sm">
                      Issues flagged
                    </Badge>
                  ) : (
                    <Badge variant="success" size="sm">
                      Verified
                    </Badge>
                  )}
                </div>

                {/* KPI Metrics Mini-Grid */}
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="p-1.5 rounded bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-800">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 block">Compliant</span>
                    <span className="font-bold font-mono text-emerald-700 text-xs">
                      {mfr.compliant_inspections}
                    </span>
                  </div>

                  <div className="p-1.5 rounded bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-800">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 block">Issues</span>
                    <span className="font-bold font-mono text-rose-700 text-xs">
                      {mfr.potential_violations}
                    </span>
                  </div>

                  <div className="p-1.5 rounded bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-800">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 block">Review</span>
                    <span className="font-bold font-mono text-amber-700 text-xs">
                      {mfr.manual_reviews}
                    </span>
                  </div>
                </div>

                {/* Repeated Issues Ledger */}
                <div className="space-y-1 pt-1">
                  <span className="text-[10px] uppercase font-bold text-slate-500 dark:text-slate-400 tracking-wider block">
                    Repeated Issues:
                  </span>
                  {repeatIssuesList.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {repeatIssuesList.map((issue, idx) => (
                        <span
                          key={idx}
                          className="px-1.5 py-0.5 rounded bg-rose-50 border border-rose-200 text-rose-800 text-[10px] font-mono"
                        >
                          {issue.label || issue.field} ({issue.count})
                        </span>
                      ))}
                    </div>
                  ) : (
                    <span className="text-[11px] text-slate-400 italic">None recorded</span>
                  )}
                </div>

                {/* Direct Action Link to filtered inspections */}
                {onNavigateToHistoryWithFilter && (
                  <div className="pt-2 border-t border-slate-100 flex justify-end">
                    <button
                      onClick={() => onNavigateToHistoryWithFilter(mfr.manufacturer_name)}
                      className="text-[11px] font-semibold text-blue-900 hover:underline inline-flex items-center gap-1 cursor-pointer"
                    >
                      <span>View inspections</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      ) : (
        <EmptyState
          icon={Building2}
          title="No manufacturer records found"
          description="Try searching for another manufacturer or brand name."
        />
      )}
    </div>
  );
};
