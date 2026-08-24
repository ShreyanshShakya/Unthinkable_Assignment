'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, MapPin, Package, Scale, DollarSign, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { Layout } from '@/components/Layout';
import { formatCurrency } from '@/lib/utils';
import api from '@/lib/api';

const orderSchema = z.object({
  pickup_address: z.string().min(5, 'Address must be at least 5 characters'),
  pickup_pincode: z.string().min(4, 'Valid pincode required'),
  pickup_city: z.string().optional(), pickup_state: z.string().optional(),
  drop_address: z.string().min(5, 'Address must be at least 5 characters'),
  drop_pincode: z.string().min(4, 'Valid pincode required'),
  drop_city: z.string().optional(), drop_state: z.string().optional(),
  length_cm: z.number().min(1, 'Length required'), breadth_cm: z.number().min(1, 'Breadth required'),
  height_cm: z.number().min(1, 'Height required'), actual_weight_kg: z.number().min(0.1, 'Weight required'),
  order_type: z.enum(['b2b', 'b2c']), payment_type: z.enum(['prepaid', 'cod']),
  order_value: z.number().min(0, 'Order value required'),
});

type OrderForm = z.infer<typeof orderSchema>;
type Pricing = { volumetric_weight_kg: number; billable_weight_kg: number; zone_type: string; base_charge: number; cod_surcharge: number; total_charge: number; applied_rule?: string; applied_cod_surcharge?: string };
type QuoteResult = { success: boolean; pricing?: Pricing; breakdown?: Pricing; pickup_zone?: { id: string; name: string; code: string }; drop_zone?: { id: string; name: string; code: string }; error?: string };

const fieldClass = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white placeholder-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-primary-500';
const labelClass = 'block text-sm font-medium text-gray-700 mb-1';

