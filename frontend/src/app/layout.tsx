import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/context/AuthContext';

export const metadata: Metadata = {
  title: 'Last Mile Delivery Tracker',
  description: 'Track and manage last-mile deliveries',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased"><AuthProvider>{children}</AuthProvider></body>
    </html>
  );
}