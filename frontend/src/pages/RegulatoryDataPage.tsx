import React, { useEffect, useState } from 'react';
import { Database, ShieldCheck, FileText, CheckCircle2, Clock, ExternalLink, Activity, Search, RefreshCw, Layers } from 'lucide-react';
import { fetchJson } from '../api/client';

interface DatabaseHealth {
  status: string;
  database: string;
  engine_dialect: string;
  environment: string;
  host: string;
  database_name: string;
  latency_ms: number;
  checked_at: string;
  metrics: {
    total_rules: number;
    active_rules: number;
    pending_rules: number;
    superseded_rules: number;
    documents_count: number;
    amendments_count: number;
    latest_version: string;
  };
}

interface RuleItem {
  id: string;
  rule_id: string;
  rule_version: string;
  title: string;
  section: string;
  sub_rule?: string;
  requirement: string;
  applicable_categories: string[];
  field_to_validate: string;
  validation_type: string;
  severity: string;
  effective_from: string;
  effective_until?: string;
  status: string;
  source_document_id?: string;
  source_url?: string;
  source_page?: string;
  source_excerpt?: string;
}

export const RegulatoryDataPage: React.FC = () => {
  const [health, setHealth] = useState<DatabaseHealth | null>(null);
  const [rules, setRules] = useState<RuleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedRule, setSelectedRule] = useState<RuleItem | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const healthRes = await fetchJson<DatabaseHealth>('/system/database-health');
      setHealth(healthRes);

      const rulesRes = await fetchJson<RuleItem[]>('/regulatory/rules');
      setRules(rulesRes);
    } catch (err) {
      console.error('Failed to load regulatory data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredRules = rules.filter((r) => {
    const q = search.toLowerCase();
    return (
      r.rule_id.toLowerCase().includes(q) ||
      r.title.toLowerCase().includes(q) ||
      r.requirement.toLowerCase().includes(q) ||
      r.section.toLowerCase().includes(q)
    );
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 text-white rounded-2xl shadow-xl border border-slate-800">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 text-xs font-mono font-semibold border border-blue-400/20">
              PARAKH AI KNOWLEDGE BASE
            </span>
            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-xs font-mono font-semibold border border-emerald-400/20 flex items-center gap-1">
              <Activity className="w-3 h-3 animate-pulse" /> LIVE DATABASE
            </span>
          </div>
          <h1 className="text-2xl font-black tracking-tight">Regulatory Knowledge Base</h1>
          <p className="text-sm text-slate-300 mt-1 max-w-2xl">
            Versioned statutory requirements synchronized from official Department of Consumer Affairs Legal Metrology Gazettes.
          </p>
        </div>

        <button
          onClick={fetchData}
          disabled={loading}
          className="self-start md:self-auto px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition flex items-center gap-2 shadow-lg"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Database Health</span>
        </button>
      </div>

      {/* Database Health Summary Ribbon */}
      {health && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
            <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Database Engine</div>
            <div className="text-base font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wide mt-1 flex items-center gap-1.5">
              <Database className="w-4 h-4 text-blue-600" />
              {health.database}
            </div>
            <div className="text-[10px] text-emerald-600 font-semibold mt-1">Status: {health.status} ({health.latency_ms}ms)</div>
          </div>

          <div className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
            <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Active Statutory Rules</div>
            <div className="text-xl font-black text-slate-900 dark:text-slate-100 mt-1">{health.metrics.active_rules}</div>
            <div className="text-[10px] text-slate-400 mt-1">Version: {health.metrics.latest_version}</div>
          </div>

          <div className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
            <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Pending Review</div>
            <div className="text-xl font-black text-amber-600 mt-1">{health.metrics.pending_rules}</div>
            <div className="text-[10px] text-slate-400 mt-1">Human-in-the-loop staging</div>
          </div>

          <div className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
            <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Superseded Rules</div>
            <div className="text-xl font-black text-slate-500 mt-1">{health.metrics.superseded_rules}</div>
            <div className="text-[10px] text-slate-400 mt-1">Historical versions preserved</div>
          </div>

          <div className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
            <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">DCA Documents</div>
            <div className="text-xl font-black text-indigo-600 mt-1">{health.metrics.documents_count}</div>
            <div className="text-[10px] text-slate-400 mt-1">Official Gazette publications</div>
          </div>

          <div className="p-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
            <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">Amendments Tracked</div>
            <div className="text-xl font-black text-emerald-600 mt-1">{health.metrics.amendments_count}</div>
            <div className="text-[10px] text-slate-400 mt-1">Legislative additions</div>
          </div>
        </div>
      )}

      {/* Rules Table Section */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">Live Statutory Rules Catalog</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Queried directly from database table <code>regulatory_rules</code>.</p>
          </div>

          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search rule ID, section, requirement..."
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto border border-slate-200 dark:border-slate-800 rounded-xl">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-100 dark:bg-slate-800/60 text-slate-700 dark:text-slate-300 font-semibold border-b border-slate-200 dark:border-slate-800">
                <th className="p-3">Rule ID</th>
                <th className="p-3">Section</th>
                <th className="p-3">Requirement</th>
                <th className="p-3">Target Field</th>
                <th className="p-3">Validation Type</th>
                <th className="p-3">Effective From</th>
                <th className="p-3">Status</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-slate-800 dark:text-slate-200 font-medium">
              {filteredRules.map((rule) => (
                <tr key={rule.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
                  <td className="p-3 font-mono font-bold text-blue-600 dark:text-blue-400">{rule.rule_id}</td>
                  <td className="p-3 text-slate-600 dark:text-slate-400">{rule.section} {rule.sub_rule ? `(${rule.sub_rule})` : ''}</td>
                  <td className="p-3 max-w-xs truncate">{rule.title || rule.requirement}</td>
                  <td className="p-3 font-mono text-[11px]">{rule.field_to_validate}</td>
                  <td className="p-3 font-mono text-[10px] uppercase">
                    <span className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700">
                      {rule.validation_type}
                    </span>
                  </td>
                  <td className="p-3 text-slate-500 font-mono">{rule.effective_from ? rule.effective_from.substring(0, 10) : '2011-03-01'}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      rule.status === 'ACTIVE'
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                        : 'bg-slate-100 text-slate-600 border border-slate-300'
                    }`}>
                      {rule.status}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => setSelectedRule(rule)}
                      className="px-2.5 py-1 bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 rounded-lg text-[11px] font-bold hover:opacity-90 transition"
                    >
                      Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Rule Detail Modal Drawer */}
      {selectedRule && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 max-w-2xl w-full p-6 shadow-2xl space-y-4 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-start justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <div>
                <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300 text-xs font-mono font-bold">
                  {selectedRule.rule_id} • v{selectedRule.rule_version}
                </span>
                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-1">{selectedRule.title}</h3>
              </div>
              <button
                onClick={() => setSelectedRule(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-900 dark:hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <div className="font-bold text-slate-500 uppercase tracking-wider text-[10px]">Statutory Section</div>
                <div className="text-slate-900 dark:text-slate-100 font-medium">{selectedRule.section} {selectedRule.sub_rule ? `sub-rule ${selectedRule.sub_rule}` : ''}</div>
              </div>

              <div>
                <div className="font-bold text-slate-500 uppercase tracking-wider text-[10px]">Requirement Description</div>
                <div className="text-slate-800 dark:text-slate-200 bg-slate-50 dark:bg-slate-800/60 p-2.5 rounded-xl border border-slate-200 dark:border-slate-700">
                  {selectedRule.requirement}
                </div>
              </div>

              {selectedRule.source_excerpt && (
                <div>
                  <div className="font-bold text-slate-500 uppercase tracking-wider text-[10px]">Official Gazette Excerpt</div>
                  <div className="text-slate-700 dark:text-slate-300 italic bg-amber-50/50 dark:bg-amber-950/20 p-2.5 rounded-xl border border-amber-200/50 font-serif">
                    "{selectedRule.source_excerpt}"
                  </div>
                </div>
              )}

              {selectedRule.source_url && (
                <div className="pt-2 flex items-center justify-between border-t border-slate-200 dark:border-slate-800">
                  <span className="text-slate-500 text-[11px]">Official Reference: {selectedRule.source_page || 'Gazette Notification'}</span>
                  <a
                    href={selectedRule.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="px-3 py-1.5 bg-blue-600 text-white rounded-lg font-bold flex items-center gap-1.5 text-xs hover:bg-blue-500 transition"
                  >
                    <span>View Official Source</span>
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
