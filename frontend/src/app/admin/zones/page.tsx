'use client';

import { useAuthStore } from '@/store/auth';
import { Layout } from '@/components/Layout';
import { MapPin, Plus, Search, Map } from 'lucide-react';
import Link from 'next/link';

export default function AdminZonesPage() {
  const { user } = useAuthStore();

  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Zone Management</h1>
            <p className="text-gray-600">Manage delivery zones and their coverage areas</p>
          </div>
          <Link href="/admin/zones/new" className="px-4 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700">
            <Plus className="h-5 w-5 mr-2" />
            Add Zone
          </Link>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex flex-col md:flex-row gap-4 mb-6">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search zones..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>
          
          <div className="text-center py-12">
            <MapPin className="h-16 w-16 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500 text-lg">No zones configured</p>
            <p className="text-gray-400 mt-1">Create zones to define delivery coverage areas</p>
            <Link
              href="/admin/zones/new"
              className="mt-4 inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create First Zone
            </Link>
          </div>
        </div>
      </div>
    </Layout>
  );
}