export default function CreateOrderPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [isGettingQuote, setIsGettingQuote] = useState(false);
  const [quote, setQuote] = useState<QuoteResult | null>(null);
  const [error, setError] = useState('');
  const { register, handleSubmit, getValues, formState: { errors } } = useForm<OrderForm>({
    resolver: zodResolver(orderSchema),
    defaultValues: { order_type: 'b2c', payment_type: 'prepaid', order_value: 0 },
  });

  const getQuote = async () => {
    setError(''); setQuote(null);
    const validation = orderSchema.safeParse(getValues());
    if (!validation.success) { setError(validation.error.issues[0]?.message || 'Please complete all required fields.'); return; }
    setIsGettingQuote(true);
    try { const response = await api.post('/orders/quote', validation.data); setQuote(response.data); }
    catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((x: any) => x.msg).join(', ') : 'Unable to calculate the quote.');
    } finally { setIsGettingQuote(false); }
  };

  const onSubmit = async (data: OrderForm) => {
    setIsLoading(true); setError('');
    try { const response = await api.post('/orders', data); router.push(`/dashboard/orders/${response.data.id}`); }
    catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((x: any) => x.msg).join(', ') : `Failed to create order (${err.response?.status || 'network error'}).`);
    } finally { setIsLoading(false); }
  };

  const pricing = quote?.pricing || quote?.breakdown;

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-8">
        <div><Link href="/dashboard" className="text-gray-500 hover:text-gray-700 mb-2 inline-flex items-center"><ArrowLeft className="h-5 w-5 mr-1" /> Back to Dashboard</Link><h1 className="text-2xl font-bold text-gray-900">Create New Order</h1><p className="text-gray-600 mt-1">Fill in the details below to create a new shipment</p></div>
        {error && <div className="flex items-start p-4 rounded-lg bg-red-50 text-red-700 border border-red-100"><AlertCircle className="h-5 w-5 mr-2 mt-0.5 flex-shrink-0" /><span>{error}</span></div>}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
          <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6"><h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center"><MapPin className="h-5 w-5 text-primary-600 mr-2" /> Pickup Details</h2><div className="grid grid-cols-1 md:grid-cols-2 gap-4"><div className="md:col-span-2"><label className={labelClass}>Pickup Address *</label><textarea {...register('pickup_address')} rows={2} className={fieldClass} placeholder="Complete pickup address" />{errors.pickup_address && <p className="mt-1 text-sm text-red-600">{errors.pickup_address.message}</p>}</div><div><label className={labelClass}>Pincode *</label><input {...register('pickup_pincode')} type="text" inputMode="numeric" maxLength={10} className={fieldClass} placeholder="e.g., 110001" />{errors.pickup_pincode && <p className="mt-1 text-sm text-red-600">{errors.pickup_pincode.message}</p>}</div><div><label className={labelClass}>City</label><input {...register('pickup_city')} type="text" className={fieldClass} /></div><div><label className={labelClass}>State</label><input {...register('pickup_state')} type="text" className={fieldClass} /></div></div></section>
          <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6"><h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center"><MapPin className="h-5 w-5 text-primary-600 mr-2" /> Drop Details</h2><div className="grid grid-cols-1 md:grid-cols-2 gap-4"><div className="md:col-span-2"><label className={labelClass}>Drop Address *</label><textarea {...register('drop_address')} rows={2} className={fieldClass} placeholder="Complete drop address" />{errors.drop_address && <p className="mt-1 text-sm text-red-600">{errors.drop_address.message}</p>}</div><div><label className={labelClass}>Pincode *</label><input {...register('drop_pincode')} type="text" inputMode="numeric" maxLength={10} className={fieldClass} placeholder="e.g., 400001" />{errors.drop_pincode && <p className="mt-1 text-sm text-red-600">{errors.drop_pincode.message}</p>}</div><div><label className={labelClass}>City</label><input {...register('drop_city')} type="text" className={fieldClass} /></div><div><label className={labelClass}>State</label><input {...register('drop_state')} type="text" className={fieldClass} /></div></div></section>
          <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6"><h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center"><Package className="h-5 w-5 text-primary-600 mr-2" /> Package Details</h2><div className="grid grid-cols-1 md:grid-cols-4 gap-4"><div><label className={labelClass}>Length (cm) *</label><input {...register('length_cm', { valueAsNumber: true })} type="number" step="0.1" min="1" className={fieldClass} />{errors.length_cm && <p className="mt-1 text-sm text-red-600">{errors.length_cm.message}</p>}</div><div><label className={labelClass}>Breadth (cm) *</label><input {...register('breadth_cm', { valueAsNumber: true })} type="number" step="0.1" min="1" className={fieldClass} />{errors.breadth_cm && <p className="mt-1 text-sm text-red-600">{errors.breadth_cm.message}</p>}</div><div><label className={labelClass}>Height (cm) *</label><input {...register('height_cm', { valueAsNumber: true })} type="number" step="0.1" min="1" className={fieldClass} />{errors.height_cm && <p className="mt-1 text-sm text-red-600">{errors.height_cm.message}</p>}</div><div><label className={labelClass}>Actual Weight (kg) *</label><input {...register('actual_weight_kg', { valueAsNumber: true })} type="number" step="0.1" min="0.1" className={fieldClass} />{errors.actual_weight_kg && <p className="mt-1 text-sm text-red-600">{errors.actual_weight_kg.message}</p>}</div></div></section>
          <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6"><h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center"><Scale className="h-5 w-5 text-primary-600 mr-2" /> Order Classification</h2><div className="grid grid-cols-1 md:grid-cols-3 gap-4"><div><label className={labelClass}>Order Type *</label><select {...register('order_type')} className={fieldClass}><option value="b2c">B2C (Business to Consumer)</option><option value="b2b">B2B (Business to Business)</option></select></div><div><label className={labelClass}>Payment Type *</label><select {...register('payment_type')} className={fieldClass}><option value="prepaid">Prepaid</option><option value="cod">Cash on Delivery (COD)</option></select></div><div><label className={labelClass}>Order Value *</label><input {...register('order_value', { valueAsNumber: true })} type="number" step="0.01" min="0" className={fieldClass} placeholder="Order value" />{errors.order_value && <p className="mt-1 text-sm text-red-600">{errors.order_value.message}</p>}</div></div></section>
          <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6"><div className="flex items-center justify-between gap-4"><div><h2 className="text-lg font-semibold text-gray-900 flex items-center"><DollarSign className="h-5 w-5 text-primary-600 mr-2" /> Price Quote</h2><p className="text-sm text-gray-500 mt-1">Calculate the shipping charge before placing the order.</p></div><button type="button" onClick={getQuote} disabled={isGettingQuote} className="btn-primary whitespace-nowrap">{isGettingQuote ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Calculating...</> : 'Get Quote'}</button></div>
            {quote?.success && pricing && <div className="mt-6 rounded-lg border border-green-100 bg-green-50 p-5"><div className="flex items-center text-green-700 font-medium mb-4"><CheckCircle className="h-5 w-5 mr-2" /> Quote calculated successfully</div><div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm"><div><p className="text-gray-500">Zone</p><p className="font-semibold text-gray-900">{pricing.zone_type}</p></div><div><p className="text-gray-500">Billable Weight</p><p className="font-semibold text-gray-900">{pricing.billable_weight_kg} kg</p></div><div><p className="text-gray-500">Base Charge</p><p className="font-semibold text-gray-900">{formatCurrency(pricing.base_charge)}</p></div><div><p className="text-gray-500">Total</p><p className="font-bold text-green-700 text-lg">{formatCurrency(pricing.total_charge)}</p></div></div></div>}
          </section>
          <div className="flex justify-end gap-3 pb-8"><Link href="/dashboard" className="btn-secondary">Cancel</Link><button type="submit" disabled={isLoading} className="btn-primary min-w-36">{isLoading ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Creating...</> : 'Create Order'}</button></div>
        </form>
      </div>
    </Layout>
  );
}
