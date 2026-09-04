import React, { useState, useEffect } from 'react';
import { BookOpen, Search, Scale, ShieldAlert, CheckCircle, AlertTriangle, ExternalLink } from 'lucide-react';
import { RuleDefinition } from '../types';
import { api } from '../services/api';

export const RulesLibraryPage: React.FC = () => {
  const [rules, setRules] = useState<RuleDefinition[]>([]);
  const [search, setSearch] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadRules() {
      try {
        const data = await api.getRules();
        setRules(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadRules();
  }, []);

  const filtered = rules.filter(r =>
    r.rule_id.toLowerCase().includes(search.toLowerCase()) ||
    r.title.toLowerCase().includes(search.toLowerCase()) ||
    r.legal_reference.toLowerCase().includes(search.toLowerCase()) ||
    r.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 p-6 rounded-3xl border border-slate-800 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-indigo-50 dark:bg-indigo-950/400/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">Statutory Legal Codification</span>
            <h1 className="text-2xl font-black text-white mt-0.5">Legal Metrology Rules Catalog</h1>
          </div>
        </div>
        <p className="text-xs text-slate-300 mt-2 max-w-3xl leading-relaxed">
          The platform codifies statutory provisions from the <strong>Legal Metrology Act, 2009</strong> and the <strong>Legal Metrology (Packaged Commodities) Rules, 2011</strong> (including 2022/2023 Amendments) into deterministic, auditable software rules.
        </p>
      </div>

      {/* Schedule II Font Height Table Reference Banner */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 space-y-3">
        <div className="flex items-center gap-2">
          <Scale className="w-4 h-4 text-blue-400" />
          <h3 className="text-sm font-bold text-white">Schedule II: Mandatory Minimum Height of Numerals and Letters</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-semibold bg-slate-950/50">
                <th className="py-2.5 px-3">Area of Principal Display Panel (A)</th>
                <th className="py-2.5 px-3">Min. Height of Numeral</th>
                <th className="py-2.5 px-3">Min. Height of Letter</th>
                <th className="py-2.5 px-3">Applicability</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
              <tr>
                <td className="py-2 px-3">A &le; 50 cm²</td>
                <td className="py-2 px-3 text-amber-400 font-bold">1.5 mm</td>
                <td className="py-2 px-3 text-slate-200">1.0 mm</td>
                <td className="py-2 px-3 font-sans text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">Small pouches, sachets</td>
              </tr>
              <tr>
                <td className="py-2 px-3">50 cm² &lt; A &le; 100 cm²</td>
                <td className="py-2 px-3 text-amber-400 font-bold">2.0 mm</td>
                <td className="py-2 px-3 text-slate-200">1.5 mm</td>
                <td className="py-2 px-3 font-sans text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">Standard snack pouches, cosmetics</td>
              </tr>
              <tr>
                <td className="py-2 px-3">100 cm² &lt; A &le; 500 cm²</td>
                <td className="py-2 px-3 text-amber-400 font-bold">4.0 mm</td>
                <td className="py-2 px-3 text-slate-200">2.5 mm</td>
                <td className="py-2 px-3 font-sans text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">Medium boxes, large bags (chips, coffee)</td>
              </tr>
              <tr>
                <td className="py-2 px-3">A &gt; 500 cm²</td>
                <td className="py-2 px-3 text-amber-400 font-bold">6.0 mm</td>
                <td className="py-2 px-3 text-slate-200">4.0 mm</td>
                <td className="py-2 px-3 font-sans text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">Bulk cartons, detergent packs</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-4 top-3.5" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by rule code, title, legal reference, or statutory section..."
          className="w-full bg-slate-900 border border-slate-800 rounded-2xl pl-11 pr-4 py-3 text-xs text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400"
        />
      </div>

      {/* Rules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map(r => (
          <div key={r.rule_id} className="bg-slate-900/60 border border-slate-800 p-5 rounded-2xl space-y-3 shadow-md hover:border-slate-700 transition">
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950/400/10 text-blue-400 border border-blue-500/20">
                {r.rule_id}
              </span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                r.severity === 'CRITICAL' ? 'bg-rose-50 dark:bg-rose-950/400/10 text-rose-400 border-rose-500/20' : 'bg-amber-50 dark:bg-amber-950/400/10 text-amber-400 border-amber-500/20'
              }`}>
                {r.severity}
              </span>
            </div>

            <div>
              <h4 className="font-bold text-sm text-white">{r.title}</h4>
              <p className="text-xs text-indigo-400 font-medium mt-0.5">{r.legal_reference}</p>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">{r.description}</p>

            {r.penalty_section && (
              <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400 flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                <span>Statutory Penalty: <strong className="text-slate-300">{r.penalty_section}</strong></span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
