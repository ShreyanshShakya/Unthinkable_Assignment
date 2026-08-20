'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Mail, Lock, AlertCircle, Eye, EyeOff, Truck } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true);
    setError('');
    try {
      await login(data.email, data.password);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <Link href="/" className="inline-flex items-center justify-center">
            <div className="h-12 w-12 rounded-xl bg-primary-600 flex items-center justify-center">
              <Truck className="h-8 w-8 text-white" />
            </div>
          </Link>
          <h2 className="mt-6 text-3xl font-bold text-gray-900">Sign in to your account</h2>
          <p className="mt-2 text-sm text-gray-600">
            Or{' '}
            <Link href="/register" className="font-medium text-primary-600 hover:text-primary-500">
              create a new account
            </Link>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
          {error && (
            <div className="flex items-center p-3 rounded-lg bg-red-50 text-red-600 text-sm">
              <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0" />
              {error}
            </div>
          )}

          <div className="rounded-lg border border-gray-300 bg-white">
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
              <input
                {...register('email')}
                type="email"
                placeholder="Email address"
                className="block w-full pl-10 pr-3 py-3 border-0 focus:ring-0 focus:border-0 text-gray-900 placeholder-gray-500"
              />
            </div>
            <div className="border-t border-gray-200" />
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
              <input
                {...register('password')}
                type={showPassword ? 'text' : 'password'}
                placeholder="Password"
                className="block w-full pl-10 pr-10 py-3 border-0 focus:ring-0 focus:border-0 text-gray-900 placeholder-gray-500"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
          </div>

          {errors.email && (
            <p className="text-sm text-red-600">{errors.email.message}</p>
          )}
          {errors.password && (
            <p className="text-sm text-red-600">{errors.password.message}</p>
          )}

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="remember"
                name="remember"
                type="checkbox"
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="remember" className="ml-2 block text-sm text-gray-900">
                Remember me
              </label>
            </div>
            <Link href="/forgot-password" className="text-sm font-medium text-primary-600 hover:text-primary-500">
              Forgot password?
            </Link>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <div className="text-center text-sm text-gray-600">
          <p>Demo credentials:</p>
          <p className="text-xs mt-1">customer@test.com / password123</p>
          <p className="text-xs">agent@test.com / password123</p>
          <p className="text-xs">admin@test.com / password123</p>
        </div>
      </div>
    </div>
  );
}