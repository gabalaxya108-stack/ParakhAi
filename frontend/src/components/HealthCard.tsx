import React from 'react';
import { HealthResponse } from '../types/health';
import { ApiClientError } from '../api/client';

interface HealthCardProps {
  health: HealthResponse | null;
  loading: boolean;
  error: ApiClientError | null;
  onRefresh: () => void;
}

export const HealthCard: React.FC<HealthCardProps> = ({ health, loading, error, onRefresh }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl max-w-xl w-full">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">System Health & Diagnostic</h2>
          <p className="text-xs text-slate-400 font-mono mt-0.5">GET /api/v1/health</p>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-50 dark:bg-blue-950/400 disabled:opacity-50 text-xs font-semibold text-white transition shadow"
        >
          {loading ? 'Pinging...' : 'Refresh Status'}
        </button>
      </div>

      {loading && !health && !error && (
        <div className="py-8 flex flex-col items-center justify-center gap-2">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">Verifying backend service...</span>
        </div>
      )}

      {error && (
        <div className="bg-rose-950/40 border border-rose-500/30 rounded-xl p-4 text-xs text-rose-300">
          <div className="font-bold text-rose-400 mb-1">Connection Error ({error.code})</div>
          <p>{error.message}</p>
          <div className="text-[10px] text-slate-400 font-mono mt-2">{error.timestamp}</div>
        </div>
      )}

      {health && (
        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/80 border border-slate-800">
            <span className="text-xs font-medium text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">Operational Status</span>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">{health.status}</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-slate-950/50 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-400 block mb-1">Service</span>
              <span className="font-semibold text-slate-200">{health.service}</span>
            </div>
            <div className="bg-slate-950/50 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-400 block mb-1">Version</span>
              <span className="font-mono font-bold text-blue-400">v{health.version}</span>
            </div>
            <div className="bg-slate-950/50 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-400 block mb-1">Environment</span>
              <span className="font-semibold text-slate-200 capitalize">{health.environment}</span>
            </div>
            <div className="bg-slate-950/50 p-3 rounded-xl border border-slate-800">
              <span className="text-slate-400 block mb-1">Uptime</span>
              <span className="font-mono text-slate-200">{health.uptime_seconds}s</span>
            </div>
          </div>

          <div className="text-[11px] font-mono text-slate-400 text-right pt-2 border-t border-slate-800/80">
            Timestamp: {health.timestamp}
          </div>
        </div>
      )}
    </div>
  );
};
