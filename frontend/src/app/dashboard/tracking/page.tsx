'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Layout } from '@/components/Layout';
import { MapPin, Package, Truck, CheckCircle, Clock, ArrowLeft, ExternalLink, AlertCircle } from 'lucide-react';
import api from '@/lib/api';
import { cn, formatDateTime } from '@/lib/utils';

interface Order {
  id: string;
  order_number: string;
  status: string;
  pickup_address: string;
  drop_address: string;
  pickup_city?: string;
  drop_city?: string;
  pickup_state?: string;
  drop_state?: string;
  pickup_pincode: string;
  drop_pincode: string;
  created_at: string;
}

interface HistoryEntry {
  id: string;
  new_status: string;
  actor_role: string;
  reason?: string;
  created_at: string;
}

const statuses = ['created', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered'];
const labels: Record<string, string> = {
  created: 'Order Created',
  picked_up: 'Picked Up',
  in_transit: 'In Transit',
  out_for_delivery: 'Out for Delivery',
  delivered: 'Delivered',
  failed: 'Delivery Failed',
};

export default function TrackingPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const response = await api.get('/orders');
        const list: Order[] = response.data.orders || [];
        setOrders(list);
        if (list.length) setSelectedId(list[0].id);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Unable to load shipments.');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    api.get(`/orders/${selectedId}/tracking`)
      .then(response => setHistory(response.data || []))
      .catch(() => setHistory([]));
  }, [selectedId]);

  const order = orders.find(o => o.id === selectedId);
  const currentIndex = order ? statuses.indexOf(order.status) : -1;
  const mapUrl = order
    ? `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(`${order.pickup_address}, ${order.pickup_city || ''}, ${order.pickup_state || ''} ${order.pickup_pincode}`)}&destination=${encodeURIComponent(`${order.drop_address}, ${order.drop_city || ''}, ${order.drop_state || ''} ${order.drop_pincode}`)}`
    : '#';

  if (loading) return <Layout><div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent" /></div></Layout>;

  return (
    <Layout>
      <div className="max-w-5xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Link href="/dashboard" className="text-gray-500 hover:text-gray-700 inline-flex items-center mb-2"><ArrowLeft className="h-5 w-5 mr-1" /> Back to Dashboard</Link>
            <h1 className="text-2xl font-bold text-gray-900">Track Shipment</h1>
            <p className="text-gray-600 mt-1">View the current shipment status and route.</p>
          </div>
        </div>

        {error && <div className="p-4 rounded-lg bg-red-50 text-red-700 flex items-center"><AlertCircle className="h-5 w-5 mr-2" />{error}</div>}

        {orders.length === 0 ? (
          <div className="bg-white rounded-xl border p-10 text-center"><Package className="h-12 w-12 mx-auto text-gray-300 mb-3" /><p className="text-gray-600">No shipments available to track.</p></div>
        ) : (
          <>
            <div className="bg-white rounded-xl border p-5">
              <label className="block text-sm font-medium text-gray-700 mb-2">Shipment</label>
              <select value={selectedId} onChange={e => setSelectedId(e.target.value)} className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 bg-white">
                {orders.map(o => <option key={o.id} value={o.id}>{o.order_number} — {o.status.replaceAll('_', ' ')}</option>)}
              </select>
            </div>

            {order && <>
              <div className="bg-white rounded-xl border p-6">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
                  <div><p className="text-sm text-gray-500">Order</p><h2 className="text-xl font-bold text-gray-900">{order.order_number}</h2></div>
                  <span className="px-3 py-1 rounded-full bg-blue-100 text-blue-800 text-sm font-medium w-fit">{labels[order.status] || order.status.replaceAll('_', ' ')}</span>
                </div>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-lg bg-blue-50"><p className="text-xs text-blue-600 font-medium mb-1">PICKUP</p><p className="font-medium text-gray-900">{order.pickup_address}</p><p className="text-sm text-gray-600">{order.pickup_city}, {order.pickup_state} — {order.pickup_pincode}</p></div>
                  <div className="p-4 rounded-lg bg-green-50"><p className="text-xs text-green-600 font-medium mb-1">DROP</p><p className="font-medium text-gray-900">{order.drop_address}</p><p className="text-sm text-gray-600">{order.drop_city}, {order.drop_state} — {order.drop_pincode}</p></div>
                </div>
              </div>

              <div className="bg-white rounded-xl border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-5">Shipment Progress</h2>
                <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                  {statuses.map((status, index) => {
                    const done = currentIndex >= index;
                    const event = history.find(h => h.new_status === status);
                    return <div key={status} className={cn('rounded-lg border p-4', done ? 'border-primary-200 bg-primary-50' : 'border-gray-200 bg-gray-50')}>
                      <div className="flex items-center gap-2 mb-2">{done ? <CheckCircle className="h-5 w-5 text-primary-600" /> : <Clock className="h-5 w-5 text-gray-400" />}<span className={cn('text-sm font-medium', done ? 'text-gray-900' : 'text-gray-500')}>{labels[status]}</span></div>
                      {event && <p className="text-xs text-gray-500">{formatDateTime(event.created_at)}</p>}
                    </div>;
                  })}
                </div>
              </div>

              <div className="bg-white rounded-xl border overflow-hidden">
                <div className="p-5 border-b"><h2 className="text-lg font-semibold text-gray-900 flex items-center"><MapPin className="h-5 w-5 text-primary-600 mr-2" /> Route Map</h2></div>
                <div className="h-64 bg-gray-100 flex flex-col items-center justify-center text-center p-6">
                  <Truck className="h-12 w-12 text-primary-600 mb-3" />
                  <p className="font-medium text-gray-900">Pickup → Destination</p>
                  <p className="text-sm text-gray-500 mt-1">Open the route in Google Maps for directions.</p>
                  <a href={mapUrl} target="_blank" rel="noreferrer" className="mt-4 inline-flex items-center px-4 py-2 rounded-lg bg-primary-600 text-white font-medium hover:bg-primary-700"><ExternalLink className="h-4 w-4 mr-2" /> Open Map</a>
                </div>
              </div>
            </>}
          </>
        )}
      </div>
    </Layout>
  );
}
