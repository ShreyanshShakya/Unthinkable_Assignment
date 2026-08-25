'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Loader2, UserCheck, RefreshCw, AlertCircle } from 'lucide-react';
import { Layout } from '@/components/Layout';
import api from '@/lib/api';

interface Agent {
  id: string;
  employee_id: string;
  status: string;
  max_concurrent_deliveries: number;
  current_deliveries_count: number;
  is_active: boolean;
  user_name?: string;
  user_email?: string;
  user_phone?: string;
}

export default function AssignAgentPage() {
  const params = useParams();
  const router = useRouter();
  const orderId = params.id as string;
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState('');
  const [loading, setLoading] = useState(true);
  const [assigning, setAssigning] = useState(false);
  const [error, setError] = useState('');

  const loadAgents = async () => {
    setLoading(true); setError('');
    try {
      const response = await api.get<Agent[]>('/agents', { params: { limit: 100, is_active: true } });
      setAgents(Array.isArray(response.data) ? response.data : []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load agents');
    } finally { setLoading(false); }
  };

  useEffect(() => { loadAgents(); }, []);

  const availableAgents = useMemo(
    () => agents.filter(a => a.is_active && a.current_deliveries_count < a.max_concurrent_deliveries),
    [agents]
  );

  const assign = async () => {
    if (!selectedAgent) { setError('Select an agent first.'); return; }
    setAssigning(true); setError('');
    try {
      await api.post('/agents/assign', { order_id: orderId, agent_id: selectedAgent });
      router.push(`/admin/orders/${orderId}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to assign agent');
    } finally { setAssigning(false); }
  };

  const autoAssign = async () => {
    setAssigning(true); setError('');
    try {
      await api.post('/agents/assign', { order_id: orderId });
      router.push(`/admin/orders/${orderId}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'No suitable agent could be found');
    } finally { setAssigning(false); }
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto space-y-6">
        <Link href={`/admin/orders/${orderId}`} className="inline-flex items-center text-gray-500 hover:text-gray-700">
          <ArrowLeft className="h-5 w-5 mr-1" /> Back to Order
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Assign Delivery Agent</h1>
          <p className="text-gray-600 mt-1">Choose an agent manually or let the assignment service select one.</p>
        </div>

        {error && <div className="p-4 rounded-lg bg-red-50 border border-red-100 text-red-700 flex items-start"><AlertCircle className="h-5 w-5 mr-2 mt-0.5" />{error}</div>}

        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 space-y-5">
          {loading ? (
            <div className="py-10 text-center"><Loader2 className="h-8 w-8 animate-spin mx-auto text-primary-600" /><p className="mt-2 text-gray-500">Loading agents...</p></div>
          ) : availableAgents.length === 0 ? (
            <div className="py-8 text-center text-gray-500">
              <UserCheck className="h-12 w-12 mx-auto text-gray-300 mb-3" />
              <p>No active agents with available capacity.</p>
              <button onClick={loadAgents} className="mt-4 inline-flex items-center px-3 py-2 border rounded-lg text-sm"><RefreshCw className="h-4 w-4 mr-1" />Refresh</button>
            </div>
          ) : (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Agent</label>
                <select value={selectedAgent} onChange={e => setSelectedAgent(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900">
                  <option value="">Select an agent</option>
                  {availableAgents.map(agent => (
                    <option key={agent.id} value={agent.id}>
                      {agent.user_name || agent.employee_id} — {agent.status} — {agent.current_deliveries_count}/{agent.max_concurrent_deliveries}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex flex-col sm:flex-row gap-3">
                <button onClick={assign} disabled={assigning || !selectedAgent} className="flex-1 inline-flex justify-center items-center px-4 py-2 bg-primary-600 text-white rounded-lg disabled:opacity-50">
                  {assigning ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <UserCheck className="h-4 w-4 mr-2" />} Assign Selected Agent
                </button>
                <button onClick={autoAssign} disabled={assigning} className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg disabled:opacity-50">
                  <RefreshCw className="h-4 w-4 mr-2" /> Auto Assign
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </Layout>
  );
}
