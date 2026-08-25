'use client';

import { useEffect, useState } from 'react';
import { Layout } from '@/components/Layout';
import { Package, Truck, Clock, CheckCircle, AlertCircle, Eye } from 'lucide-react';
import { formatCurrency, cn } from '@/lib/utils';
import api from '@/lib/api';
import Link from 'next/link';

interface Order {
  id: string; order_number: string; status: string; total_charge: number;
  pickup_address: string; drop_address: string; pickup_pincode: string; drop_pincode: string;
  pickup_city?: string; drop_city?: string;
  pickup_zone?: { name: string; code: string }; drop_zone?: { name: string; code: string };
  length_cm: number; breadth_cm: number; height_cm: number; actual_weight_kg: number;
  volumetric_weight_kg: number; billable_weight_kg: number; order_type: string;
  payment_type: string; zone_type: string; created_at: string; picked_up_at?: string;
  delivered_at?: string; failure_reason?: string;
}

interface AgentProfile {
  id: string; employee_id: string; zone_id?: string; status: string;
  max_concurrent_deliveries: number; current_deliveries_count: number; is_active: boolean;
  user?: { full_name: string; email: string; phone?: string };
  user_name?: string; user_email?: string; user_phone?: string;
}

const ACTIVE_STATUSES = ['assigned', 'picked_up', 'in_transit', 'out_for_delivery'];
const normalizeStatus = (status: string) => status?.toLowerCase() || 'offline';

