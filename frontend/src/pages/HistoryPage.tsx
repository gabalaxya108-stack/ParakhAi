import React, { useState, useEffect } from 'react';
import { History, Search, Download, CheckCircle2, AlertOctagon, ChevronRight, Eye, Filter } from 'lucide-react';
import { InspectionSummaryDTO } from '../types';
import { api } from '../services/api';

interface HistoryPageProps {
  onOpenInspection: (id: string) => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({ onOpenInspection }) => {
  const [inspections, setInspections] = useState<InspectionSummaryDTO[]>([]);
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadHistory() {
      try {
        setLoading(true);
        const data = await api.getInspections();
        setInspections(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, []);

  const filtered = inspections.filter(item => {
    const matchesSearch =
      item.commodity_name.toLowerCase().includes(search.toLowerCase()) ||
      item.inspection_number.toLowerCase().includes(search.toLowerCase()) ||
      item.commodity_category.toLowerCase().includes(search.toLowerCase()) ||
      (item.brand_name && item.brand_name.toLowerCase().includes(search.toLowerCase()));

    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'PASS' && item.overall_compliance === 'PASS') ||
      (statusFilter === 'FAIL' && item.overall_compliance === 'FAIL');

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-blue-400">Audit Trail</span>
          <h1 className="text-2xl font-black text-white mt-0.5">Inspection History & Official Reports</h1>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3 bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by commodity, brand, inspection number, or category..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:focus:ring-blue-400"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <button
            onClick={() => setStatusFilter('all')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
              statusFilter === 'all' ? 'bg-blue-600 text-white' : 'bg-slate-950 text-slate-400 hover:text-white'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setStatusFilter('PASS')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
              statusFilter === 'PASS' ? 'bg-emerald-600 text-white' : 'bg-slate-950 text-slate-400 hover:text-white'
            }`}
          >
            Compliant
          </button>
          <button
            onClick={() => setStatusFilter('FAIL')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
              statusFilter === 'FAIL' ? 'bg-rose-600 text-white' : 'bg-slate-950 text-slate-400 hover:text-white'
            }`}
          >
            Violations
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-3xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-semibold">
                <th className="py-3 px-4">Inspection Ref</th>
                <th className="py-3 px-4">Commodity / Brand</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Date</th>
                <th className="py-3 px-4">Compliance Verdict</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {filtered.map(item => {
                const isPass = item.overall_compliance === 'PASS';
                const isFail = item.overall_compliance === 'FAIL';
                const pdfUrl = api.getReportPdfUrl(item.id);

                return (
                  <tr key={item.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-mono font-bold text-blue-400">
                      {item.inspection_number}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-100">{item.commodity_name}</div>
                      {item.brand_name && <div className="text-[11px] text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400">{item.brand_name}</div>}
                    </td>
                    <td className="py-3 px-4 text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400">{item.commodity_category}</td>
                    <td className="py-3 px-4 font-mono text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400">{item.created_at.slice(0, 10)}</td>
                    <td className="py-3 px-4">
                      {isPass ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/400/10 text-emerald-400 border border-emerald-500/20">
                          <CheckCircle2 className="w-3 h-3" /> Compliant
                        </span>
                      ) : isFail ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-rose-50 dark:bg-rose-950/400/10 text-rose-400 border border-rose-500/20">
                          <AlertOctagon className="w-3 h-3" /> {item.violations_count} Violations
                        </span>
                      ) : (
                        <span className="inline-flex items-center text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/400/10 text-amber-400 border border-amber-500/20">
                          Pending
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => onOpenInspection(item.id)}
                          className="px-2.5 py-1 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 font-semibold text-[11px] flex items-center gap-1 transition"
                        >
                          <Eye className="w-3 h-3" /> Cockpit
                        </button>
                        <a
                          href={pdfUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
                          title="Download PDF Report"
                        >
                          <Download className="w-3.5 h-3.5" />
                        </a>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
