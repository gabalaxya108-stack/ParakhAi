import React, { useEffect, useState } from 'react';
import {
  Shield,
  Users,
  FileClock,
  KeyRound,
  UserPlus,
  Lock,
  CheckCircle2,
  AlertOctagon,
  RefreshCw
} from 'lucide-react';
import { adminApi, AuditLogItem, UserRecord } from '../api/admin';
import { Badge } from '../components/ui/Badge';
import { Card } from '../components/ui/Card';

interface AdminPortalPageProps {
  currentRole: 'INSPECTOR' | 'SUPERVISOR' | 'ADMIN';
}

export const AdminPortalPage: React.FC<AdminPortalPageProps> = ({ currentRole }) => {
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [users, setUsers] = useState<UserRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // New user form state
  const [showAddUser, setShowAddUser] = useState<boolean>(false);
  const [newUsername, setNewUsername] = useState<string>('');
  const [newEmail, setNewEmail] = useState<string>('');
  const [newFullName, setNewFullName] = useState<string>('');
  const [newUserRole, setNewUserRole] = useState<string>('INSPECTOR');
  const [creatingUser, setCreatingUser] = useState<boolean>(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const loadPortalData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch audit logs (Supervisor or Admin)
      const logs = await adminApi.getAuditLogs(currentRole, 50);
      setAuditLogs(logs);

      // Fetch users (Admin only)
      if (currentRole === 'ADMIN') {
        const uList = await adminApi.getUsers(currentRole);
        setUsers(uList);
      } else {
        setUsers([]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load administrative data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPortalData();
  }, [currentRole]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCreatingUser(true);
      setError(null);
      const created = await adminApi.createUser(
        {
          username: newUsername.trim(),
          email: newEmail.trim(),
          full_name: newFullName.trim(),
          role: newUserRole,
        },
        currentRole
      );
      setUsers((prev) => [...prev, created]);
      setNewUsername('');
      setNewEmail('');
      setNewFullName('');
      setShowAddUser(false);
      setSuccessMsg(`User '${created.username}' provisioned with role '${created.role}'.`);
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'User creation failed');
    } finally {
      setCreatingUser(false);
    }
  };

  const isSupervisorOrAdmin = currentRole === 'SUPERVISOR' || currentRole === 'ADMIN';
  const isAdmin = currentRole === 'ADMIN';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Administration & Regulatory Audit Trail
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            System audit trail of enforcement actions and role-based privilege management for Legal Metrology officers.
          </p>
        </div>

        <button
          onClick={loadPortalData}
          disabled={loading}
          className="px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-600 text-xs font-medium transition flex items-center gap-1.5 self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-blue-600' : ''}`} />
          <span>Refresh data</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center gap-3">
          <AlertOctagon className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-center gap-3">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Role Permission Matrix Card */}
      <Card padding="md" className="space-y-4">
        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
          <KeyRound className="w-4 h-4 text-blue-600" />
          Role-Based Access Control Architecture (Microsoft Entra ID)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className={`p-4 rounded-xl border transition ${
            currentRole === 'INSPECTOR' ? 'bg-blue-50/70 border-blue-400 ring-2 ring-blue-100' : 'bg-slate-50 border-slate-200 dark:border-slate-800'
          }`}>
            <span className="font-bold text-slate-900 block">Inspector Role</span>
            <span className="text-[11px] text-blue-700 font-mono block mt-0.5">Role Level: 1</span>
            <p className="text-slate-600 mt-2 text-xs leading-relaxed">
              Authorized to upload commodity packaging, inspect OCR perceptions, screen statutory compliance, and submit official human review determinations.
            </p>
          </div>

          <div className={`p-4 rounded-xl border transition ${
            currentRole === 'SUPERVISOR' ? 'bg-blue-50/70 border-blue-400 ring-2 ring-blue-100' : 'bg-slate-50 border-slate-200 dark:border-slate-800'
          }`}>
            <span className="font-bold text-slate-900 block">Supervisor Role</span>
            <span className="text-[11px] text-blue-700 font-mono block mt-0.5">Role Level: 2</span>
            <p className="text-slate-600 mt-2 text-xs leading-relaxed">
              Enjoys full inspector privileges plus cross-jurisdictional surveillance analytics and access to the immutable system regulatory audit log.
            </p>
          </div>

          <div className={`p-4 rounded-xl border transition ${
            currentRole === 'ADMIN' ? 'bg-blue-50/70 border-blue-400 ring-2 ring-blue-100' : 'bg-slate-50 border-slate-200 dark:border-slate-800'
          }`}>
            <span className="font-bold text-slate-900 block">Administrator Role</span>
            <span className="text-[11px] text-blue-700 font-mono block mt-0.5">Role Level: 3</span>
            <p className="text-slate-600 mt-2 text-xs leading-relaxed">
              Full platform sovereignty: Manage officer identities, provision accounts, modify statutory Legal Metrology rulesets, and inspect cryptographic audit trails.
            </p>
          </div>
        </div>
      </Card>

      {/* User Management Section (Admin Only) */}
      {isAdmin ? (
        <Card padding="md" className="space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
                <Users className="w-4 h-4 text-blue-600" />
                Officer & Account Management
              </h3>
              <span className="text-xs text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">Admin privilege required</span>
            </div>

            <button
              onClick={() => setShowAddUser(!showAddUser)}
              className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold transition flex items-center gap-1.5"
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>{showAddUser ? 'Cancel' : 'Provision officer'}</span>
            </button>
          </div>

          {/* Provisioning Form */}
          {showAddUser && (
            <form onSubmit={handleCreateUser} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3 text-xs">
              <span className="font-bold text-slate-900 block">Provision New Enforcement Account</span>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <input
                  type="text"
                  required
                  placeholder="Username (e.g. inspector_mum01)"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  className="px-3 py-2 rounded-lg bg-white border border-slate-200 text-slate-900 dark:text-white"
                />
                <input
                  type="email"
                  required
                  placeholder="Email (e.g. officer@gov.in)"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  className="px-3 py-2 rounded-lg bg-white border border-slate-200 text-slate-900 dark:text-white"
                />
                <input
                  type="text"
                  required
                  placeholder="Full Name"
                  value={newFullName}
                  onChange={(e) => setNewFullName(e.target.value)}
                  className="px-3 py-2 rounded-lg bg-white border border-slate-200 text-slate-900 dark:text-white"
                />
                <select
                  value={newUserRole}
                  onChange={(e) => setNewUserRole(e.target.value)}
                  className="px-3 py-2 rounded-lg bg-white border border-slate-200 text-slate-900 dark:text-white"
                >
                  <option value="INSPECTOR">INSPECTOR</option>
                  <option value="SUPERVISOR">SUPERVISOR</option>
                  <option value="ADMIN">ADMIN</option>
                </select>
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={creatingUser}
                  className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold"
                >
                  {creatingUser ? 'Creating...' : 'Save & provision account'}
                </button>
              </div>
            </form>
          )}

          {/* Users Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 font-medium bg-slate-50 dark:bg-slate-950">
                  <th className="py-2.5 px-3">Username</th>
                  <th className="py-2.5 px-3">Full Name</th>
                  <th className="py-2.5 px-3">Email</th>
                  <th className="py-2.5 px-3">Role</th>
                  <th className="py-2.5 px-3">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/60">
                    <td className="py-2.5 px-3 font-mono text-blue-700 font-bold">{u.username}</td>
                    <td className="py-2.5 px-3 text-slate-900 font-medium">{u.full_name}</td>
                    <td className="py-2.5 px-3 text-slate-500 font-mono">{u.email}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200 dark:border-slate-800">
                        {u.role}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 font-mono text-[11px]">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 text-xs text-slate-600 flex items-center gap-3">
          <Lock className="w-4 h-4 text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500" />
          <span>User provisioning and credential administration is restricted to <strong>Administrator</strong> accounts.</span>
        </div>
      )}

      {/* Immutable Regulatory Audit Log Section */}
      <Card padding="none" className="overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-sm text-slate-900 flex items-center gap-2">
              <FileClock className="w-4 h-4 text-blue-600" />
              Cryptographic Regulatory Audit Trail
            </h3>
            <span className="text-xs text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">Chronological ledger of enforcement actions</span>
          </div>

          <span className="text-xs font-mono text-slate-500 dark:text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">
            {auditLogs.length} events logged
          </span>
        </div>

        {isSupervisorOrAdmin ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-medium">
                  <th className="py-3 px-6">Timestamp</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Entity</th>
                  <th className="py-3 px-4">Entity ID</th>
                  <th className="py-3 px-4">IP Address</th>
                  <th className="py-3 px-6">Audit Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/60">
                    <td className="py-3 px-6 text-slate-500 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-bold text-blue-700 whitespace-nowrap">
                      {log.action}
                    </td>
                    <td className="py-3 px-4 text-slate-700 font-sans">
                      {log.entity_type}
                    </td>
                    <td className="py-3 px-4 text-slate-500 truncate max-w-[120px]">
                      {log.entity_id || '—'}
                    </td>
                    <td className="py-3 px-4 text-slate-400 dark:text-slate-500 dark:text-slate-400 dark:text-slate-500">
                      {log.ip_address || '127.0.0.1'}
                    </td>
                    <td className="py-3 px-6 text-slate-600 truncate max-w-[240px] font-sans">
                      {log.change_details ? JSON.stringify(log.change_details) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-slate-500 space-y-2">
            <Lock className="w-8 h-8 text-slate-400 mx-auto" />
            <p className="text-xs">Audit log examination is restricted to <strong>Supervisor</strong> and <strong>Administrator</strong> accounts.</p>
          </div>
        )}
      </Card>
    </div>
  );
};
