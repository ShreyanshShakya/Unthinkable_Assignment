'use client';

import { ReactNode, useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { Menu, X, LogOut, User, Package, Truck, Settings, Home, ClipboardList, MapPin, Users, DollarSign } from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const pathname = usePathname();
  const { user, isAuthenticated, clearAuth } = useAuthStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { name: 'Orders', href: '/dashboard/orders', icon: Package },
    { name: 'Tracking', href: '/dashboard/tracking', icon: MapPin },
  ];

  const adminNavigation = [
    { name: 'Dashboard', href: '/admin', icon: Home },
    { name: 'Orders', href: '/admin/orders', icon: ClipboardList },
    { name: 'Agents', href: '/admin/agents', icon: Users },
    { name: 'Zones', href: '/admin/zones', icon: MapPin },
    { name: 'Rates', href: '/admin/rates', icon: DollarSign },
    { name: 'Settings', href: '/admin/settings', icon: Settings },
  ];

  const agentNavigation = [
    { name: 'Dashboard', href: '/agent', icon: Home },
    { name: 'My Orders', href: '/agent/orders', icon: Package },
    { name: 'Availability', href: '/agent/availability', icon: Settings },
  ];

  const getNavigation = () => {
    if (!user) return navigation;
    switch (user.role) {
      case 'admin':
        return adminNavigation;
      case 'agent':
        return agentNavigation;
      default:
        return navigation;
    }
  };

  const handleLogout = () => {
    clearAuth();
    window.location.href = '/login';
  };

  if (!isAuthenticated && pathname !== '/login' && pathname !== '/register') {
    return null; // Will redirect via middleware
  }

  const navItems = getNavigation();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-40 bg-white border-b border-gray-200">
        <div className="flex items-center justify-between h-16 px-4">
          <button
            onClick={() => setMobileMenuOpen(true)}
            className="p-2 rounded-lg text-gray-500 hover:bg-gray-100"
            aria-label="Open menu"
          >
            <Menu className="h-6 w-6" />
          </button>
          <Link href="/" className="text-xl font-bold text-primary-600">
            LastMile
          </Link>
          <div className="w-10" />
        </div>
      </header>

      {/* Mobile sidebar */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-50 bg-black/50" onClick={() => setMobileMenuOpen(false)}>
          <div className="fixed inset-y-0 left-0 w-64 bg-white shadow-xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex flex-col h-full">
              <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200">
                <Link href="/" className="text-xl font-bold text-primary-600">
                  LastMile
                </Link>
                <button
                  onClick={() => setMobileMenuOpen(false)}
                  className="p-2 rounded-lg text-gray-500 hover:bg-gray-100"
                  aria-label="Close menu"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              <nav className="flex-1 px-4 py-4 space-y-2 overflow-y-auto">
                {navItems.map((item) => (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      pathname === item.href
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <item.icon className="h-5 w-5 mr-3" />
                    {item.name}
                  </Link>
                ))}
              </nav>
              <div className="p-4 border-t border-gray-200">
                <div className="flex items-center px-3 py-2 mb-2">
                  <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                    <span className="text-sm font-medium text-primary-600">
                      {user?.full_name?.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
                    <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <LogOut className="h-5 w-5 mr-3" />
                  Sign out
                </button>
              </div>
              </div>
    </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <aside className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:z-40 lg:w-64 lg:bg-white lg:border-r lg:border-gray-200">
        <div className="flex flex-col h-full">
          <div className="flex items-center h-16 px-6 border-b border-gray-200">
            <Link href="/" className="text-xl font-bold text-primary-600">
              LastMile
            </Link>
          </div>
          <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
            {navItems.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  pathname === item.href
                    ? 'bg-primary-50 text-primary-600'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <item.icon className="h-5 w-5 mr-3" />
                {item.name}
              </Link>
            ))}
          </nav>
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center px-3 py-2 mb-2">
              <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                <span className="text-sm font-medium text-primary-600">
                  {user?.full_name?.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="ml-3 flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{user?.full_name}</p>
                <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <LogOut className="h-5 w-5 mr-3" />
              Sign out
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="lg:ml-64 min-h-screen">
        <div className="pt-16 lg:pt-0 px-4 py-8">
          {children}
        </div>
      </main>
    </div>
  );
}