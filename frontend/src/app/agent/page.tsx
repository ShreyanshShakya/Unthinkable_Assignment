'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/auth';
import { Layout } from '@/components/Layout';
import { Package, Truck, MapPin, Clock, CheckCircle, XCircle, AlertCircle, Loader2, MapPin as MapPinIcon, Calendar, User, Phone, Shield, Scale, DollarSign, Menu, X, Plus, Eye } from 'lucide-react';
import { formatDateTime, formatCurrency, cn } from '@/lib/utils';
import api from '@/lib/api';
import Link from 'next/link';

interface Order {
  id: string;
  order_number: string;
  status: string;
  total_charge: number;
  pickup_address: string;
  drop_address: string;
  pickup_pincode: string;
  drop_pincode: string;
  pickup_city?: string;
  drop_city?: string;
  pickup_zone?: { name: string; code: string };
  drop_zone?: { name: string; code: string };
  length_cm: number;
  breadth_cm: number;
  height_cm: number;
  actual_weight_kg: number;
  volumetric_weight_kg: number;
  billable_weight_kg: number;
  order_type: string;
  payment_type: string;
  zone_type: string;
  created_at: string;
  picked_up_at?: string;
  delivered_at?: string;
  failure_reason?: string;
}

interface AgentProfile {
  id: string;
  employee_id: string;
  zone_id?: string;
  status: string;
  max_concurrent_deliveries: number;
  current_deliveries_count: number;
  is_active: boolean;
  user: { full_name: string; email: string; phone?: string };
}

const statusColors: Record<string, string> = {
  created: 'bg-blue-100 text-blue-800',
  picked_up: 'bg-yellow-100 text-yellow-800',
  in_transit: 'bg-purple-100 text-purple-800',
  out_for_delivery: 'bg-orange-100 text-orange-800',
  delivered: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-gray-100 text-gray-800',
};

const statusOrder = ['created', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'failed', 'cancelled'];

