'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/store/auth';
import { Layout } from '@/components/Layout';
import { Package, Truck, MapPin, Clock, Search, Filter, ChevronDown, ChevronUp, Eye, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { formatDateTime, formatCurrency, cn } from '@/lib/utils';
import api from '@/lib/api';

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
  order_type: string;
  payment_type: string;
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

export default function OrdersPage() {
  const { user } = useAuthStore();
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const pageSize = 10;

  useEffect(() => {
    fetchOrders();
  }, [statusFilter, sortOrder, currentPage]);

  const fetchOrders = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        skip: ((currentPage - 1) * pageSize).toString(),
        limit: pageSize.toString(),
      });
      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      
      const response = await api.get(`/orders?${params.toString()}`);
      const data = response.data;
      setOrders(data.orders || []);
      setTotalPages(data.total_pages || 1);
    } catch (error) {
      console.error('Failed to fetch orders:', error);
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

  const sortedOrders = [...filteredOrders].sort((a, b) => {
    const aIndex = statusOrder.indexOf(a.status);
    const bIndex = statusOrder.indexOf(b.status);
    if (sortOrder === 'asc') return aIndex - bIndex;
    return bIndex - aIndex;
  });

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Orders</h1>
            <p className="text-gray-600">Track and manage all your shipments</p>
          </div>
          <Link
            href="/dashboard/orders/new"
            className="inline-flex items-center px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Package className="h-5 w-5 mr-2" />
            New Order
          </Link>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search by order number..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div className="flex items-center gap-4">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
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
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                {sortOrder === 'asc' ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Orders Table */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          {isLoading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-600 border-t-transparent mx-auto"></div>
              <p className="mt-4 text-gray-500">Loading orders...</p>
            </div>
          ) : sortedOrders.length === 0 ? (
            <div className="p-12 text-center">
              <Package className="h-16 w-16 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500 text-lg">No orders found</p>
              <p className="text-gray-400 mt-1">Try adjusting your filters or create a new order</p>
              <Link
                href="/dashboard/orders/new"
                className="mt-4 inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700"
              >
                <Package className="h-4 w-4 mr-2" />
                Create Order
              </Link>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-100">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Order</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Route</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider pr-6">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {sortedOrders.map((order) => (
                      <tr key={order.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <Link href={`/dashboard/orders/${order.id}`} className="font-medium text-gray-900 hover:text-primary-600">
                            {order.order_number}
                          </Link>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-900">
                            {order.pickup_zone?.code || '—'} → {order.drop_zone?.code || '—'}
                          </div>
                          <div className="text-xs text-gray-500 truncate max-w-xs">
                            {order.pickup_address} → {order.drop_address}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                              {order.order_type.toUpperCase()}
                            </span>
                            <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                              {order.payment_type.toUpperCase()}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={cn('px-3 py-1 rounded-full text-xs font-medium', statusColors[order.status])}>
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
                            href={`/dashboard/orders/${order.id}`}
                            className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            View
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
                  <p className="text-sm text-gray-600">
                    Page {currentPage} of {totalPages}
                  </p>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </Layout>
  );
}