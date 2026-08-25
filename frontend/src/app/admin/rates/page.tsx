'use client';

import { useEffect, useMemo, useState } from 'react';
import { Layout } from '@/components/Layout';
import { DollarSign, Plus, Search, Loader2 } from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api';

interface RateCard { id: string; name: string; order_type: string; zone_type: string; is_active: boolean; effective_from: string; effective_to?: string | null; }

export default function AdminRatesPage() {
  const [rates, setRates] = useState<RateCard[]>([]); const [search, setSearch] = useState(''); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  useEffect(() => { api.get('/admin/rate-cards').then(r=>setRates(r.data||[])).catch((e:any)=>setError(e.response?.data?.detail||'Failed to load rate cards')).finally(()=>setLoading(false)); }, []);
  const filtered = useMemo(() => rates.filter(r => `${r.name} ${r.order_type} ${r.zone_type}`.toLowerCase().includes(search.toLowerCase())), [rates, search]);
  return <Layout><div className="space-y-6">
    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4"><div><h1 className="text-2xl font-bold text-gray-900">Rate Management</h1><p className="text-gray-600">Configure rate cards and pricing rules</p></div><Link href="/admin/rates/new" className="inline-flex items-center px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700"><Plus className="h-5 w-5 mr-2"/>Add Rate Card</Link></div>
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6"><div className="relative mb-6"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400"/><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search rate cards..." className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-gray-900"/></div>
      {error && <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700">{error}</div>}
      {loading ? <div className="py-12 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600"/></div> : filtered.length === 0 ? <div className="text-center py-12"><DollarSign className="h-16 w-16 mx-auto text-gray-300 mb-4"/><p className="text-gray-500 text-lg">No rate cards configured</p><p className="text-gray-400 mt-1">Create rate cards to define pricing for different order types and zones</p></div> : <div className="overflow-x-auto"><table className="w-full"><thead><tr className="border-b text-left text-xs text-gray-500 uppercase"><th className="px-4 py-3">Name</th><th className="px-4 py-3">Order Type</th><th className="px-4 py-3">Zone Type</th><th className="px-4 py-3">Status</th></tr></thead><tbody className="divide-y">{filtered.map(r=><tr key={r.id}><td className="px-4 py-4 font-medium text-gray-900">{r.name}</td><td className="px-4 py-4 text-gray-700">{r.order_type}</td><td className="px-4 py-4 text-gray-700">{r.zone_type}</td><td className="px-4 py-4"><span className={`px-2 py-1 rounded-full text-xs ${r.is_active?'bg-green-100 text-green-800':'bg-gray-100 text-gray-700'}`}>{r.is_active?'Active':'Inactive'}</span></td></tr>)}</tbody></table></div>}
    </div></div></Layout>;
}
