'use client';

import { useEffect, useMemo, useState } from 'react';
import { Layout } from '@/components/Layout';
import { MapPin, Plus, Search, Loader2, RefreshCw } from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api';

interface Zone { id: string; name: string; code: string; description?: string | null; is_active: boolean; }

function errorMessage(err: any) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((x: any) => x?.msg || JSON.stringify(x)).join(', ');
  if (err?.response?.status === 401) return 'Admin session expired. Please sign in again.';
  if (err?.response?.status === 403) return 'You do not have administrator permission.';
  if (err?.response?.status === 404) return 'Zone API was not found on the deployed backend. Redeploy the latest backend commit.';
  return err?.message || 'Failed to load zones';
}

export default function AdminZonesPage() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get<Zone[]>('/admin/zones', { params: { limit: 1000 } });
      setZones(Array.isArray(response.data) ? response.data : []);
    } catch (err: any) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = useMemo(
    () => zones.filter(z => `${z.name} ${z.code} ${z.description || ''}`.toLowerCase().includes(search.toLowerCase())),
    [zones, search]
  );

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Zone Management</h1>
            <p className="text-gray-600">Manage delivery zones and their coverage areas</p>
          </div>
          <Link href="/admin/zones/new" className="inline-flex items-center px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700">
            <Plus className="h-5 w-5 mr-2" /> Add Zone
          </Link>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="relative mb-6">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search zones..." className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-gray-900" />
          </div>

          {error && (
            <div className="mb-4 p-4 rounded-lg bg-red-50 border border-red-100 text-red-700 flex items-center justify-between gap-4">
              <span>{error}</span>
              <button onClick={load} className="inline-flex items-center px-3 py-1.5 bg-white border rounded-lg text-sm font-medium hover:bg-gray-50">
                <RefreshCw className="h-4 w-4 mr-1" /> Retry
              </button>
            </div>
          )}

          {loading ? (
            <div className="py-12 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600" /><p className="mt-3 text-gray-500">Loading zones...</p></div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-12">
              <MapPin className="h-16 w-16 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500 text-lg">{zones.length ? 'No matching zones' : 'No zones configured'}</p>
              <p className="text-gray-400 mt-1">Create zones to define delivery coverage areas</p>
              {!zones.length && <Link href="/admin/zones/new" className="mt-4 inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700"><Plus className="h-4 w-4 mr-2" /> Create First Zone</Link>}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead><tr className="border-b text-left text-xs text-gray-500 uppercase"><th className="px-4 py-3">Name</th><th className="px-4 py-3">Code</th><th className="px-4 py-3">Description</th><th className="px-4 py-3">Status</th></tr></thead>
                <tbody className="divide-y">{filtered.map(z => <tr key={z.id} className="hover:bg-gray-50"><td className="px-4 py-4 font-medium text-gray-900">{z.name}</td><td className="px-4 py-4 text-gray-700">{z.code}</td><td className="px-4 py-4 text-gray-600">{z.description || '—'}</td><td className="px-4 py-4"><span className={`px-2 py-1 rounded-full text-xs ${z.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-700'}`}>{z.is_active ? 'Active' : 'Inactive'}</span></td></tr>)}</tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
