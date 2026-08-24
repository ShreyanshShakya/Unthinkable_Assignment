'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/auth';
import { Layout } from '@/components/Layout';
import { Package, Users, MapPin, DollarSign, Truck, Settings, Plus, Search, Filter, ChevronDown, ChevronUp, Eye, AlertCircle, CheckCircle, XCircle, Loader2, TrendingUp, TrendingDown } from 'lucide-react';
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
  created_at: string;
  pickup_zone?: { name: string; code: string };
  drop_zone?: { name: string; code: string };
  customer_id: string;
  customer?: { full_name: string; email: string; phone?: string };
  agent_id?: string;
  agent?: { full_name: string; email: string; phone?: string };
}

interface Stats {
  total_orders: number;
  active_orders: number;
  delivered_today: number;
  revenue_today: number;
  total_agents: number;
  available_agents: number;
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

export default function AdminDashboard() {
  const { user } = useAuthStore();
  const [stats, setStats] = useState<Stats>({
    total_orders: 0,
    active_orders: 0,
    delivered_today: 0,
    revenue_today: 0,
    total_agents: 0,
    available_agents: 0,
  });
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const pageSize = 15;

  useEffect(() => {
    fetchDashboard();
  }, [statusFilter, currentPage]);

  const fetchDashboard = async () => {
    setIsLoading(true);
    try {
      const [statsRes, ordersRes] = await Promise.all([
        api.get('/admin/stats'),
        api.get(`/admin/orders?skip=${(currentPage - 1) * pageSize}&limit=${pageSize}&status=${statusFilter !== 'all' ? statusFilter : ''}`),
      ]);
      setStats(statsRes.data);
      setOrders(ordersRes.data.orders || []);
      setTotalPages(ordersRes.data.total_pages || 1);
    } catch (error) {
      console.error('Failed to fetch dashboard:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredOrders = orders.filter(order => {
    if (search && !order.order_number.toLowerCase().includes(search.toLowerCase())) {
      return false;
    }
    return true;
  });

  return (
    <Layout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
            <p className="text-gray-600">System overview and management</p>
          </div>
          <div className="flex gap-2">
            <Link href="/admin/orders/new" className="px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700">
              <Plus className="h-5 w-5 mr-2" />
              Create Order
            </Link>
            <Link href="/admin/orders" className="px-4 py-2 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50">
              All Orders
            </Link>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-blue-100 text-blue-600">
                <Package className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Orders</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_orders}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-yellow-100 text-yellow-600">
                <Truck className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Orders</p>
                <p className="text-2xl font-bold text-gray-900">{stats.active_orders}</p>
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
                <p className="text-2xl font-bold text-gray-900">{stats.delivered_today}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-purple-100 text-purple-600">
                <DollarSign className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Revenue Today</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(stats.revenue_today)}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-indigo-100 text-indigo-600">
                <Users className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Agents</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_agents}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-teal-100 text-teal-600">
                <Truck className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Available Agents</p>
                <p className="text-2xl font-bold text-gray-900">{stats.available_agents}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Navigation */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link href="/admin/orders" className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:border-primary-300 hover:bg-primary-50 transition-colors">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-blue-100 text-blue-600">
                <Package className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Manage Orders</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_orders}</p>
              </div>
            </div>
          </Link>
          <Link href="/admin/agents" className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:border-primary-300 hover:bg-primary-50 transition-colors">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-green-100 text-green-600">
                <Users className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Manage Agents</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_agents}</p>
              </div>
            </div>
          </Link>
          <Link href="/admin/zones" className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:border-primary-300 hover:bg-primary-50 transition-colors">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-purple-100 text-purple-600">
                <MapPin className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Manage Zones</p>
                <p className="text-2xl font-bold text-gray-900">Configure</p>
              </div>
            </div>
          </Link>
        </div>

        {/* Recent Orders */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="px-6 py-4 border-b border-gray-100 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Orders</h2>
            <div className="flex items-center gap-4">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
              >
                <option value="all">All Status</option>
                <option value="created">Created</option>
                <option value="picked_up">Picked Up</option>
                <option value="in_transit">In Transit</option>
                <option value="out_for_delivery">Out for Delivery</option>
                <option value="delivered">Delivered</option>
                <option value="failed">Failed</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>
          
          {isLoading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-600 border-t-transparent mx-auto"></div>
              <p className="mt-4 text-gray-500">Loading orders...</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-100">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Order</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Agent</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Route</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider pr-6">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {orders.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="px-6 py-12 text-center">
                          <Package className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                          <p className="text-gray-500">No orders found</p>
                        </td>
                      </tr>
                    ) : (
                      orders.map((order) => (
                        <tr key={order.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4">
                            <Link href={`/admin/orders/${order.id}`} className="font-medium text-gray-900 hover:text-primary-600">
                              {order.order_number}
                            </Link>
                          </td>
                          <td className="px-6 py-4">
                            <div>
                              <p className="font-medium text-gray-900">{order.customer?.full_name || 'Unknown'}</p>
                              <p className="text-sm text-gray-500">{order.customer?.email}</p>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <p className="text-gray-900">{order.agent?.full_name || 'Unassigned'}</p>
                          </td>
                          <td className="px-6 py-4">
                            <div className="text-sm text-gray-900">
                              {order.pickup_zone?.code || '—'} → {order.drop_zone?.code || '—'}
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className={cn('px-3 py-1 rounded-full text-xs font-medium', {
                              'bg-blue-100 text-blue-800': order.status === 'created',
                              'bg-yellow-100 text-yellow-800': order.status === 'picked_up',
                              'bg-purple-100 text-purple-800': order.status === 'in_transit',
                              'bg-orange-100 text-orange-800': order.status === 'out_for_delivery',
                              'bg-green-100 text-green-800': order.status === 'delivered',
                              'bg-red-100 text-red-800': order.status === 'failed',
                              'bg-gray-100 text-gray-800': order.status === 'cancelled',
                            })}>
                              {order.status.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="px-6 py-4 font-medium text-gray-900">
                            {formatCurrency(order.total_charge)}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500">
                            {formatDateTime(order.created_at)}
                          </td>
                          <td className="px-6 py-4 text-right pr-6">
                            <Link
                              href={`/admin/orders/${order.id}`}
                              className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              View
                            </Link>
                          </td>
</tr>
                      )))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
    </Layout>
  );
}