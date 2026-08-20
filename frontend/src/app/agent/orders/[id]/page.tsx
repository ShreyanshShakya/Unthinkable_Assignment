'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/auth';
import { Layout } from '@/components/Layout';
import { Package, Truck, MapPin, Clock, DollarSign, ArrowLeft, AlertCircle, CheckCircle, XCircle, Loader2, MapPin as MapPinIcon, Calendar, User, Phone, Shield, Scale, Eye } from 'lucide-react';
import { formatDateTime, formatCurrency, cn, formatDate } from '@/lib/utils';
import api from '@/lib/api';

interface Order {
  id: string;
  order_number: string;
  status: string;
  total_charge: number;
  base_charge: number;
  cod_surcharge: number;
  pickup_address: string;
  drop_address: string;
  pickup_pincode: string;
  drop_pincode: string;
  pickup_city?: string;
  drop_city?: string;
  pickup_state?: string;
  drop_state?: string;
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

interface StatusHistory {
  id: string;
  old_status?: string;
  new_status: string;
  actor_id: string;
  actor_role: string;
  reason?: string;
  created_at: string;
}

const statusColors: Record<string, string> = {
  created: 'bg-blue-100 text-blue-800 border-blue-200',
  picked_up: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  in_transit: 'bg-purple-100 text-purple-800 border-purple-200',
  out_for_delivery: 'bg-orange-100 text-orange-800 border-orange-200',
  delivered: 'bg-green-100 text-green-800 border-green-200',
  failed: 'bg-red-100 text-red-800 border-red-200',
  cancelled: 'bg-gray-100 text-gray-800 border-gray-200',
};

const statusIcons: Record<string, React.ReactNode> = {
  created: <Package className="h-5 w-5" />,
  picked_up: <Truck className="h-5 w-5" />,
  in_transit: <Truck className="h-5 w-5" />,
  out_for_delivery: <MapPinIcon className="h-5 w-5" />,
  delivered: <CheckCircle className="h-5 w-5" />,
  failed: <XCircle className="h-5 w-5" />,
  cancelled: <AlertCircle className="h-5 w-5" />,
};

const statusLabels: Record<string, string> = {
  created: 'Order Created',
  picked_up: 'Picked Up',
  in_transit: 'In Transit',
  out_for_delivery: 'Out for Delivery',
  delivered: 'Delivered',
  failed: 'Delivery Failed',
  cancelled: 'Cancelled',
};

const statusDescriptions: Record<string, string> = {
  created: 'Order is awaiting pickup by an agent.',
  picked_up: 'Package has been picked up and is on the way.',
  in_transit: 'Package is in transit to the destination.',
  out_for_delivery: 'Package is out for final delivery.',
  delivered: 'Package has been successfully delivered!',
  failed: 'Delivery attempt failed. You can reschedule.',
  cancelled: 'This order has been cancelled.',
};

const statusOrder = ['created', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered', 'failed', 'cancelled'];

const validTransitions: Record<string, string[]> = {
  created: ['picked_up', 'cancelled'],
  picked_up: ['in_transit', 'cancelled'],
  in_transit: ['out_for_delivery', 'cancelled'],
  out_for_delivery: ['delivered', 'failed'],
  failed: ['out_for_delivery', 'cancelled'],
  delivered: [],
  cancelled: [],
};

export default function AgentOrderDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuthStore();
  const [order, setOrder] = useState<Order | null>(null);
  const [history, setHistory] = useState<StatusHistory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState<string | null>(null);

  const orderId = params.id as string;

  useEffect(() => {
    fetchOrder();
  }, [orderId]);

  const fetchOrder = async () => {
    setIsLoading(true);
    try {
      const [orderRes, historyRes] = await Promise.all([
        api.get(`/orders/${orderId}`),
        api.get(`/orders/${orderId}/tracking`),
      ]);
      setOrder(orderRes.data);
      setHistory(historyRes.data || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load order');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStatusUpdate = async (newStatus: string) => {
    if (!order) return;
    setUpdatingStatus(newStatus);
    try {
      await api.patch(`/orders/${orderId}/status`, { status: newStatus });
      router.refresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update status');
    } finally {
      setUpdatingStatus(null);
    }
  };

  const getAllowedTransitions = (currentStatus: string) => {
    return validTransitions[currentStatus] || [];
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

  if (error) {
    return (
      <Layout>
        <div className="text-center py-12">
          <AlertCircle className="h-16 w-16 mx-auto text-red-500 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900">Failed to load order</h2>
          <p className="text-gray-500 mt-2">{error}</p>
          <Link href="/agent" className="mt-4 inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700">
            Back to Dashboard
          </Link>
        </div>
      </Layout>
    );
  }

  if (!order) {
    return (
      <Layout>
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold text-gray-900">Order not found</h2>
          <Link href="/agent" className="mt-4 inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700">
            Back to Dashboard
          </Link>
        </div>
      </Layout>
    );
  }

  const currentStatusIndex = statusOrder.indexOf(order.status);
  const completedStatuses = statusOrder.slice(0, currentStatusIndex + 1);
  const allowedTransitions = getAllowedTransitions(order.status);

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Link href="/agent" className="text-gray-500 hover:text-gray-700 mb-2 inline-flex items-center">
            <ArrowLeft className="h-5 w-5 mr-1" />
            Back to Dashboard
          </Link>
          <div className="text-right">
            <h1 className="text-2xl font-bold text-gray-900">{order.order_number}</h1>
            <p className="text-gray-600">{order.order_type.toUpperCase()} • {order.payment_type.toUpperCase()}</p>
          </div>
        </div>

        {/* Status Timeline */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">Delivery Timeline</h2>
          <div className="relative">
            <div className="absolute left-10 top-0 bottom-0 w-0.5 bg-gray-200" />
            <div className="space-y-6">
              {statusOrder.map((status, index) => {
                const isCompleted = completedStatuses.includes(status);
                const isCurrent = status === order.status;
                const historyEntry = history.find(h => h.new_status === status);
                
                return (
                  <div key={status} className="relative flex items-start">
                    <div className={cn(
                      'flex-shrink-0 w-20 h-20 rounded-full border-4 flex items-center justify-center z-10',
                      isCompleted ? statusColors[status].replace('bg-', 'bg-').replace('text-', 'text-') : 'bg-white border-gray-200',
                      isCurrent && 'ring-4 ring-primary-200'
                    )}>
                      {isCompleted ? (
                        <CheckCircle className={cn('h-6 w-6', isCurrent ? 'text-primary-600' : 'text-green-600')} />
                      ) : (
                        statusIcons[status]
                      )}
                    </div>
                    <div className="ml-6 pt-1 flex-1">
                      <div className={cn('font-medium', isCurrent ? 'text-gray-900' : 'text-gray-600')}>
                        {statusLabels[status]}
                      </div>
                      <p className="text-sm text-gray-500 mt-1">{statusDescriptions[status]}</p>
                      {historyEntry && (
                        <p className="text-xs text-gray-400 mt-1">
                          {historyEntry.actor_role === 'customer' ? 'By customer' : historyEntry.actor_role === 'agent' ? 'By you' : 'By admin'}
                          {historyEntry.reason && ` • ${historyEntry.reason}`}
                          • {formatDateTime(historyEntry.created_at)}
                        </p>
                      )}
                      {!historyEntry && isCompleted && (
                        <p className="text-xs text-gray-400 mt-1">Completed</p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Order Details Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Addresses */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <MapPinIcon className="h-5 w-5 text-primary-600 mr-2" />
                Addresses
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-4 rounded-lg bg-blue-50">
                  <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                    <MapPinIcon className="h-4 w-4 text-blue-600 mr-1" />
                    Pickup
                  </h4>
                  <p className="text-gray-600">{order.pickup_address}</p>
                  <p className="text-sm text-gray-500 mt-1">
                    {order.pickup_pincode}{order.pickup_city && `, ${order.pickup_city}`}{order.pickup_state && `, ${order.pickup_state}`}
                  </p>
                  {order.pickup_zone && (
                    <p className="text-xs text-blue-600 mt-1">Zone: {order.pickup_zone.name} ({order.pickup_zone.code})</p>
                  )}
                </div>
                <div className="p-4 rounded-lg bg-green-50">
                  <h4 className="font-medium text-gray-900 mb-2 flex items-center">
                    <MapPinIcon className="h-4 w-4 text-green-600 mr-1" />
                    Drop
                  </h4>
                  <p className="text-gray-600">{order.drop_address}</p>
                  <p className="text-sm text-gray-500 mt-1">
                    {order.drop_pincode}{order.drop_city && `, ${order.drop_city}`}{order.drop_state && `, ${order.drop_state}`}
                  </p>
                  {order.drop_zone && (
                    <p className="text-xs text-green-600 mt-1">Zone: {order.drop_zone.name} ({order.drop_zone.code})</p>
                  )}
                </div>
              </div>
            </div>

            {/* Package Details */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Package className="h-5 w-5 text-primary-600 mr-2" />
                Package Details
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg bg-gray-50">
                  <p className="text-sm text-gray-500">Length</p>
                  <p className="font-semibold text-gray-900">{order.length_cm} cm</p>
                </div>
                <div className="p-4 rounded-lg bg-gray-50">
                  <p className="text-sm text-gray-500">Breadth</p>
                  <p className="font-semibold text-gray-900">{order.breadth_cm} cm</p>
                </div>
                <div className="p-4 rounded-lg bg-gray-50">
                  <p className="text-sm text-gray-500">Height</p>
                  <p className="font-semibold text-gray-900">{order.height_cm} cm</p>
                </div>
                <div className="p-4 rounded-lg bg-gray-50">
                  <p className="text-sm text-gray-500">Actual Weight</p>
                  <p className="font-semibold text-gray-900">{order.actual_weight_kg} kg</p>
                </div>
                <div className="p-4 rounded-lg bg-gray-50 md:col-span-2">
                  <p className="text-sm text-gray-500">Volumetric Weight</p>
                  <p className="font-semibold text-gray-900">{order.volumetric_weight_kg} kg</p>
                </div>
                <div className="p-4 rounded-lg bg-gray-50 md:col-span-2">
                  <p className="text-sm text-gray-500">Billable Weight</p>
                  <p className="font-semibold text-gray-900">{order.billable_weight_kg} kg</p>
                </div>
              </div>
            </div>

            {/* Pricing */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <DollarSign className="h-5 w-5 text-primary-600 mr-2" />
                Pricing Breakdown
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between py-2 border-b border-gray-100">
                  <span className="text-gray-600">Base Charge</span>
                  <span className="font-medium text-gray-900">{formatCurrency(order.base_charge)}</span>
                </div>
                {order.cod_surcharge > 0 && (
                  <div className="flex justify-between py-2 border-b border-gray-100 text-yellow-700">
                    <span className="text-gray-600">COD Surcharge</span>
                    <span className="font-medium">{formatCurrency(order.cod_surcharge)}</span>
                  </div>
                )}
                <div className="flex justify-between py-2 text-lg font-bold text-primary-600">
                  <span>Total Charge</span>
                  <span>{formatCurrency(order.total_charge)}</span>
                </div>
              </div>
            </div>

            {/* Order Classification */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Scale className="h-5 w-5 text-primary-600 mr-2" />
                Order Classification
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-lg bg-gray-50">
                  <p className="text-sm text-gray-500">Order Type</p>
                  <p className="font-semibold text-gray-900 capitalize">{order.order_type}</p>
                </div>
                <div className="p-4 rounded-lg bg-gray-50">
                  <p className="text-sm text-gray-500">Payment Type</p>
                  <p className="font-semibold text-gray-900 capitalize">{order.payment_type}</p>
                </div>
                <div className="p-4 rounded-lg bg-gray-50">
                  <p className="text-sm text-gray-500">Zone Type</p>
                  <p className="font-semibold text-gray-900 capitalize">{order.zone_type.replace('_', ' ')}</p>
                </div>
                <div className="p-4 rounded-lg bg-gray-50">
                  <p className="text-sm text-gray-500">Created</p>
                  <p className="font-semibold text-gray-900">{formatDateTime(order.created_at)}</p>
                </div>
              </div>
            </div>

            {/* Failure Reason */}
            {order.status === 'failed' && order.failure_reason && (
              <div className="bg-red-50 rounded-xl border border-red-200 p-6">
                <h3 className="text-lg font-semibold text-red-800 mb-2 flex items-center">
                  <AlertCircle className="h-5 w-5 mr-2" />
                  Delivery Failed
                </h3>
                <p className="text-red-700">{order.failure_reason}</p>
                <p className="text-sm text-red-600 mt-2">Contact support to reschedule this delivery.</p>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Current Status Card */}
            <div className={cn('bg-white rounded-xl shadow-sm border border-gray-100 p-6 sticky top-24', statusColors[order.status])}>
              <div className="text-center">
                <div className={cn('w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center', statusColors[order.status].replace('bg-', 'bg-').replace('text-', 'text-'))}>
                  {statusIcons[order.status]}
                </div>
                <h3 className="text-xl font-bold">{statusLabels[order.status]}</h3>
                <p className="text-sm opacity-80 mt-1">{statusDescriptions[order.status]}</p>
                {history.length > 0 && history[0] && (
                  <p className="text-xs opacity-70 mt-2">
                    Updated: {formatDateTime(history[0].created_at)}
                  </p>
                )}
              </div>
            </div>

            {/* Status Update */}
            {allowedTransitions.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <h4 className="font-semibold text-gray-900 mb-4">Update Status</h4>
                <div className="space-y-2">
                  {allowedTransitions.map((nextStatus) => (
                    <button
                      key={nextStatus}
                      onClick={() => handleStatusUpdate(nextStatus)}
                      disabled={updatingStatus === nextStatus}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg text-left hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                      <div className="font-medium capitalize">{nextStatus.replace('_', ' ')}</div>
                      <div className="text-sm text-gray-500">
                        {statusDescriptions[nextStatus]}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Quick Info */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h4 className="font-semibold text-gray-900 mb-4">Quick Info</h4>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Order Number</span>
                  <span className="font-medium font-mono">{order.order_number}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Order Type</span>
                  <span className="font-medium capitalize">{order.order_type}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Payment Type</span>
                  <span className="font-medium capitalize">{order.payment_type}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Zone Type</span>
                  <span className="font-medium capitalize">{order.zone_type.replace('_', ' ')}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Created</span>
                  <span className="font-medium">{formatDateTime(order.created_at)}</span>
                </div>
                {order.picked_up_at && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Picked Up</span>
                    <span className="font-medium">{formatDateTime(order.picked_up_at)}</span>
                  </div>
                )}
                {order.delivered_at && (
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Delivered</span>
                    <span className="font-medium">{formatDateTime(order.delivered_at)}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h4 className="font-semibold text-gray-900 mb-4">Actions</h4>
              <div className="space-y-2">
                <Link
                  href="/agent/orders"
                  className="w-full inline-flex items-center justify-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Back to Dashboard
                </Link>
                <Link
                  href="/agent/tracking"
                  className="w-full inline-flex items-center justify-center px-4 py-2 border border-primary-300 rounded-lg text-sm font-medium text-primary-600 hover:bg-primary-50"
                >
                  <MapPinIcon className="h-4 w-4 mr-2" />
                  Track on Map
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}