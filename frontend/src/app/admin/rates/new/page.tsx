'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, AlertCircle, Loader2, DollarSign } from 'lucide-react';
import { Layout } from '@/components/Layout';
import api from '@/lib/api';

export default function NewRateCardPage() {
  const router = useRouter();
  const [form, setForm] = useState({ name:'', order_type:'b2c', zone_type:'INTRA_ZONE' });
  const [error, setError] = useState(''); const [loading, setLoading] = useState(false);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(''); setLoading(true);
    try { await api.post('/admin/rate-cards', form); router.push('/admin/rates'); }
    catch (err:any) { const d=err.response?.data?.detail; setError(typeof d==='string'?d:Array.isArray(d)?d.map((x:any)=>x.msg).join(', '):'Failed to create rate card'); }
    finally { setLoading(false); }
  };
  return <Layout><div className="max-w-2xl mx-auto space-y-6"><Link href="/admin/rates" className="inline-flex items-center text-gray-500"><ArrowLeft className="h-5 w-5 mr-1"/>Back to Rates</Link><div><h1 className="text-2xl font-bold text-gray-900">Create Rate Card</h1><p className="text-gray-600 mt-1">Configure a pricing card for an order and zone type.</p></div><form onSubmit={submit} className="bg-white rounded-xl border shadow-sm p-6 space-y-5">{error&&<div className="p-3 rounded-lg bg-red-50 text-red-700 flex items-center"><AlertCircle className="h-5 w-5 mr-2"/>{error}</div>}<div><label className="block text-sm font-medium mb-1 text-gray-700">Name *</label><input required value={form.name} onChange={e=>setForm({...form,name:e.target.value})} className="w-full px-3 py-2 border rounded-lg text-gray-900" placeholder="B2C Standard"/></div><div><label className="block text-sm font-medium mb-1 text-gray-700">Order Type *</label><select value={form.order_type} onChange={e=>setForm({...form,order_type:e.target.value})} className="w-full px-3 py-2 border rounded-lg text-gray-900"><option value="b2c">B2C</option><option value="b2b">B2B</option></select></div><div><label className="block text-sm font-medium mb-1 text-gray-700">Zone Type *</label><select value={form.zone_type} onChange={e=>setForm({...form,zone_type:e.target.value})} className="w-full px-3 py-2 border rounded-lg text-gray-900"><option value="INTRA_ZONE">Intra Zone</option><option value="INTER_ZONE">Inter Zone</option><option value="INTRA_CITY">Intra City</option><option value="INTER_CITY">Inter City</option></select></div><div className="flex justify-end gap-3"><Link href="/admin/rates" className="px-4 py-2 border rounded-lg">Cancel</Link><button disabled={loading} className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg disabled:opacity-60">{loading?<Loader2 className="h-4 w-4 mr-2 animate-spin"/>:<DollarSign className="h-4 w-4 mr-2"/>}{loading?'Creating...':'Create Rate Card'}</button></div></form></div></Layout>;
}
