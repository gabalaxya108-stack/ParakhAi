import { API_BASE_URL } from './client';
export interface AuditLogItem {
  id: number;
  inspection_id?: number | null;
  user_id?: number | null;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  change_details?: any;
  ip_address?: string | null;
  timestamp: string;
}

export interface UserRecord {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: string;
  created_at: string;
}

export const adminApi = {
  getAuditLogs: async (role: string = 'SUPERVISOR', limit: number = 50): Promise<AuditLogItem[]> => {
    const res = await fetch(`${API_BASE_URL}/admin/audit-logs?limit=${limit}`, {
      headers: { 'X-User-Role': role },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Access denied (${res.status})`);
    }
    return res.json();
  },

  getUsers: async (role: string = 'ADMIN'): Promise<UserRecord[]> => {
    const res = await fetch(`${API_BASE_URL}/admin/users`, {
      headers: { 'X-User-Role': role },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Access denied (${res.status})`);
    }
    return res.json();
  },

  createUser: async (
    userData: { username: string; email: string; full_name: string; role: string },
    role: string = 'ADMIN'
  ): Promise<UserRecord> => {
    const res = await fetch(`${API_BASE_URL}/admin/users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Role': role,
      },
      body: JSON.stringify(userData),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to create user (${res.status})`);
    }
    return res.json();
  },
};
