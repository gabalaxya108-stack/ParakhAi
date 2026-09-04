import React, { useEffect, useState } from "react";
import {
  FileWarning,
  CheckCircle2,
  Clock,
  Send,
  AlertTriangle,
  Search,
  Filter,
  RefreshCw,
  ExternalLink,
  Shield,
  FileText
} from "lucide-react";
import { fetchJson } from "../api/client";

interface ComplaintItem {
  id: number;
  complaint_id: string;
  inspection_id: string;
  product_name: string | null;
  manufacturer_name: string | null;
  commodity_category: string;
  status: string;
  statutory_provisions: string | null;
  violations_json: any;
  enforcement_notes: string | null;
  created_at: string;
  updated_at: string;
}

interface ComplaintQueuePageProps {
  onSelectInspection?: (inspectionId: string) => void;
}

export const ComplaintQueuePage: React.FC<ComplaintQueuePageProps> = ({ onSelectInspection }) => {
  const [complaints, setComplaints] = useState<ComplaintItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [actionModalItem, setActionModalItem] = useState<ComplaintItem | null>(null);
  const [actionNotes, setActionNotes] = useState("");
  const [updating, setUpdating] = useState(false);

  const fetchComplaints = async () => {
    try {
      setLoading(true);
      const data = await fetchJson<ComplaintItem[]>("/complaints");
      setComplaints(data || []);
    } catch (err) {
      console.error("Failed to load complaints:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplaints();
  }, []);

  const handleUpdateStatus = async (newStatus: string) => {
    if (!actionModalItem) return;
    try {
      setUpdating(true);
      const updated = await fetchJson<ComplaintItem>("/complaints/" + actionModalItem.complaint_id + "/status", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_status: newStatus, notes: actionNotes })
      });
      setComplaints((prev) => prev.map((c) => (c.complaint_id === updated.complaint_id ? updated : c)));
      setActionModalItem(null);
      setActionNotes("");
    } catch (err) {
      console.error("Failed to update status:", err);
    } finally {
      setUpdating(false);
    }
  };

  const filtered = complaints.filter((c) => {
    if (statusFilter !== "ALL" && c.status !== statusFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchName = (c.product_name || "").toLowerCase().includes(q);
      const matchMfg = (c.manufacturer_name || "").toLowerCase().includes(q);
      const matchId = c.complaint_id.toLowerCase().includes(q);
      const matchInsp = c.inspection_id.toLowerCase().includes(q);
      return matchName || matchMfg || matchId || matchInsp;
    }
    return true;
  });

  const pendingCount = complaints.filter((c) => c.status === "PENDING_NOTICE").length;
  const issuedCount = complaints.filter((c) => c.status === "NOTICE_ISSUED").length;
  const closedCount = complaints.filter((c) => c.status === "CLOSED").length;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-400">
              <FileWarning className="w-5 h-5" />
            </span>
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
              Statutory Enforcement & Complaint Queue
            </h1>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
            Official docket of verified non-compliant packaged commodities forwarded for Legal Metrology Act prosecution and Section 39 notices.
          </p>
        </div>

        <button
          onClick={fetchComplaints}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold border border-slate-300 dark:border-slate-700 transition cursor-pointer self-start sm:self-auto"
        >
          <RefreshCw className={"w-3.5 h-3.5 " + (loading ? "animate-spin" : "")} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Metric Cards Ribbon */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
        <div
          onClick={() => setStatusFilter("ALL")}
          className={"p-3.5 rounded-xl border transition cursor-pointer " + (statusFilter === "ALL" ? "bg-blue-50/60 border-blue-300 dark:bg-blue-950/40 dark:border-blue-800 shadow-xs" : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300")}
        >
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">Total Registered</span>
          <span className="text-2xl font-bold text-slate-900 dark:text-white">{complaints.length}</span>
        </div>

        <div
          onClick={() => setStatusFilter("PENDING_NOTICE")}
          className={"p-3.5 rounded-xl border transition cursor-pointer " + (statusFilter === "PENDING_NOTICE" ? "bg-rose-50/60 border-rose-300 dark:bg-rose-950/40 dark:border-rose-800 shadow-xs" : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300")}
        >
          <span className="text-[11px] font-bold text-rose-700 dark:text-rose-400 uppercase tracking-wider block">Pending Statutory Notice</span>
          <span className="text-2xl font-bold text-rose-700 dark:text-rose-400">{pendingCount}</span>
        </div>

        <div
          onClick={() => setStatusFilter("NOTICE_ISSUED")}
          className={"p-3.5 rounded-xl border transition cursor-pointer " + (statusFilter === "NOTICE_ISSUED" ? "bg-amber-50/60 border-amber-300 dark:bg-amber-950/40 dark:border-amber-800 shadow-xs" : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300")}
        >
          <span className="text-[11px] font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wider block">Notice Issued (Reply Awaited)</span>
          <span className="text-2xl font-bold text-amber-700 dark:text-amber-400">{issuedCount}</span>
        </div>

        <div
          onClick={() => setStatusFilter("CLOSED")}
          className={"p-3.5 rounded-xl border transition cursor-pointer " + (statusFilter === "CLOSED" ? "bg-emerald-50/60 border-emerald-300 dark:bg-emerald-950/40 dark:border-emerald-800 shadow-xs" : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300")}
        >
          <span className="text-[11px] font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider block">Compounded / Closed</span>
          <span className="text-2xl font-bold text-emerald-700 dark:text-emerald-400">{closedCount}</span>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white dark:bg-slate-900 p-3 rounded-xl border border-slate-200 dark:border-slate-800">
        <div className="relative w-full sm:w-80">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by product, manufacturer, CMP ID..."
            className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-hidden focus:ring-2 focus:ring-blue-600"
          />
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span>Showing {filtered.length} cases</span>
        </div>
      </div>

      {/* Complaints List */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-500">Loading enforcement cases...</div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 space-y-2">
          <Shield className="w-8 h-8 text-slate-400 mx-auto" />
          <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">No enforcement cases matching filter</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((item) => (
            <div
              key={item.complaint_id}
              className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-4 shadow-xs space-y-3 transition hover:border-slate-300 dark:hover:border-slate-700"
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-blue-900 dark:text-blue-300 px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-900">
                      {item.complaint_id}
                    </span>
                    <span className={"text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider " + (item.status === "PENDING_NOTICE" ? "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300" : item.status === "NOTICE_ISSUED" ? "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300" : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300")}>
                      {item.status.replace("_", " ")}
                    </span>
                    <span className="text-xs text-slate-400">• Registered {new Date(item.created_at).toLocaleDateString()}</span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                    {item.product_name || "Packaged Commodity"}
                  </h3>
                  <p className="text-xs text-slate-600 dark:text-slate-400">
                    Manufacturer/Packer: <span className="font-semibold text-slate-800 dark:text-slate-200">{item.manufacturer_name || "Unidentified / Missing on Label"}</span>
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  {onSelectInspection && (
                    <button
                      onClick={() => onSelectInspection(item.inspection_id)}
                      className="px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>View Dossier</span>
                    </button>
                  )}

                  <button
                    onClick={() => setActionModalItem(item)}
                    className="px-3 py-1.5 rounded-lg bg-blue-700 hover:bg-blue-800 text-white text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>Update Status</span>
                  </button>
                </div>
              </div>

              {/* Statutory Provisions & Violations */}
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 text-xs space-y-1.5">
                <div className="flex items-center gap-1.5 font-semibold text-slate-700 dark:text-slate-300">
                  <Shield className="w-3.5 h-3.5 text-blue-700" />
                  <span>Statutory Ground: {item.statutory_provisions || "Rule 6, Legal Metrology Rules, 2011"}</span>
                </div>
                {item.enforcement_notes && (
                  <p className="text-[11px] text-slate-600 dark:text-slate-400 italic">
                    Inspector Notes: {item.enforcement_notes}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Enforcement Status Action Modal */}
      {actionModalItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 w-full max-w-lg p-6 space-y-4">
            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <FileWarning className="w-4 h-4 text-rose-600" />
              <span>Update Enforcement Status for {actionModalItem.complaint_id}</span>
            </h3>

            <p className="text-xs text-slate-600 dark:text-slate-400">
              Commodity: <span className="font-semibold text-slate-800 dark:text-slate-200">{actionModalItem.product_name}</span>
            </p>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">New Enforcement Action</label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => handleUpdateStatus("NOTICE_ISSUED")}
                  disabled={updating}
                  className="px-3 py-2 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-semibold text-xs transition cursor-pointer"
                >
                  Issue Notice (Sec 39)
                </button>
                <button
                  type="button"
                  onClick={() => handleUpdateStatus("HEARING_SCHEDULED")}
                  disabled={updating}
                  className="px-3 py-2 rounded-lg bg-blue-700 hover:bg-blue-800 text-white font-semibold text-xs transition cursor-pointer"
                >
                  Schedule Hearing
                </button>
                <button
                  type="button"
                  onClick={() => handleUpdateStatus("CLOSED")}
                  disabled={updating}
                  className="px-3 py-2 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-xs transition cursor-pointer"
                >
                  Compound / Close
                </button>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Enforcement Record Notes</label>
              <textarea
                value={actionNotes}
                onChange={(e) => setActionNotes(e.target.value)}
                placeholder="Enter dispatch reference, speed post tracking ID, hearing date, or compounding fee details..."
                rows={3}
                className="w-full p-2.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-hidden focus:ring-2 focus:ring-blue-600"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setActionModalItem(null)}
                className="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold transition cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