export default function AgentDashboard() {
  const { user } = useAuthStore();
  const [profile, setProfile] = useState<AgentProfile | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [stats, setStats] = useState({
    active: 0,
    delivered: 0,
    pending: 0,
    failed: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const [profileRes, ordersRes] = await Promise.all([
        api.get('/agents/profile'),
        api.get('/agent/orders'),
      ]);
      setProfile(profileRes.data);
      const orderData = ordersRes.data;
      setOrders(orderData.orders || []);
      
      const active = orderData.orders?.filter((o: Order) => 
        ['picked_up', 'in_transit', 'out_for_delivery'].includes(o.status)
      ).length || 0;
      const delivered = orderData.orders?.filter((o: Order) => o.status === 'delivered').length || 0;
      const pending = orderData.orders?.filter((o: Order) => o.status === 'created').length || 0;
      const failed = orderData.orders?.filter((o: Order) => o.status === 'failed').length || 0;
      
      setStats({ active, delivered, pending, failed });
    } catch (error) {
      console.error('Failed to fetch dashboard:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateOrderStatus = async (orderId: string, newStatus: string) => {
    setIsUpdatingStatus(true);
    try {
      await api.patch(`/orders/${orderId}/status`, { status: newStatus });
      // Refresh
      fetchDashboard();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update status');
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const updateAgentStatus = async (newStatus: string) => {
    setIsUpdatingStatus(true);
    try {
      await api.patch('/agents/status', { status: newStatus });
      fetchDashboard();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update agent status');
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const activeOrders = orders.filter(o => 
    ['picked_up', 'in_transit', 'out_for_delivery'].includes(o.status)
  );
  const recentDelivered = orders.filter(o => o.status === 'delivered').slice(0, 5);
  const pendingOrders = orders.filter(o => o.status === 'created');

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Welcome, {profile?.user?.full_name?.split(' ')[0] || 'Agent'}!
            </h1>
            <p className="text-gray-600">
              {profile?.employee_id || 'N/A'} • {profile?.status ? profile.status.charAt(0).toUpperCase() + profile.status.slice(1) : 'N/A'}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={profile?.status || 'offline'}
              onChange={(e) => updateAgentStatus(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="available">Available</option>
              <option value="busy">Busy</option>
              <option value="offline">Offline</option>
            </select>
          </div>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-blue-100 text-blue-600">
                <Package className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Deliveries</p>
                <p className="text-2xl font-bold text-gray-900">{stats.active}</p>
                <p className="text-xs text-gray-500">{stats.active}/{profile?.max_concurrent_deliveries} capacity</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-green-100 text-green-600">
                <CheckCircle className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Delivered Today</p>
                <p className="text-2xl font-bold text-gray-900">{stats.delivered}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-yellow-100 text-yellow-600">
                <Clock className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Pending Pickup</p>
                <p className="text-2xl font-bold text-gray-900">{stats.pending}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-red-100 text-red-600">
                <AlertCircle className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Failed</p>
                <p className="text-2xl font-bold text-gray-900">{stats.failed}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Active Deliveries */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Active Deliveries</h2>
            <span className="px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              {activeOrders.length} active
            </span>
          </div>
          {activeOrders.length === 0 ? (
            <div className="p-12 text-center">
              <Truck className="h-16 w-16 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500 text-lg">No active deliveries</p>
              <p className="text-gray-400 mt-1">Orders will appear here when assigned</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {activeOrders.map((order) => (
                <Link
                  key={order.id}
                  href={`/agent/orders/${order.id}`}
                  className="px-6 py-4 hover:bg-gray-50 transition-colors flex items-center justify-between"
                >
                  <div className="flex items-center">
                    <div className="h-10 w-10 rounded-lg bg-primary-100 flex items-center justify-center">
                      <Package className="h-5 w-5 text-primary-600" />
                    </div>
                    <div className="ml-4">
                      <p className="font-medium text-gray-900">{order.order_number}</p>
                      <p className="text-sm text-gray-500">
                        {order.pickup_zone?.code} → {order.drop_zone?.code}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <span className={cn('px-3 py-1 rounded-full text-xs font-medium', {
                      'bg-blue-100 text-blue-800': order.status === 'created',
                      'bg-yellow-100 text-yellow-800': order.status === 'picked_up',
                      'bg-purple-100 text-purple-800': order.status === 'in_transit',
                      'bg-orange-100 text-orange-800': order.status === 'out_for_delivery',
                      'bg-green-100 text-green-800': order.status === 'delivered',
                      'bg-red-100 text-red-800': order.status === 'failed',
                    })}>
                      {order.status.replace('_', ' ')}
                    </span>
                    <Eye className="h-5 w-5 text-gray-400" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Pending Pickup Orders */}
        {pendingOrders.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Awaiting Pickup</h2>
              <span className="px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                {pendingOrders.length} pending
              </span>
            </div>
            <div className="divide-y divide-gray-100">
              {pendingOrders.map((order) => (
                <div key={order.id} className="px-6 py-4 hover:bg-gray-50 flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="h-10 w-10 rounded-lg bg-yellow-100 flex items-center justify-center">
                      <Package className="h-5 w-5 text-yellow-600" />
                    </div>
                    <div className="ml-4">
                      <p className="font-medium text-gray-900">{order.order_number}</p>
                      <p className="text-sm text-gray-500">
                        {order.pickup_zone?.code} → {order.drop_zone?.code}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="px-3 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                      Awaiting Pickup
                    </span>
                    <Link
                      href={`/agent/orders/${order.id}`}
                      className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
                    >
                      View
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Delivered */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Recently Delivered</h2>
            <Link href="/agent/orders" className="text-sm text-primary-600 hover:text-primary-500">
              View all
            </Link>
          </div>
          {recentDelivered.length === 0 ? (
            <div className="p-12 text-center">
              <CheckCircle className="h-16 w-16 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">No deliveries completed yet</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {recentDelivered.map((order) => (
                <div key={order.id} className="px-6 py-4 hover:bg-gray-50 flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="h-10 w-10 rounded-lg bg-green-100 flex items-center justify-center">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    </div>
                    <div className="ml-4">
                      <p className="font-medium text-gray-900">{order.order_number}</p>
                      <p className="text-sm text-gray-500">
                        {order.pickup_zone?.code} → {order.drop_zone?.code} • {formatCurrency(order.total_charge)}
                      </p>
                    </div>
                  </div>
                  <Link
                    href={`/agent/orders/${order.id}`}
                    className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    View
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}