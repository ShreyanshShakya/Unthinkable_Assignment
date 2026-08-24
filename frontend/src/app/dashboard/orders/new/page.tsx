'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuthStore } from '@/store/auth';
import { Layout } from '@/components/Layout';
import { ArrowLeft, MapPin, Package, Scale, DollarSign, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { cn, formatCurrency } from '@/lib/utils';
import api from '@/lib/api';
import Link from 'next/link';

const orderSchema = z.object({
  pickup_address: z.string().min(5, 'Address must be at least 5 characters'),
  pickup_pincode: z.string().min(4, 'Valid pincode required'),
  pickup_city: z.string().optional(),
  pickup_state: z.string().optional(),
  drop_address: z.string().min(5, 'Address must be at least 5 characters'),
  drop_pincode: z.string().min(4, 'Valid pincode required'),
  drop_city: z.string().optional(),
  drop_state: z.string().optional(),
  length_cm: z.number().min(1, 'Length required'),
  breadth_cm: z.number().min(1, 'Breadth required'),
  height_cm: z.number().min(1, 'Height required'),
  actual_weight_kg: z.number().min(0.1, 'Weight required'),
  order_type: z.enum(['b2b', 'b2c']),
  payment_type: z.enum(['prepaid', 'cod']),
  order_value: z.number().min(0, 'Order value required'),
});

type OrderForm = z.infer<typeof orderSchema>;

interface QuoteResult {
  success: boolean;
  pricing?: {
    volumetric_weight_kg: number;
    billable_weight_kg: number;
    zone_type: string;
    base_charge: number;
    cod_surcharge: number;
    total_charge: number;
    applied_rule?: string;
    applied_cod_surcharge?: string;
  };
  pickup_zone?: { id: string; name: string; code: string };
  drop_zone?: { id: string; name: string; code: string };
  error?: string;
}

export default function CreateOrderPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [quote, setQuote] = useState<QuoteResult | null>(null);
  const [isGettingQuote, setIsGettingQuote] = useState(false);
  const [error, setError] = useState('');

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<OrderForm>({
    resolver: zodResolver(orderSchema),
    defaultValues: {
      order_type: 'b2c',
      payment_type: 'prepaid',
      order_value: 0,
    },
  });

  const paymentType = watch('payment_type');
  const orderValue = watch('order_value');

  const getQuote = async (data: Partial<OrderForm>) => {
    if (!data.pickup_pincode || !data.drop_pincode || !data.length_cm || !data.breadth_cm || !data.height_cm || !data.actual_weight_kg) {
      return;
    }
    setIsGettingQuote(true);
    try {
      const response = await api.post('/orders/quote', {
        ...data,
        order_type: data.order_type || 'b2c',
        payment_type: data.payment_type || 'prepaid',
        order_value: data.order_value || 0,
      });
      setQuote(response.data);
    } catch (err: any) {
      setQuote({ success: false, error: err.response?.data?.detail || 'Failed to get quote' });
    } finally {
      setIsGettingQuote(false);
    }
  };

  // Auto-fetch quote when key fields change
  useEffect(() => {
    const subscription = watch((value, { name }) => {
      if (['pickup_pincode', 'drop_pincode', 'length_cm', 'breadth_cm', 'height_cm', 'actual_weight_kg', 'order_type', 'payment_type', 'order_value'].includes(name || '')) {
        const formData = { ...watch() };
        if (formData.pickup_pincode && formData.drop_pincode && formData.length_cm && formData.breadth_cm && formData.height_cm && formData.actual_weight_kg) {
          getQuote(formData);
        }
      }
    });
    return () => subscription.unsubscribe();
  }, [watch]);

  const onSubmit = async (data: OrderForm) => {
    setIsLoading(true);
    setError('');
    try {
      const response = await api.post('/orders', data);
      router.push(`/dashboard/orders/${response.data.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create order');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <Link href="/dashboard" className="text-gray-500 hover:text-gray-700 mb-2 inline-flex items-center">
              <ArrowLeft className="h-5 w-5 mr-1" />
              Back to Dashboard
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">Create New Order</h1>
            <p className="text-gray-600 mt-1">Fill in the details below to create a new shipment</p>
          </div>
        </div>

        {error && (
          <div className="flex items-center p-4 rounded-lg bg-red-50 text-red-600">
            <AlertCircle className="h-5 w-5 mr-2" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
          {/* Pickup Details */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
              <MapPin className="h-5 w-5 text-primary-600 mr-2" />
              Pickup Details
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Pickup Address *</label>
                <textarea
                  {...register('pickup_address')}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Complete pickup address"
                />
                {errors.pickup_address && <p className="mt-1 text-sm text-red-600">{errors.pickup_address.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Pincode *</label>
                <input
                  {...register('pickup_pincode', { valueAsNumber: true })}
                  type="number"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="e.g., 110001"
                />
                {errors.pickup_pincode && <p className="mt-1 text-sm text-red-600">{errors.pickup_pincode.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
                <input
                  {...register('pickup_city')}
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
                <input
                  {...register('pickup_state')}
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>
          </div>

          {/* Drop Details */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
              <MapPin className="h-5 w-5 text-primary-600 mr-2" />
              Drop Details
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Drop Address *</label>
                <textarea
                  {...register('drop_address')}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Complete drop address"
                />
                {errors.drop_address && <p className="mt-1 text-sm text-red-600">{errors.drop_address.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Pincode *</label>
                <input
                  {...register('drop_pincode', { valueAsNumber: true })}
                  type="number"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="e.g., 400001"
                />
                {errors.drop_pincode && <p className="mt-1 text-sm text-red-600">{errors.drop_pincode.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
                <input
                  {...register('drop_city')}
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
                <input
                  {...register('drop_state')}
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>
          </div>

          {/* Package Details */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
              <Package className="h-5 w-5 text-primary-600 mr-2" />
              Package Details
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Length (cm) *</label>
                <input
                  {...register('length_cm', { valueAsNumber: true })}
                  type="number"
                  step="0.1"
                  min="1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
                {errors.length_cm && <p className="mt-1 text-sm text-red-600">{errors.length_cm.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Breadth (cm) *</label>
                <input
                  {...register('breadth_cm', { valueAsNumber: true })}
                  type="number"
                  step="0.1"
                  min="1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
                {errors.breadth_cm && <p className="mt-1 text-sm text-red-600">{errors.breadth_cm.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Height (cm) *</label>
                <input
                  {...register('height_cm', { valueAsNumber: true })}
                  type="number"
                  step="0.1"
                  min="1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
                {errors.height_cm && <p className="mt-1 text-sm text-red-600">{errors.height_cm.message}</p>}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Actual Weight (kg) *</label>
                <input
                  {...register('actual_weight_kg', { valueAsNumber: true })}
                  type="number"
                  step="0.1"
                  min="0.1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
                {errors.actual_weight_kg && <p className="mt-1 text-sm text-red-600">{errors.actual_weight_kg.message}</p>}
              </div>
            </div>
          </div>

          {/* Order Classification */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
              <Scale className="h-5 w-5 text-primary-600 mr-2" />
              Order Classification
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Order Type *</label>
                <select
                  {...register('order_type')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="b2c">B2C (Business to Consumer)</option>
                  <option value="b2b">B2B (Business to Business)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Payment Type *</label>
                <select
                  {...register('payment_type')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="prepaid">Prepaid</option>
                  <option value="cod">Cash on Delivery (COD)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Order Value *</label>
                <input
                  {...register('order_value', { valueAsNumber: true })}
                  type="number"
                  step="0.01"
                  min="0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Enter order value for COD calculation"
                />
                {errors.order_value && <p className="mt-1 text-sm text-red-600">{errors.order_value.message}</p>}
              </div>
            </div>
          </div>

          {/* Price Quote */}
          {(quote || isGettingQuote) && (
            <div className={cn('bg-white rounded-xl shadow-sm border border-gray-100 p-6 transition-all', isGettingQuote ? 'opacity-50' : '')}>
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <DollarSign className="h-5 w-5 text-primary-600 mr-2" />
                Price Quote
                {isGettingQuote && (
                  <Loader2 className="h-5 w-5 ml-2 animate-spin text-primary-600" />
                )}
                {!isGettingQuote && quote?.success && (
                  <CheckCircle className="h-5 w-5 ml-2 text-green-600" />
                )}
                {!isGettingQuote && !quote?.success && (
                  <AlertCircle className="h-5 w-5 ml-2 text-red-600" />
                )}
              </h2>
              
              {!isGettingQuote && !quote?.success && (
                <div className="text-red-600 text-sm">{quote?.error}</div>
              )}
              
              {!isGettingQuote && quote?.success && quote?.pricing && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-500">Volumetric Weight</p>
                    <p className="text-xl font-bold text-gray-900">{quote.pricing.volumetric_weight_kg} kg</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-500">Billable Weight</p>
                    <p className="text-xl font-bold text-gray-900">{quote.pricing.billable_weight_kg} kg</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-500">Zone Type</p>
                    <p className="text-xl font-bold text-gray-900 capitalize">{quote.pricing.zone_type.replace('_', ' ')}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-500">Base Charge</p>
                    <p className="text-xl font-bold text-gray-900">{formatCurrency(quote.pricing.base_charge)}</p>
                  </div>
                  {quote.pricing.cod_surcharge > 0 && (
                    <div className="bg-yellow-50 rounded-lg p-4 md:col-span-2">
                      <p className="text-sm text-yellow-700">COD Surcharge</p>
                      <p className="text-xl font-bold text-yellow-700">{formatCurrency(quote.pricing.cod_surcharge)}</p>
                      <p className="text-xs text-yellow-600 mt-1">{quote.pricing.applied_cod_surcharge}</p>
                    </div>
                  )}
                  <div className="bg-primary-50 rounded-lg p-4">
                    <p className="text-sm text-primary-700">Total Charge</p>
                    <p className="text-2xl font-bold text-primary-700">{formatCurrency(quote.pricing.total_charge)}</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Submit */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Ready to ship?</h3>
                <p className="text-gray-500 mt-1">Review the details and create your order</p>
              </div>
              <button
                type="submit"
                disabled={isLoading || isGettingQuote}
                className="px-8 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 flex items-center"
              >
                {isLoading && <Loader2 className="h-5 w-5 mr-2 animate-spin" />}
                {isLoading ? 'Creating...' : 'Create Order'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </Layout>
  );
}