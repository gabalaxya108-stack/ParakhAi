import React, { useState } from "react";
import { X, Lock, User, CheckCircle2, AlertCircle } from "lucide-react";
import { fetchJson } from "../api/client";

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (user: { id: number; username: string; role: string; full_name: string }) => void;
}

export const LoginModal: React.FC<LoginModalProps> = ({ isOpen, onClose, onLoginSuccess }) => {
  const [username, setUsername] = useState("inspector.demo");
  const [password, setPassword] = useState("Parakh@123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleQuickFill = (roleUser: string) => {
    setUsername(roleUser);
    setPassword("Parakh@123");
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetchJson<any>("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), password })
      });

      if (res && res.user) {
        localStorage.setItem("parakh_token", res.access_token);
        localStorage.setItem("parakh_user", JSON.stringify(res.user));
        onLoginSuccess(res.user);
        onClose();
      }
    } catch (err: any) {
      setError(err.message || "Login failed. Please verify credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 w-full max-w-md overflow-hidden">
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg overflow-hidden flex items-center justify-center bg-white shadow-xs border border-slate-700 shrink-0">
              <img src="/logo.png" alt="PARAKH AI Logo" className="w-full h-full object-contain p-0.5" />
            </div>
            <div>
              <h2 className="text-sm font-bold tracking-tight">PARAKH AI Access Portal</h2>
              <p className="text-[11px] text-slate-400">Department of Consumer Affairs &bull; Legal Metrology</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-slate-400 hover:text-white transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900/40 space-y-2">
            <span className="text-[11px] font-bold text-blue-900 dark:text-blue-300 uppercase tracking-wider block">
              Prototype Demo Accounts (1-Click Access)
            </span>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickFill("inspector.demo")}
                className={"p-2 rounded-lg text-xs font-semibold border transition cursor-pointer text-left " + (username === "inspector.demo" ? "bg-blue-700 text-white border-blue-700 shadow-xs" : "bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-50")}
              >
                <div className="font-bold">Inspector</div>
                <div className={"text-[9px] " + (username === "inspector.demo" ? "text-blue-100" : "text-slate-500")}>Inspect + Review</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill("officer.demo")}
                className={"p-2 rounded-lg text-xs font-semibold border transition cursor-pointer text-left " + (username === "officer.demo" ? "bg-blue-700 text-white border-blue-700 shadow-xs" : "bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-50")}
              >
                <div className="font-bold">Reviewer</div>
                <div className={"text-[9px] " + (username === "officer.demo" ? "text-blue-100" : "text-slate-500")}>Queue + Evidence</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickFill("admin.demo")}
                className={"p-2 rounded-lg text-xs font-semibold border transition cursor-pointer text-left " + (username === "admin.demo" ? "bg-blue-700 text-white border-blue-700 shadow-xs" : "bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-50")}
              >
                <div className="font-bold">Admin</div>
                <div className={"text-[9px] " + (username === "admin.demo" ? "text-blue-100" : "text-slate-500")}>Rules + DB + Audit</div>
              </button>
            </div>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 italic">
              *Prototype demo credentials for technical evaluation only. Not an official government login.
            </p>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 text-xs text-rose-800 dark:text-rose-300 flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Username</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-hidden focus:ring-2 focus:ring-blue-600"
                  placeholder="e.g. inspector.demo"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-hidden focus:ring-2 focus:ring-blue-600"
                  placeholder="••••••••"
                />
              </div>
              <p className="text-[11px] text-slate-400">Demo password: Parakh@123</p>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-blue-700 hover:bg-blue-800 text-white font-semibold text-xs transition shadow-xs flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {loading ? (
                <span>Authenticating...</span>
              ) : (
                <>
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Access Platform</span>
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
