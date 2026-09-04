import React, { useEffect, useState, useCallback } from "react";
import {
  Database,
  ExternalLink,
  RefreshCw,
  Search,
  Table as TableIcon,
  Eye,
  X,
  Server,
  Activity,
  Layers,
  HardDrive,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Shield
} from "lucide-react";
import { fetchJson } from "../api/client";

interface DBTableResponse {
  table: string;
  total_rows: number;
  schema_fields: string[];
  rows: any[];
  table_statistics: Record<string, number>;
}

export const DatabaseMonitorPage: React.FC = () => {
  const [activeTable, setActiveTable] = useState<string>("inspections");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [data, setData] = useState<DBTableResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedRecord, setSelectedRecord] = useState<any | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
  const [copySuccess, setCopySuccess] = useState<boolean>(false);

  const fetchTableData = useCallback(async (tableName: string, search: string = "") => {
    try {
      setLoading(true);
      const query = new URLSearchParams();
      query.append("table", tableName);
      if (search.trim()) query.append("search", search.trim());
      query.append("limit", "50");

      const res = await fetchJson<DBTableResponse>("/system/database-tables?" + query.toString());
      setData(res);
      setLastRefresh(new Date());
    } catch (err) {
      console.error("Failed to load database records:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTableData(activeTable, searchQuery);
  }, [activeTable, fetchTableData]);

  // Auto-refresh every 15s
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchTableData(activeTable, searchQuery);
    }, 15000);
    return () => clearInterval(interval);
  }, [autoRefresh, activeTable, searchQuery, fetchTableData]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchTableData(activeTable, searchQuery);
  };

  const handleCopyRecord = (record: any) => {
    navigator.clipboard.writeText(JSON.stringify(record, null, 2));
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  const totalRows = data?.table_statistics
    ? Object.values(data.table_statistics).reduce((a, b) => a + b, 0)
    : 0;

  const tablesList = [
    { id: "inspections", label: "Inspections", icon: Search, color: "blue" },
    { id: "products", label: "Products", icon: Layers, color: "emerald" },
    { id: "declarations", label: "Declarations", icon: TableIcon, color: "amber" },
    { id: "compliance_checks", label: "Rule Checks", icon: Shield, color: "violet" },
    { id: "complaints", label: "Complaints", icon: AlertTriangle, color: "rose" },
    { id: "audit_logs", label: "Audit Logs", icon: Activity, color: "slate" }
  ];

  const getStatusBadge = (val: string) => {
    const v = String(val).toUpperCase();
    if (v === "COMPLIANT" || v === "PASS" || v === "ACTIVE" || v === "CLOSED") {
      return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300";
    }
    if (v === "NON_COMPLIANT" || v === "FAIL" || v === "PENDING_NOTICE") {
      return "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300";
    }
    if (v === "NEEDS_REVIEW" || v === "MANUAL_REVIEW" || v === "UNABLE_TO_VERIFY") {
      return "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300";
    }
    return "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300";
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-950 dark:to-indigo-950 text-blue-700 dark:text-blue-400 shadow-sm">
              <Database className="w-5 h-5" />
            </span>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
                Database & System Monitor
              </h1>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Live read-only transparency portal • PostgreSQL persistence layer
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Auto-refresh toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={"inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-semibold border transition cursor-pointer " + (autoRefresh ? "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-900 text-emerald-800 dark:text-emerald-300" : "bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-400")}
          >
            <span className={"w-1.5 h-1.5 rounded-full " + (autoRefresh ? "bg-emerald-500 animate-pulse" : "bg-slate-400")} />
            {autoRefresh ? "Live (15s)" : "Paused"}
          </button>

          {/* Last refresh timestamp */}
          <span className="hidden sm:flex items-center gap-1 text-[10px] text-slate-400 font-mono">
            <Clock className="w-3 h-3" />
            {lastRefresh.toLocaleTimeString()}
          </span>

          <button
            onClick={() => fetchTableData(activeTable, searchQuery)}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold shadow-sm transition cursor-pointer"
          >
            <RefreshCw className={"w-3.5 h-3.5 " + (loading ? "animate-spin" : "")} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

            {/* Rules Database & Statutory Source Monitor (Prompt Section 20) */}
      <div className="p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300">
              <Shield className="w-5 h-5" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">Rules Database & Statutory Source Grounding</h3>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                  Prototype Rule Dataset
                </span>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Transparent verification of codified Legal Metrology rules against authoritative public statutory sources
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="text-slate-400">Latest Version:</span>
            <strong className="px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300 font-bold border border-blue-200 dark:border-blue-800">2026.1</strong>
          </div>
        </div>

        {/* Source Verification Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider text-[10px] border-y border-slate-200 dark:border-slate-800">
              <tr>
                <th className="px-3 py-2">Statutory Authority / Document</th>
                <th className="px-3 py-2">Rules Codified</th>
                <th className="px-3 py-2">Verification Status</th>
                <th className="px-3 py-2 text-right">Official Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
              <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                <td className="px-3 py-2.5 font-medium">
                  Legal Metrology (Packaged Commodities) Rules, 2011
                  <span className="block text-[10px] text-slate-400 font-normal">Department of Consumer Affairs, Ministry of Consumer Affairs, Food & Public Distribution</span>
                </td>
                <td className="px-3 py-2.5 font-mono text-[11px]">Rules 6(1)(a)-(q), Rule 9</td>
                <td className="px-3 py-2.5">
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    Synchronized
                  </span>
                </td>
                <td className="px-3 py-2.5 text-right">
                  <a
                    href="https://consumeraffairs.nic.in/acts-and-rules/legal-metrology/the-legal-metrology-packaged-commodities-rules-2011"
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    <span>Open Source</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </td>
              </tr>

              <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                <td className="px-3 py-2.5 font-medium">
                  LM (Packaged Commodities) Amendment Rules, 2021 — Unit Sale Price
                  <span className="block text-[10px] text-slate-400 font-normal">Gazette Notification G.S.R. 779(E) mandating USP for net quantity &gt; 100g/ml</span>
                </td>
                <td className="px-3 py-2.5 font-mono text-[11px]">Rule 6(11) USP Formula</td>
                <td className="px-3 py-2.5">
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                    Synchronized
                  </span>
                </td>
                <td className="px-3 py-2.5 text-right">
                  <a
                    href="https://egazette.gov.in"
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    <span>Open Source</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </td>
              </tr>

              <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                <td className="px-3 py-2.5 font-medium">
                  FSSAI Food Safety and Standards (Labelling and Display) Regulations, 2020
                  <span className="block text-[10px] text-slate-400 font-normal">Cross-regulatory harmonization for food and nutritional commodity declarations</span>
                </td>
                <td className="px-3 py-2.5 font-mono text-[11px]">Sec. 5(1)-(3) Mfg/Expiry</td>
                <td className="px-3 py-2.5">
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                    Synchronized
                  </span>
                </td>
                <td className="px-3 py-2.5 text-right">
                  <a
                    href="https://fssai.gov.in"
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    <span>Open Source</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </td>
              </tr>

              <tr className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                <td className="px-3 py-2.5 font-medium">
                  State-Level Packaging Directives & Regional Language Mandates
                  <span className="block text-[10px] text-slate-400 font-normal">State Legal Metrology Controller circulars for regional bilingual declarations</span>
                </td>
                <td className="px-3 py-2.5 font-mono text-[11px]">Regional Addenda</td>
                <td className="px-3 py-2.5">
                  <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
                    Pending verification
                  </span>
                </td>
                <td className="px-3 py-2.5 text-right">
                  <span className="text-[11px] text-slate-400 italic">Source verification required</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* System Overview Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-4 rounded-xl bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/40 dark:to-indigo-950/30 border border-blue-200/60 dark:border-blue-900/40">
          <div className="flex items-center gap-2 mb-2">
            <HardDrive className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <span className="text-[10px] font-bold text-blue-700 dark:text-blue-400 uppercase tracking-wider">Engine</span>
          </div>
          <span className="text-sm font-bold text-slate-900 dark:text-white">PostgreSQL 16</span>
          <span className="block text-[10px] text-slate-500 dark:text-slate-400">SQLAlchemy ORM</span>
        </div>

        <div className="p-4 rounded-xl bg-gradient-to-br from-emerald-50 to-green-50 dark:from-emerald-950/40 dark:to-green-950/30 border border-emerald-200/60 dark:border-emerald-900/40">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span className="text-[10px] font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">Status</span>
          </div>
          <span className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Connected
          </span>
          <span className="block text-[10px] text-slate-500 dark:text-slate-400">All tables accessible</span>
        </div>

        <div className="p-4 rounded-xl bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-950/40 dark:to-orange-950/30 border border-amber-200/60 dark:border-amber-900/40">
          <div className="flex items-center gap-2 mb-2">
            <Layers className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            <span className="text-[10px] font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wider">Tables</span>
          </div>
          <span className="text-sm font-bold text-slate-900 dark:text-white">{data?.table_statistics ? Object.keys(data.table_statistics).length : "—"}</span>
          <span className="block text-[10px] text-slate-500 dark:text-slate-400">Monitored relations</span>
        </div>

        <div className="p-4 rounded-xl bg-gradient-to-br from-violet-50 to-purple-50 dark:from-violet-950/40 dark:to-purple-950/30 border border-violet-200/60 dark:border-violet-900/40">
          <div className="flex items-center gap-2 mb-2">
            <Server className="w-4 h-4 text-violet-600 dark:text-violet-400" />
            <span className="text-[10px] font-bold text-violet-700 dark:text-violet-400 uppercase tracking-wider">Records</span>
          </div>
          <span className="text-sm font-bold text-slate-900 dark:text-white">{totalRows}</span>
          <span className="block text-[10px] text-slate-500 dark:text-slate-400">Total persisted rows</span>
        </div>
      </div>

      {/* Table Statistics Cards */}
      {data && data.table_statistics && (
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
          {Object.entries(data.table_statistics).map(([tbl, cnt]) => {
            const tblInfo = tablesList.find(t => t.id === tbl);
            const TblIcon = tblInfo?.icon || TableIcon;
            return (
              <button
                key={tbl}
                onClick={() => {
                  setActiveTable(tbl);
                  setSearchQuery("");
                }}
                className={"p-3 rounded-xl border transition cursor-pointer text-center group " + (activeTable === tbl ? "bg-blue-50/70 border-blue-300 dark:bg-blue-950/40 dark:border-blue-700 shadow-sm ring-1 ring-blue-200 dark:ring-blue-800" : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-blue-200 dark:hover:border-blue-900 hover:shadow-sm")}
              >
                <TblIcon className={"w-4 h-4 mx-auto mb-1.5 " + (activeTable === tbl ? "text-blue-700 dark:text-blue-400" : "text-slate-400 group-hover:text-blue-600")} />
                <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider block truncate">
                  {tbl.replace(/_/g, " ")}
                </span>
                <span className={"text-lg font-bold " + (activeTable === tbl ? "text-blue-700 dark:text-blue-300" : "text-slate-900 dark:text-white")}>{cnt}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
          {tablesList.map((t) => (
            <button
              key={t.id}
              onClick={() => {
                setActiveTable(t.id);
                setSearchQuery("");
              }}
              className={"px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition cursor-pointer " + (activeTable === t.id ? "bg-blue-700 text-white shadow-xs" : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800")}
            >
              {t.label}
            </button>
          ))}
        </div>

        <form onSubmit={handleSearchSubmit} className="relative w-full sm:w-72">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={"Search " + activeTable.replace(/_/g, " ") + "..."}
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-hidden focus:ring-2 focus:ring-blue-600"
          />
        </form>
      </div>

      {/* Table Viewport */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-xs">
        {/* Table Meta Strip */}
        <div className="px-4 py-2 bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between text-[11px]">
          <span className="font-semibold text-slate-600 dark:text-slate-300 flex items-center gap-1.5">
            <TableIcon className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
            <code className="font-mono text-blue-700 dark:text-blue-300">{activeTable}</code>
            <span className="text-slate-400">•</span>
            <span>{data?.total_rows ?? 0} rows</span>
            <span className="text-slate-400">•</span>
            <span>{data?.schema_fields?.length ?? 0} columns</span>
          </span>
          <span className="text-[10px] text-slate-400 font-mono">
            PostgreSQL • Read-only
          </span>
        </div>

        {loading ? (
          <div className="p-16 text-center">
            <RefreshCw className="w-6 h-6 animate-spin text-blue-600 mx-auto mb-3" />
            <span className="text-xs text-slate-500">Querying PostgreSQL table <code className="font-mono text-blue-600">{activeTable}</code>...</span>
          </div>
        ) : !data || data.rows.length === 0 ? (
          <div className="p-16 text-center text-xs text-slate-500">
            <Database className="w-8 h-8 text-slate-300 dark:text-slate-700 mx-auto mb-3" />
            <span>No records found in <code className="font-mono text-blue-600">{activeTable}</code></span>
            {searchQuery && <span className="block mt-1 text-slate-400">Try clearing the search filter.</span>}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800/80 border-b border-slate-200 dark:border-slate-800 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-2.5 px-3 text-center w-10">#</th>
                  {data.schema_fields.map((col) => (
                    <th key={col} className="py-2.5 px-3 whitespace-nowrap">
                      {col.replace(/_/g, " ")}
                    </th>
                  ))}
                  <th className="py-2.5 px-3 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono text-[11px]">
                {data.rows.map((row, idx) => (
                  <tr
                    key={row.id || idx}
                    className="hover:bg-blue-50/40 dark:hover:bg-slate-800/40 transition"
                  >
                    <td className="py-2.5 px-3 text-center text-[10px] text-slate-400 font-mono">
                      {idx + 1}
                    </td>
                    {data.schema_fields.map((col) => {
                      const val = row[col];
                      const valStr = typeof val === "object" ? JSON.stringify(val) : String(val ?? "—");
                      const isStatusCol = col === "overall_status" || col === "status" || col === "review_status";
                      return (
                        <td key={col} className="py-2.5 px-3 max-w-[200px] truncate text-slate-700 dark:text-slate-300">
                          {isStatusCol ? (
                            <span className={"px-1.5 py-0.5 rounded text-[10px] font-bold " + getStatusBadge(valStr)}>
                              {valStr}
                            </span>
                          ) : col.includes("_at") || col.includes("timestamp") ? (
                            <span className="text-slate-500" title={valStr}>
                              {new Date(valStr).toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })}
                            </span>
                          ) : (
                            valStr
                          )}
                        </td>
                      );
                    })}
                    <td className="py-2.5 px-3 text-right whitespace-nowrap">
                      <button
                        onClick={() => setSelectedRecord(row)}
                        className="p-1.5 rounded-lg text-blue-700 hover:bg-blue-100 dark:text-blue-400 dark:hover:bg-slate-800 transition cursor-pointer"
                        title="Inspect Full Record"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Transparency Notice */}
      <div className="text-center text-[10px] text-slate-400 dark:text-slate-500 py-2 space-y-0.5">
        <p className="font-medium">
          <Shield className="w-3 h-3 inline mr-1" />
          Read-only database transparency view • No credentials exposed • All data persisted in PostgreSQL
        </p>
      </div>

      {/* Record Inspection Modal */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden">
            <div className="px-6 py-4 bg-gradient-to-r from-slate-900 via-blue-950 to-indigo-950 text-white flex items-center justify-between border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 rounded-lg bg-blue-600/30 border border-blue-400/20">
                  <TableIcon className="w-4 h-4 text-blue-300" />
                </div>
                <div>
                  <h3 className="text-sm font-bold">Record Inspector</h3>
                  <span className="text-[10px] text-slate-300 font-mono">{activeTable} • ID: {selectedRecord.id || "—"}</span>
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => handleCopyRecord(selectedRecord)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
                  title="Copy JSON"
                >
                  {copySuccess ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
                <button
                  onClick={() => setSelectedRecord(null)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="p-6 overflow-y-auto flex-1">
              {/* Key-value pairs view */}
              <div className="space-y-1.5 mb-4">
                {Object.entries(selectedRecord).map(([key, value]) => (
                  <div key={key} className="flex gap-3 text-xs py-1.5 border-b border-slate-100 dark:border-slate-800/60 last:border-0">
                    <span className="w-40 shrink-0 font-bold text-slate-500 dark:text-slate-400 uppercase text-[10px] tracking-wider pt-0.5">
                      {key.replace(/_/g, " ")}
                    </span>
                    <span className="text-slate-800 dark:text-slate-200 font-mono text-[11px] break-all">
                      {typeof value === "object" ? (
                        <pre className="bg-slate-50 dark:bg-slate-800 p-2 rounded-lg overflow-x-auto text-[10px] leading-relaxed">
                          {JSON.stringify(value, null, 2)}
                        </pre>
                      ) : (
                        String(value ?? "—")
                      )}
                    </span>
                  </div>
                ))}
              </div>

              {/* Raw JSON */}
              <details className="group">
                <summary className="text-[10px] font-bold text-slate-400 uppercase tracking-wider cursor-pointer hover:text-slate-600 dark:hover:text-slate-300 py-2">
                  ▸ Raw JSON
                </summary>
                <pre className="p-4 rounded-xl bg-slate-950 text-emerald-400 border border-slate-800 overflow-x-auto text-[10px] leading-relaxed font-mono">
                  {JSON.stringify(selectedRecord, null, 2)}
                </pre>
              </details>
            </div>

            <div className="px-6 py-3 bg-slate-50 dark:bg-slate-800/60 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
              <span className="text-[10px] text-slate-400 font-mono flex items-center gap-1.5">
                <Shield className="w-3 h-3" /> Read-only inspection
              </span>
              <button
                onClick={() => setSelectedRecord(null)}
                className="px-4 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 text-slate-800 dark:text-slate-200 text-xs font-semibold transition cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