export default function AgentDashboard() {
  const [profile, setProfile] = useState<AgentProfile | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [stats, setStats] = useState({ active: 0, delivered: 0, pending: 0, failed: 0 });
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  useEffect(() => { fetchDashboard(); }, []);

  const fetchDashboard = async () => {
    try {
      const [profileRes, ordersRes] = await Promise.all([api.get('/agents/profile'), api.get('/agent/orders')]);
      const rawProfile = profileRes.data;
      setProfile({ ...rawProfile, status: normalizeStatus(rawProfile.status) });
      const orderList = ordersRes.data.orders || [];
      setOrders(orderList);
      setStats({
        active: orderList.filter((o: Order) => ACTIVE_STATUSES.includes(o.status)).length,
        delivered: orderList.filter((o: Order) => o.status === 'delivered').length,
        pending: orderList.filter((o: Order) => o.status === 'assigned').length,
        failed: orderList.filter((o: Order) => o.status === 'failed').length,
      });
    } catch (error) { console.error('Failed to fetch dashboard:', error); }
    finally { setIsLoading(false); }
  };

  const updateAgentStatus = async (newStatus: string) => {
    if (newStatus === profile?.status) return;
    setIsUpdatingStatus(true);
    try {
      const response = await api.patch('/agents/availability', { status: newStatus });
      // Update immediately from the server response. Do not wait for a second
      // dashboard request, which can briefly return stale cached UI state.
      const serverStatus = normalizeStatus(response.data?.status || newStatus);
      setProfile(prev => prev ? { ...prev, status: serverStatus } : prev);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update agent status');
    } finally { setIsUpdatingStatus(false); }
  };

  const activeOrders = orders.filter(o => ACTIVE_STATUSES.includes(o.status));
  const recentDelivered = orders.filter(o => o.status === 'delivered').slice(0, 5);
  const pendingOrders = orders.filter(o => o.status === 'assigned');

  if (isLoading) return <Layout><div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent" /></div></Layout>;

  const status = normalizeStatus(profile?.status || 'offline');
  const displayName = profile?.user?.full_name || profile?.user_name || 'Agent';

  return (
    <Layout>
      <div className="space-y-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Welcome, {displayName.split(' ')[0]}!</h1>
            <p className="text-gray-600">{profile?.employee_id || 'N/A'} • {status.charAt(0).toUpperCase() + status.slice(1)}</p>
          </div>
          <select value={status} disabled={isUpdatingStatus} onChange={(e) => updateAgentStatus(e.target.value)} className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 disabled:opacity-60">
            <option value="available">Available</option><option value="busy">Busy</option><option value="offline">Offline</option>
          </select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard icon={<Package className="h-6 w-6" />} title="Active Deliveries" value={stats.active} extra={`${stats.active}/${profile?.max_concurrent_deliveries} capacity`} />
          <StatCard icon={<CheckCircle className="h-6 w-6" />} title="Delivered Today" value={stats.delivered} />
          <StatCard icon={<Clock className="h-6 w-6" />} title="Pending Pickup" value={stats.pending} />
          <StatCard icon={<AlertCircle className="h-6 w-6" />} title="Failed" value={stats.failed} />
        </div>

        <section className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between"><h2 className="text-lg font-semibold text-gray-900">Active Deliveries</h2><span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">{activeOrders.length} active</span></div>
          {activeOrders.length === 0 ? <EmptyState /> : <div className="divide-y divide-gray-100">{activeOrders.map(order => <Link key={order.id} href={`/agent/orders/${order.id}`} className="px-6 py-4 hover:bg-gray-50 flex items-center justify-between"><div className="flex items-center"><div className="h-10 w-10 rounded-lg bg-primary-100 flex items-center justify-center"><Package className="h-5 w-5 text-primary-600" /></div><div className="ml-4"><p className="font-medium text-gray-900">{order.order_number}</p><p className="text-sm text-gray-500">{order.pickup_zone?.code} → {order.drop_zone?.code}</p></div></div><div className="flex items-center space-x-4"><span className={cn('px-3 py-1 rounded-full text-xs font-medium', order.status === 'assigned' ? 'bg-blue-100 text-blue-800' : order.status === 'picked_up' ? 'bg-yellow-100 text-yellow-800' : order.status === 'in_transit' ? 'bg-purple-100 text-purple-800' : 'bg-orange-100 text-orange-800')}>{order.status.replace('_', ' ')}</span><Eye className="h-5 w-5 text-gray-400" /></div></Link>)}</div>}
        </section>

        {pendingOrders.length > 0 && <section className="bg-white rounded-xl shadow-sm border border-gray-100"><div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between"><h2 className="text-lg font-semibold text-gray-900">Awaiting Pickup</h2><span className="px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">{pendingOrders.length} pending</span></div><div className="divide-y divide-gray-100">{pendingOrders.map(order => <div key={order.id} className="px-6 py-4 flex items-center justify-between"><div><p className="font-medium text-gray-900">{order.order_number}</p><p className="text-sm text-gray-500">{order.pickup_zone?.code} → {order.drop_zone?.code}</p></div><Link href={`/agent/orders/${order.id}`} className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm">View</Link></div>)}</div></section>}

        <section className="bg-white rounded-xl shadow-sm border border-gray-100"><div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between"><h2 className="text-lg font-semibold text-gray-900">Recently Delivered</h2><Link href="/agent/orders" className="text-sm text-primary-600">View all</Link></div>{recentDelivered.length === 0 ? <div className="p-12 text-center"><CheckCircle className="h-16 w-16 mx-auto text-gray-300 mb-4" /><p className="text-gray-500">No deliveries completed yet</p></div> : <div className="divide-y divide-gray-100">{recentDelivered.map(order => <div key={order.id} className="px-6 py-4 flex items-center justify-between"><div><p className="font-medium text-gray-900">{order.order_number}</p><p className="text-sm text-gray-500">{order.pickup_zone?.code} → {order.drop_zone?.code} • {formatCurrency(order.total_charge)}</p></div><Link href={`/agent/orders/${order.id}`} className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm">View</Link></div>)}</div>}</section>
      </div>
    </Layout>
  );
}

function StatCard({ icon, title, value, extra }: { icon: React.ReactNode; title: string; value: number; extra?: string }) {
  return <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6"><div className="flex items-center"><div className="p-3 rounded-lg bg-blue-100 text-blue-600">{icon}</div><div className="ml-4"><p className="text-sm font-medium text-gray-600">{title}</p><p className="text-2xl font-bold text-gray-900">{value}</p>{extra && <p className="text-xs text-gray-500">{extra}</p>}</div></div></div>;
}

function EmptyState() { return <div className="p-12 text-center"><Truck className="h-16 w-16 mx-auto text-gray-300 mb-4" /><p className="text-gray-500 text-lg">No active deliveries</p><p className="text-gray-400 mt-1">Orders will appear here when assigned</p></div>; }
