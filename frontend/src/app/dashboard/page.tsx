'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/store/auth';
import { Layout } from '@/components/Layout';
import { Package, Truck, MapPin, Clock, DollarSign, Plus, Eye, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { formatDateTime, formatCurrency, getInitials, cn } from '@/lib/utils';
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

const statusIcons: Record<string, React.ReactNode> = {
  created: <Package className="h-4 w-4" />,
  picked_up: <Truck className="h-4 w-4" />,
  in_transit: <Truck className="h-4 w-4" />,
  out_for_delivery: <MapPin className="h-4 w-4" />,
  delivered: <CheckCircle className="h-4 w-4" />,
  failed: <XCircle className="h-4 w-4" />,
  cancelled: <AlertCircle className="h-4 w-4" />,
};

export default function CustomerDashboard() {
  const { user } = useAuthStore();
  const [orders, setOrders] = useState<Order[]>([]);
  const [stats, setStats] = useState({
    active: 0,
    delivered: 0,
    pending: 0,
    total_spent: 0,
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await api.get('/orders');
      const data = response.data;
      setOrders(data.orders || []);
      
      // Calculate stats
      const active = data.orders?.filter((o: Order) => 
        ['picked_up', 'in_transit', 'out_for_delivery'].includes(o.status)
      ).length || 0;
      const delivered = data.orders?.filter((o: Order) => o.status === 'delivered').length || 0;
      const pending = data.orders?.filter((o: Order) => o.status === 'created').length || 0;
      const total_spent = data.orders?.reduce((sum: number, o: Order) => sum + o.total_charge, 0) || 0;
      
      setStats({ active, delivered, pending, total_spent });
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent"></div>
        </div>
      </Layout>
    );
  }

  const recentOrders = orders.slice(0, 5);

  return (
    <Layout>
      <div className="space-y-8">
        {/* Welcome header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back, {user?.full_name?.split(' ')[0]}!
          </h1>
          <p className="text-gray-600 mt-1">Here's an overview of your deliveries</p>
        </div>

        {/* Stats cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-blue-100 text-blue-600">
                <Package className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Orders</p>
                <p className="text-2xl font-bold text-gray-900">{stats.active}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-green-100 text-green-600">
                <CheckCircle className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Delivered</p>
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
                <p className="text-sm font-medium text-gray-600">Pending</p>
                <p className="text-2xl font-bold text-gray-900">{stats.pending}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-purple-100 text-purple-600">
                <DollarSign className="h-6 w-6" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Spent</p>
                <p className="text-2xl font-bold text-gray-900">{formatCurrency(stats.total_spent)}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick actions */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              href="/dashboard/orders/new"
              className="p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors"
            >
              <div className="p-3 rounded-lg bg-primary-100 text-primary-600 mb-2">
                <Plus className="h-6 w-6" />
              </div>
              <p className="font-medium text-gray-900">Create Order</p>
              <p className="text-sm text-gray-500 mt-1">Ship a new package</p>
            </Link>
            <Link
              href="/dashboard/orders"
              className="p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors"
            >
              <div className="p-3 rounded-lg bg-blue-100 text-blue-600 mb-2">
                <Package className="h-6 w-6" />
              </div>
              <p className="font-medium text-gray-900">View All Orders</p>
              <p className="text-sm text-gray-500 mt-1">Track & manage orders</p>
            </Link>
            <Link
              href="/dashboard/tracking"
              className="p-4 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors"
            >
              <div className="p-3 rounded-lg bg-green-100 text-green-600 mb-2">
                <MapPin className="h-6 w-6" />
              </div>
              <p className="font-medium text-gray-900">Track Shipment</p>
              <p className="text-sm text-gray-500 mt-1">Real-time tracking</p>
            </Link>
          </div>
        </div>

        {/* Recent orders */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Recent Orders</h2>
            <Link href="/dashboard/orders" className="text-sm text-primary-600 hover:text-primary-500">
              View all
            </Link>
          </div>
          {recentOrders.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <Package className="h-12 w-12 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">No orders yet</p>
              <Link
                href="/dashboard/orders/new"
                className="mt-4 inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                Create your first order
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {recentOrders.map((order) => (
                <Link
                  key={order.id}
                  href={`/dashboard/orders/${order.id}`}
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
                    <span className={cn('px-3 py-1 rounded-full text-xs font-medium', statusColors[order.status])}>
                      {order.status.replace('_', ' ')}
                    </span>
                    <span className="font-medium text-gray-900">
                      {formatCurrency(order.total_charge)}
                    </span>
                    <Eye className="h-5 w-5 text-gray-400" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}