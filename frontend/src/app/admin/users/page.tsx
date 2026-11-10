'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { api, AdminUserRecord } from '@/lib/api';
import { AdminPageShell } from '@/components/admin/AdminPageShell';
import {
  Users,
  UserPlus,
  UserCog,
  ShieldPlus,
  ShieldCheck,
  Crown,
  Trash2,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Search,
} from 'lucide-react';

function fmtTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function AdminUsersPage() {
  const { user, token } = useAuth();
  const [users, setUsers] = useState<AdminUserRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState('');
  const [actionMsg, setActionMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<'ALL' | 'admin' | 'user'>('ALL');

  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'user',
    preferred_language: 'en',
  });
  const [createLoading, setCreateLoading] = useState(false);

  const fetchUsers = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await api.getAdminUsers(token);
      setUsers(data);
      setLastRefreshed(new Date().toLocaleTimeString());
    } catch (e: any) {
      setActionMsg({ type: 'error', text: e.message || 'Failed to fetch users' });
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  useEffect(() => {
    if (!actionMsg) return;
    const t = setTimeout(() => setActionMsg(null), 5000);
    return () => clearTimeout(t);
  }, [actionMsg]);

  const handleDeleteUser = async (userId: string, email: string) => {
    if (!token) return;
    if (!confirm(`Permanently delete user "${email}" and all their medical data? This cannot be undone.`)) return;
    try {
      await api.deleteAdminUser(token, userId);
      setActionMsg({ type: 'success', text: `User "${email}" deleted successfully.` });
      fetchUsers();
    } catch (e: any) {
      setActionMsg({ type: 'error', text: e.message || 'Delete failed' });
    }
  };

  const handleToggleRole = async (userId: string, currentRole: string, email: string) => {
    if (!token) return;
    const newRole: 'user' | 'admin' = currentRole === 'admin' ? 'user' : 'admin';
    if (!confirm(`Change "${email}" from ${currentRole} → ${newRole}?`)) return;
    try {
      await api.updateAdminUserRole(token, userId, newRole);
      setActionMsg({ type: 'success', text: `"${email}" is now a ${newRole}.` });
      fetchUsers();
    } catch (e: any) {
      setActionMsg({ type: 'error', text: e.message || 'Role update failed' });
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    setCreateLoading(true);
    try {
      await api.createAdminUser(token, createForm);
      setActionMsg({ type: 'success', text: `User "${createForm.email}" created as ${createForm.role}.` });
      setShowCreateForm(false);
      setCreateForm({ email: '', password: '', full_name: '', role: 'user', preferred_language: 'en' });
      fetchUsers();
    } catch (e: any) {
      setActionMsg({ type: 'error', text: e.message || 'Create user failed' });
    } finally {
      setCreateLoading(false);
    }
  };

  const filteredUsers = users.filter((u) => {
    const matchesRole = roleFilter === 'ALL' || u.role === roleFilter;
    const q = searchQuery.trim().toLowerCase();
    const matchesSearch =
      !q ||
      u.email.toLowerCase().includes(q) ||
      (u.full_name || '').toLowerCase().includes(q);
    return matchesRole && matchesSearch;
  });

  const adminCount = users.filter((u) => u.role === 'admin').length;
  const standardCount = users.filter((u) => u.role === 'user').length;

  return (
    <AdminPageShell
      title="User Accounts Management"
      breadcrumb="User Management"
      description="Create new user or administrator accounts, promote or demote roles, and permanently remove accounts without exposing clinical records."
      badgeText="Role-Based Access Control (RBAC)"
      lastRefreshed={lastRefreshed}
      actions={
        <div className="flex gap-2">
          <button
            onClick={fetchUsers}
            disabled={loading}
            className="px-3 py-2 rounded-xl bg-slate-800 border border-white/10 text-white text-xs font-semibold flex items-center gap-2 hover:bg-slate-700 transition disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-purple-500/20 transition"
          >
            <UserPlus className="h-3.5 w-3.5" />
            Add User / Admin
          </button>
        </div>
      }
    >
      {/* Action Feedback Banner */}
      {actionMsg && (
        <div
          className={`p-3 rounded-2xl text-xs flex items-center gap-3 border ${
            actionMsg.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
        >
          {actionMsg.type === 'success' ? (
            <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
          ) : (
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
          )}
          <span>{actionMsg.text}</span>
        </div>
      )}

      {/* Summary Badges */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="glass-card p-4 rounded-2xl border border-white/10 space-y-1">
          <p className="text-[11px] text-slate-400">Total Registered Accounts</p>
          <p className="text-2xl font-extrabold text-white">{users.length}</p>
        </div>
        <div className="glass-card p-4 rounded-2xl border border-white/10 space-y-1">
          <p className="text-[11px] text-slate-400">Administrators</p>
          <p className="text-2xl font-extrabold text-purple-400">{adminCount}</p>
        </div>
        <div className="glass-card p-4 rounded-2xl border border-white/10 space-y-1">
          <p className="text-[11px] text-slate-400">Standard Users (Patients)</p>
          <p className="text-2xl font-extrabold text-blue-400">{standardCount}</p>
        </div>
      </div>

      {/* Create User Form */}
      {showCreateForm && (
        <div className="glass-card p-6 rounded-2xl border border-purple-500/30 bg-purple-950/10 space-y-4">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <UserPlus className="h-4 w-4 text-purple-400" />
            Create New User Account
          </h2>
          <form onSubmit={handleCreateUser} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-1">
              <label className="text-[11px] text-slate-400 font-medium uppercase tracking-wider">Email *</label>
              <input
                required
                type="email"
                value={createForm.email}
                onChange={(e) => setCreateForm((f) => ({ ...f, email: e.target.value }))}
                placeholder="user@example.com"
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-400"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[11px] text-slate-400 font-medium uppercase tracking-wider">Password *</label>
              <input
                required
                type="password"
                minLength={6}
                value={createForm.password}
                onChange={(e) => setCreateForm((f) => ({ ...f, password: e.target.value }))}
                placeholder="Min. 6 characters"
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-400"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[11px] text-slate-400 font-medium uppercase tracking-wider">Full Name</label>
              <input
                type="text"
                value={createForm.full_name}
                onChange={(e) => setCreateForm((f) => ({ ...f, full_name: e.target.value }))}
                placeholder="Optional"
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-400"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[11px] text-slate-400 font-medium uppercase tracking-wider">Role *</label>
              <select
                value={createForm.role}
                onChange={(e) => setCreateForm((f) => ({ ...f, role: e.target.value }))}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-400"
              >
                <option value="user">User (Patient)</option>
                <option value="admin">Admin (System Manager)</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-[11px] text-slate-400 font-medium uppercase tracking-wider">Language</label>
              <select
                value={createForm.preferred_language}
                onChange={(e) => setCreateForm((f) => ({ ...f, preferred_language: e.target.value }))}
                className="w-full bg-slate-900 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-purple-400"
              >
                <option value="en">English</option>
                <option value="ta">Tamil</option>
                <option value="hi">Hindi</option>
              </select>
            </div>
            <div className="flex items-end gap-2">
              <button
                type="submit"
                disabled={createLoading}
                className="flex-1 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold flex items-center justify-center gap-2 transition disabled:opacity-50"
              >
                {createLoading ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <UserPlus className="h-3.5 w-3.5" />}
                {createLoading ? 'Creating...' : 'Create Account'}
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-3 py-2 rounded-xl bg-slate-800 border border-white/10 text-slate-400 text-xs hover:text-white transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Search & Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <UserCog className="h-4 w-4 text-purple-400" />
          <span>Showing {filteredUsers.length} of {users.length} accounts</span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search className="h-3.5 w-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search email or name..."
              className="bg-slate-900 border border-white/10 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white focus:outline-none focus:border-purple-400"
            />
          </div>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value as 'ALL' | 'admin' | 'user')}
            className="bg-slate-900 border border-white/10 text-xs text-white rounded-xl px-3 py-1.5 focus:outline-none focus:border-purple-400"
          >
            <option value="ALL">All Roles</option>
            <option value="admin">Admins Only</option>
            <option value="user">Users Only</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="glass-card rounded-2xl border border-white/10 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-white/5 text-[10px] uppercase tracking-wider text-slate-400 border-b border-white/10">
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Language</th>
                <th className="py-3 px-4">Registered</th>
                <th className="py-3 px-4">Last Sign In</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading && users.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-10 text-center text-slate-400 text-xs">
                    <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-purple-400" />
                    Loading users...
                  </td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-10 text-center text-slate-400 text-xs">
                    No users found.
                  </td>
                </tr>
              ) : (
                filteredUsers.map((u) => (
                  <tr key={u.id} className="hover:bg-white/[0.02] transition">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2.5">
                        <div className="h-7 w-7 rounded-full bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-300 text-[10px] font-bold flex-shrink-0">
                          {(u.full_name || u.email).charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="font-semibold text-white">{u.full_name || '—'}</p>
                          <p className="text-[10px] text-slate-400 font-mono">{u.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      {u.role === 'admin' ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 text-[10px] font-bold">
                          <Crown className="h-3 w-3" /> Admin
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-300 border border-blue-500/20 text-[10px] font-bold">
                          <Users className="h-3 w-3" /> User
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-mono">
                      {{ en: '🇬🇧 English', ta: '🇮🇳 Tamil', hi: '🇮🇳 Hindi' }[u.preferred_language] || u.preferred_language}
                    </td>
                    <td className="py-3 px-4 text-slate-400 font-mono text-[10px]">{fmtTime(u.created_at)}</td>
                    <td className="py-3 px-4 text-slate-400 font-mono text-[10px]">{fmtTime(u.last_sign_in_at)}</td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                          u.is_active
                            ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                            : 'bg-slate-500/10 text-slate-400 border-slate-500/30'
                        }`}
                      >
                        {u.is_active ? 'Active' : 'Suspended'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleToggleRole(u.id, u.role, u.email)}
                          title={u.role === 'admin' ? 'Demote to User' : 'Promote to Admin'}
                          className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400 hover:bg-purple-500/20 transition"
                        >
                          {u.role === 'admin' ? <Users className="h-3.5 w-3.5" /> : <ShieldPlus className="h-3.5 w-3.5" />}
                        </button>
                        {u.id !== user?.id && (
                          <button
                            onClick={() => handleDeleteUser(u.id, u.email)}
                            title="Delete User"
                            className="p-1.5 rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <p className="text-[11px] text-slate-500 text-center">
        <ShieldCheck className="h-3 w-3 inline mr-1 text-emerald-500" />
        Deleting a user permanently removes all their medical reports, lab results, prescriptions, and conversation history via cascaded database deletion.
      </p>
    </AdminPageShell>
  );
}

