'use client';

import { useEffect, useMemo, useState } from 'react';
import { Layout } from '@/components/Layout';
import { Users, Plus, Search, Loader2 } from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api';

interface Agent { id: string; employee_id: string; status: string; max_concurrent_deliveries: number; current_deliveries_count: number; is_active: boolean; user_name?: string; user_email?: string; user_phone?: string; }

export default function AdminAgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]); const [search, setSearch] = useState(''); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  const load = async () => { setLoading(true); setError(''); try { const r = await api.get('/agents?limit=100'); setAgents(r.data || []); } catch (e: any) { setError(e.response?.data?.detail || 'Failed to load agents'); } finally { setLoading(false); } };
  useEffect(() => { load(); }, []);
  const filtered = useMemo(() => agents.filter(a => `${a.employee_id} ${a.user_name || ''} ${a.user_email || ''}`.toLowerCase().includes(search.toLowerCase())), [agents, search]);
  return <Layout><div className="space-y-6">
    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4"><div><h1 className="text-2xl font-bold text-gray-900">Agent Management</h1><p className="text-gray-600">Manage delivery agents and their assignments</p></div><Link href="/admin/agents/new" className="inline-flex items-center px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700"><Plus className="h-5 w-5 mr-2"/>Add Agent</Link></div>
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6"><div className="relative mb-6"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400"/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search agents..." className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-gray-900"/></div>
      {error && <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700">{error}</div>}
      {loading ? <div className="py-12 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600"/></div> : filtered.length === 0 ? <div className="text-center py-12"><Users className="h-16 w-16 mx-auto text-gray-300 mb-4"/><p className="text-gray-500 text-lg">No agents found</p><p className="text-gray-400 mt-1">Agents must be provisioned by an administrator.</p></div> : <div className="overflow-x-auto"><table className="w-full"><thead><tr className="border-b text-left text-xs text-gray-500 uppercase"><th className="px-4 py-3">Agent</th><th className="px-4 py-3">Employee ID</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Capacity</th></tr></thead><tbody className="divide-y">{filtered.map(a=><tr key={a.id}><td className="px-4 py-4"><div className="font-medium text-gray-900">{a.user_name || 'Unnamed'}</div><div className="text-sm text-gray-500">{a.user_email || '—'}</div></td><td className="px-4 py-4 text-gray-700">{a.employee_id}</td><td className="px-4 py-4"><span className="px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700">{a.status}</span></td><td className="px-4 py-4 text-gray-700">{a.current_deliveries_count}/{a.max_concurrent_deliveries}</td></tr>)}</tbody></table></div>}
    </div></div></Layout>;
}
