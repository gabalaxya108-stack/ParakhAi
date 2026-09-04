import React, { useEffect, useState } from 'react';
import {
  BookOpen,
  Search,
  Filter,
  FileText,
  History,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  ExternalLink,
  Calendar,
  Layers,
  ArrowRight,
  RefreshCw
} from 'lucide-react';
import { rulesApi } from '../api/rules';
import {
  RuleModel,
  RegulatoryDocumentDTO,
  RuleAmendmentDTO,
  RegulatoryCatalogSummary
} from '../types/rules';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';

export const RuleCatalogPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'rules' | 'documents' | 'amendments' | 'admin'>('rules');
  const [rules, setRules] = useState<RuleModel[]>([]);
  const [documents, setDocuments] = useState<RegulatoryDocumentDTO[]>([]);
  const [amendments, setAmendments] = useState<RuleAmendmentDTO[]>([]);
  const [summary, setSummary] = useState<RegulatoryCatalogSummary | null>(null);

  const [availableVersions, setAvailableVersions] = useState<string[]>(['2026.1', '2011']);
  const [selectedVersion, setSelectedVersion] = useState<string>('2026.1');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [ruleData, docData, amendData, sumData] = await Promise.all([
        rulesApi.getRules({
          version: selectedVersion,
          category: selectedCategory === 'all' ? undefined : selectedCategory,
        }),
        rulesApi.getRegulatoryDocuments().catch(() => []),
        rulesApi.getRuleAmendments().catch(() => []),
        rulesApi.getRegulatorySummary().catch(() => null),
      ]);

      setRules(ruleData.rules);
      setDocuments(docData);
      setAmendments(amendData);
      setSummary(sumData);
      if (sumData?.available_versions) {
        setAvailableVersions(sumData.available_versions);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load regulatory data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedVersion, selectedCategory]);

  const filteredRules = rules.filter((r) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.rule_id.toLowerCase().includes(q) ||
      (r.name && r.name.toLowerCase().includes(q)) ||
      (r.title && r.title.toLowerCase().includes(q)) ||
      r.field_to_validate.toLowerCase().includes(q) ||
      (r.section && r.section.toLowerCase().includes(q)) ||
      (r.source_reference && r.source_reference.toLowerCase().includes(q))
    );
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Header */}
      <PageHeader
        title="Regulatory Rules & Statutory Database"
        subtitle="Versioned Department of Consumer Affairs (DCA) requirements under the Legal Metrology (Packaged Commodities) Rules, 2011 and official amendments."
      />

      {/* Summary KPI Ribbon */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
            <div className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Active Rules</div>
            <div className="text-xl font-bold text-blue-900 mt-1">{summary.active_rules}</div>
            <div className="text-[10px] text-emerald-600 font-medium mt-0.5">Enforced in inspection pipeline</div>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
            <div className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Official Documents</div>
            <div className="text-xl font-bold text-slate-800 mt-1">{summary.documents_count}</div>
            <div className="text-[10px] text-slate-500 mt-0.5">Gazettes & notifications</div>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
            <div className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Statutory Amendments</div>
            <div className="text-xl font-bold text-slate-800 mt-1">{summary.amendments_count}</div>
            <div className="text-[10px] text-slate-500 mt-0.5">Tracked historical changes</div>
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs">
            <div className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Active Catalog Version</div>
            <div className="text-xl font-bold text-indigo-900 mt-1">v{summary.latest_version}</div>
            <div className="text-[10px] text-slate-500 mt-0.5">Date-indexed resolution</div>
          </div>
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded border border-rose-200 bg-rose-50 text-xs text-rose-800 flex items-center gap-2.5">
          <AlertOctagon className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 gap-6 text-xs font-medium">
        <button
          onClick={() => setActiveTab('rules')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition cursor-pointer ${
            activeTab === 'rules'
              ? 'border-blue-900 text-blue-900 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-100'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span>Statutory Rules ({rules.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('documents')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition cursor-pointer ${
            activeTab === 'documents'
              ? 'border-blue-900 text-blue-900 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-100'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Official DCA Publications ({documents.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('amendments')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition cursor-pointer ${
            activeTab === 'amendments'
              ? 'border-blue-900 text-blue-900 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-100'
          }`}
        >
          <History className="w-4 h-4" />
          <span>Statutory Amendments ({amendments.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('admin')}
          className={`pb-3 border-b-2 flex items-center gap-2 transition cursor-pointer ${
            activeTab === 'admin'
              ? 'border-blue-900 text-blue-900 font-semibold'
              : 'border-transparent text-slate-500 hover:text-slate-800 dark:text-slate-100'
          }`}
        >
          <ShieldCheck className="w-4 h-4" />
          <span>Governance & Staging</span>
        </button>
      </div>

      {/* Tab 1: Statutory Rules */}
      {activeTab === 'rules' && (
        <div className="space-y-4">
          {/* Version Selector & Filter Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-3 rounded-lg border border-slate-200 shadow-xs">
            <div className="relative w-full sm:w-80">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by rule ID, declaration, or statutory section..."
                className="w-full pl-8 pr-3 py-1.5 rounded border border-slate-200 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-900 transition"
              />
            </div>

            <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto text-xs">
              <div className="flex items-center gap-1.5">
                <span className="text-slate-500 font-medium">Category:</span>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="px-2.5 py-1 rounded border border-slate-200 bg-white text-xs text-slate-800 focus:outline-none focus:border-blue-900 cursor-pointer"
                >
                  <option value="all">All Commodities</option>
                  <option value="packaged_commodity">Packaged Commodity</option>
                  <option value="food">Food & Beverages</option>
                  <option value="cosmetics">Cosmetics</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5">
                <span className="text-slate-500 font-medium">Version:</span>
                <select
                  value={selectedVersion}
                  onChange={(e) => setSelectedVersion(e.target.value)}
                  className="px-2.5 py-1 rounded border border-slate-200 bg-white font-mono text-xs text-slate-800 focus:outline-none focus:border-blue-900 cursor-pointer"
                >
                  {availableVersions.map((v) => (
                    <option key={v} value={v}>
                      v{v} {v === '2026.1' ? '(Active)' : ''}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Rules Table */}
          <Card padding="none" className="overflow-hidden">
            {loading ? (
              <div className="py-12 text-center space-y-2">
                <div className="w-6 h-6 border-2 border-blue-900 border-t-transparent rounded-full animate-spin mx-auto"></div>
                <p className="text-xs text-slate-500 font-medium">Loading database-backed rules...</p>
              </div>
            ) : filteredRules.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                      <th className="py-2.5 px-4">Rule ID & Section</th>
                      <th className="py-2.5 px-3">Statutory Requirement</th>
                      <th className="py-2.5 px-3">Declaration</th>
                      <th className="py-2.5 px-3">Validation Type</th>
                      <th className="py-2.5 px-3">Severity</th>
                      <th className="py-2.5 px-3">Effective Date</th>
                      <th className="py-2.5 px-4 text-right">Official Source</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {filteredRules.map((r) => {
                      return (
                        <tr key={r.rule_id} className="hover:bg-slate-50 transition">
                          <td className="py-2.5 px-4 font-mono text-blue-900 font-semibold text-[11px]">
                            <div>{r.rule_id}</div>
                            {r.section && (
                              <div className="text-[10px] text-slate-500 font-sans mt-0.5">
                                {r.section} {r.sub_rule || ''}
                              </div>
                            )}
                          </td>

                          <td className="py-2.5 px-3 font-medium text-slate-900 max-w-[300px]">
                            <div>{r.title || r.name}</div>
                            <div className="text-[11px] text-slate-500 font-normal leading-snug mt-0.5">{r.requirement}</div>
                          </td>

                          <td className="py-2.5 px-3 font-mono text-slate-700 text-[11px] capitalize">
                            {r.field_to_validate.replace(/_/g, ' ')}
                          </td>

                          <td className="py-2.5 px-3 font-mono text-slate-600 text-[11px]">
                            <span className="inline-flex px-1.5 py-0.5 rounded bg-slate-100 border border-slate-200 text-[10px]">
                              {r.validation_type}
                            </span>
                          </td>

                          <td className="py-2.5 px-3">
                            <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-semibold border ${
                              r.severity === 'CRITICAL'
                                ? 'bg-rose-50 text-rose-800 border-rose-200 dark:border-rose-900'
                                : r.severity === 'HIGH'
                                ? 'bg-amber-50 text-amber-800 border-amber-200 dark:border-amber-900'
                                : 'bg-slate-100 text-slate-700 border-slate-200 dark:border-slate-800'
                            }`}>
                              {r.severity}
                            </span>
                          </td>

                          <td className="py-2.5 px-3 font-mono text-slate-600 text-[11px]">
                            {r.effective_from}
                          </td>

                          <td className="py-2.5 px-4 text-right">
                            {r.source_url ? (
                              <a
                                href={r.source_url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1 text-[11px] text-blue-900 hover:underline font-mono"
                              >
                                <span>{r.source_reference || 'View Source'}</span>
                                <ExternalLink className="w-3 h-3 shrink-0" />
                              </a>
                            ) : (
                              <span className="text-[11px] text-slate-500 font-mono">
                                {r.source_reference || 'Department of Consumer Affairs'}
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-slate-500 dark:text-slate-400 dark:text-slate-500">
                No rules match the current query.
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Tab 2: Official DCA Documents */}
      {activeTab === 'documents' && (
        <Card padding="none" className="overflow-hidden">
          <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-slate-900 dark:text-white">Authoritative Government Sources</div>
              <div className="text-[11px] text-slate-500 mt-0.5">
                Statutory acts, rules, and Gazette of India notifications published by the Department of Consumer Affairs.
              </div>
            </div>
            <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400 dark:text-slate-500">
              Total: {documents.length} verified documents
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold">
                  <th className="py-2.5 px-4">Publication Name</th>
                  <th className="py-2.5 px-3">Type</th>
                  <th className="py-2.5 px-3">Notification Number</th>
                  <th className="py-2.5 px-3">Publication Date</th>
                  <th className="py-2.5 px-3">Effective Date</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-4 text-right">Gazette / Official Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50 transition">
                    <td className="py-3 px-4 font-medium text-slate-900 max-w-[320px]">
                      <div>{doc.document_name}</div>
                      <div className="text-[11px] text-slate-500 font-normal mt-0.5">{doc.source_reference}</div>
                    </td>

                    <td className="py-3 px-3">
                      <span className="inline-flex px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-100 border border-slate-200 text-slate-700 dark:text-slate-200">
                        {doc.document_type}
                      </span>
                    </td>

                    <td className="py-3 px-3 font-mono text-blue-900 text-[11px] font-semibold">
                      {doc.notification_number || 'N/A'}
                    </td>

                    <td className="py-3 px-3 font-mono text-slate-600 text-[11px]">
                      {doc.publication_date}
                    </td>

                    <td className="py-3 px-3 font-mono text-slate-600 text-[11px]">
                      {doc.effective_date}
                    </td>

                    <td className="py-3 px-3">
                      <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-semibold border ${
                        doc.status === 'ACTIVE'
                          ? 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:border-emerald-900'
                          : 'bg-slate-100 text-slate-600 border-slate-200 dark:border-slate-800'
                      }`}>
                        {doc.status}
                      </span>
                    </td>

                    <td className="py-3 px-4 text-right">
                      {doc.source_url ? (
                        <a
                          href={doc.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] text-blue-900 hover:underline font-mono"
                        >
                          <span>Official PDF / Gazette</span>
                          <ExternalLink className="w-3 h-3 shrink-0" />
                        </a>
                      ) : (
                        <span className="text-[11px] text-slate-500 font-mono">DCA Record</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Tab 3: Statutory Amendments Timeline */}
      {activeTab === 'amendments' && (
        <Card padding="none" className="overflow-hidden">
          <div className="p-4 bg-slate-50 border-b border-slate-200 dark:border-slate-800">
            <div className="text-xs font-semibold text-slate-900 dark:text-white">Legislative Amendment Audit Trail</div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              Historical record of statutory insertions, substitutions, and clarifications across gazetted amendments.
            </div>
          </div>

          <div className="p-4 space-y-4">
            {amendments.map((am) => (
              <div key={am.id} className="p-3.5 rounded-lg border border-slate-200 bg-white space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-blue-900">{am.rule_id}</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-indigo-50 text-indigo-800 border border-indigo-200 dark:border-indigo-900">
                      {am.change_type}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-[11px] text-slate-500 font-mono">
                    <Calendar className="w-3.5 h-3.5" />
                    <span>Effective from: {am.effective_from}</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-1">
                  {am.previous_value && (
                    <div className="p-2.5 rounded bg-rose-50/60 border border-rose-100">
                      <div className="text-[10px] uppercase font-semibold text-rose-800 tracking-wider">Previous Requirement</div>
                      <div className="text-slate-800 mt-1 text-[11px]">{am.previous_value}</div>
                    </div>
                  )}

                  <div className="p-2.5 rounded bg-emerald-50/60 border border-emerald-100">
                    <div className="text-[10px] uppercase font-semibold text-emerald-800 tracking-wider">Amended / Mandated Requirement</div>
                    <div className="text-slate-800 mt-1 text-[11px]">{am.new_value}</div>
                  </div>
                </div>

                {am.explanation && (
                  <div className="text-[11px] text-slate-600 bg-slate-50 p-2 rounded border border-slate-200/60">
                    <span className="font-semibold text-slate-700 dark:text-slate-200">Statutory Rationale:</span> {am.explanation}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Tab 4: Admin Governance & Staging */}
      {activeTab === 'admin' && (
        <div className="space-y-4">
          <Card className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-slate-900 dark:text-white">Regulatory Staging & Approval Workflow</div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  AI-assisted document ingestion proposes candidate rules with status PENDING_REVIEW. Human admin approval is strictly required before rules become ACTIVE.
                </div>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-200 dark:border-amber-900">
                Human-In-The-Loop Enforced
              </span>
            </div>

            <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-2">
              <div className="font-semibold text-slate-800 dark:text-slate-100">Operational Governance Lifecycle:</div>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 text-[11px]">
                <div className="p-2 rounded bg-white border border-slate-200 dark:border-slate-800">
                  <span className="font-semibold text-amber-700 dark:text-amber-400">1. PENDING_REVIEW</span>
                  <p className="text-slate-500 mt-0.5">Ingested from gazette notification; quarantined from inspection engine.</p>
                </div>
                <div className="p-2 rounded bg-white border border-slate-200 dark:border-slate-800">
                  <span className="font-semibold text-blue-700 dark:text-blue-400">2. APPROVED</span>
                  <p className="text-slate-500 mt-0.5">Verified by Legal Metrology officer against official gazette text.</p>
                </div>
                <div className="p-2 rounded bg-white border border-slate-200 dark:border-slate-800">
                  <span className="font-semibold text-emerald-700 dark:text-emerald-400">3. ACTIVE</span>
                  <p className="text-slate-500 mt-0.5">Live in inspection pipeline; evaluated against uploaded packages.</p>
                </div>
                <div className="p-2 rounded bg-white border border-slate-200 dark:border-slate-800">
                  <span className="font-semibold text-slate-700 dark:text-slate-200">4. SUPERSEDED</span>
                  <p className="text-slate-500 mt-0.5">Archived by newer amendment; retained for historical reproducibility.</p>
                </div>
              </div>
            </div>

            <div className="text-xs text-slate-600 dark:text-slate-400 dark:text-slate-500">
              Currently, all 13 core statutory requirements under the Legal Metrology (Packaged Commodities) Rules, 2011 are verified and in <strong className="text-emerald-700 dark:text-emerald-400">ACTIVE</strong> status.
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
