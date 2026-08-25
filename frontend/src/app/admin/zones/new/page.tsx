'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, AlertCircle, Loader2, MapPin } from 'lucide-react';
import { Layout } from '@/components/Layout';
import api from '@/lib/api';

export default function NewZonePage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const getError = (err: any) => {
    const detail = err?.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) return detail.map((x: any) => x?.msg || JSON.stringify(x)).join(', ');
    if (err?.response?.status === 401) return 'Your admin session has expired. Please sign in again.';
    if (err?.response?.status === 403) return 'Only administrators can create zones.';
    if (err?.response?.status === 404) return 'The zone creation API is not available on the deployed backend.';
    if (err?.message) return err.message;
    return 'Failed to create zone';
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const zoneName = name.trim();
      const zoneCode = code.trim().toUpperCase();
      if (!zoneName || !zoneCode) {
        setError('Zone name and zone code are required.');
        return;
      }
      await api.post('/admin/zones', {
        name: zoneName,
        code: zoneCode,
        description: description.trim() || null,
      });
      router.push('/admin/zones');
    } catch (err: any) {
      setError(getError(err));
    } finally {
      setLoading(false);
    }
  };

  return <Layout><div className="max-w-2xl mx-auto space-y-6">
    <Link href="/admin/zones" className="inline-flex items-center text-gray-500 hover:text-gray-700"><ArrowLeft className="h-5 w-5 mr-1"/>Back to Zones</Link>
    <div><h1 className="text-2xl font-bold text-gray-900">Create Zone</h1><p className="text-gray-600 mt-1">Define a delivery zone and its coverage.</p></div>
    <form onSubmit={submit} className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 space-y-5">
      {error && <div className="flex items-start p-3 rounded-lg bg-red-50 text-red-700"><AlertCircle className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0"/><span>{error}</span></div>}
      <div><label className="block text-sm font-medium text-gray-700 mb-1">Zone Name *</label><input required value={name} onChange={e=>setName(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-gray-900" placeholder="North Delhi"/></div>
      <div><label className="block text-sm font-medium text-gray-700 mb-1">Zone Code *</label><input required value={code} onChange={e=>setCode(e.target.value)} className="w-full px-3 py-2 border rounded-lg text-gray-900" placeholder="NORTH"/></div>
      <div><label className="block text-sm font-medium text-gray-700 mb-1">Description</label><textarea value={description} onChange={e=>setDescription(e.target.value)} rows={3} className="w-full px-3 py-2 border rounded-lg text-gray-900" placeholder="Coverage description"/></div>
      <div className="flex justify-end gap-3"><Link href="/admin/zones" className="px-4 py-2 border rounded-lg">Cancel</Link><button disabled={loading} className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg disabled:opacity-60">{loading?<Loader2 className="h-4 w-4 mr-2 animate-spin"/>:<MapPin className="h-4 w-4 mr-2"/>}{loading?'Creating...':'Create Zone'}</button></div>
    </form>
  </div></Layout>;
}
