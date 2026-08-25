'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, AlertCircle, Loader2, UserPlus } from 'lucide-react';
import { Layout } from '@/components/Layout';
import api from '@/lib/api';

interface Zone { id: string; name: string; code: string; }

export default function NewAgentPage() {
  const router = useRouter();
  const [zones, setZones] = useState<Zone[]>([]);
  const [form, setForm] = useState({ email:'', password:'', full_name:'', phone:'', employee_id:'', zone_id:'', max_concurrent_deliveries:3 });
  const [error, setError] = useState(''); const [loading, setLoading] = useState(false); const [loadingZones, setLoadingZones] = useState(true);

  useEffect(() => { api.get('/admin/zones').then(r=>setZones(r.data||[])).catch(()=>{}).finally(()=>setLoadingZones(false)); }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(''); setLoading(true);
    try {
      // Public registration always creates CUSTOMER accounts. This page therefore
      // provisions the account as an agent using the protected admin endpoint.
      const userRes = await api.post('/admin/agents', { email: form.email, password: form.password, full_name: form.full_name, phone: form.phone || null });
      const userId = userRes.data?.user_id || userRes.data?.id;
      if (!userId) throw new Error('Agent account was created but no user ID was returned');
      await api.post('/admin/agents/profile', { user_id: userId, employee_id: form.employee_id, zone_id: form.zone_id || null, max_concurrent_deliveries: form.max_concurrent_deliveries });
      router.push('/admin/agents');
    } catch (err: any) {
      const d = err.response?.data?.detail;
      setError(typeof d === 'string' ? d : Array.isArray(d) ? d.map((x:any)=>x.msg).join(', ') : 'Failed to create agent');
    } finally { setLoading(false); }
  };

  return <Layout><div className="max-w-2xl mx-auto space-y-6">
    <Link href="/admin/agents" className="inline-flex items-center text-gray-500 hover:text-gray-700"><ArrowLeft className="h-5 w-5 mr-1"/>Back to Agents</Link>
    <div><h1 className="text-2xl font-bold text-gray-900">Add Agent</h1><p className="text-gray-600 mt-1">Provision an agent account from the admin panel.</p></div>
    <form onSubmit={submit} className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 space-y-5">
      {error && <div className="flex items-start p-3 rounded-lg bg-red-50 text-red-700"><AlertCircle className="h-5 w-5 mr-2"/>{error}</div>}
      <div className="grid md:grid-cols-2 gap-4">
        <div><label className="block text-sm font-medium mb-1 text-gray-700">Full Name *</label><input required value={form.full_name} onChange={e=>setForm({...form,full_name:e.target.value})} className="w-full px-3 py-2 border rounded-lg text-gray-900"/></div>
        <div><label className="block text-sm font-medium mb-1 text-gray-700">Employee ID *</label><input required value={form.employee_id} onChange={e=>setForm({...form,employee_id:e.target.value})} className="w-full px-3 py-2 border rounded-lg text-gray-900" placeholder="AG-001"/></div>
        <div><label className="block text-sm font-medium mb-1 text-gray-700">Email *</label><input required type="email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} className="w-full px-3 py-2 border rounded-lg text-gray-900"/></div>
        <div><label className="block text-sm font-medium mb-1 text-gray-700">Temporary Password *</label><input required minLength={8} type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})} className="w-full px-3 py-2 border rounded-lg text-gray-900"/></div>
        <div><label className="block text-sm font-medium mb-1 text-gray-700">Phone</label><input value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})} className="w-full px-3 py-2 border rounded-lg text-gray-900"/></div>
        <div><label className="block text-sm font-medium mb-1 text-gray-700">Zone</label><select value={form.zone_id} onChange={e=>setForm({...form,zone_id:e.target.value})} disabled={loadingZones} className="w-full px-3 py-2 border rounded-lg text-gray-900"><option value="">No zone</option>{zones.map(z=><option key={z.id} value={z.id}>{z.code} — {z.name}</option>)}</select></div>
        <div><label className="block text-sm font-medium mb-1 text-gray-700">Max Concurrent Deliveries</label><input type="number" min={1} max={10} value={form.max_concurrent_deliveries} onChange={e=>setForm({...form,max_concurrent_deliveries:Number(e.target.value)})} className="w-full px-3 py-2 border rounded-lg text-gray-900"/></div>
      </div>
      <div className="flex justify-end gap-3"><Link href="/admin/agents" className="px-4 py-2 border rounded-lg">Cancel</Link><button disabled={loading} className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg disabled:opacity-60">{loading?<Loader2 className="h-4 w-4 mr-2 animate-spin"/>:<UserPlus className="h-4 w-4 mr-2"/>}{loading?'Creating...':'Create Agent'}</button></div>
    </form>
  </div></Layout>;
}
