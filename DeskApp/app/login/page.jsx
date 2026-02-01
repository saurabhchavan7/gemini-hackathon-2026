/**
 * app/login/page.jsx
 * 
 * Purpose: Login page with Google OAuth integration
 * 
 * Flow:
 * 1. User clicks "Sign in with Google" button
 * 2. Calls window.electronAPI.googleLogin() via IPC
 * 3. Electron opens browser for OAuth consent
 * 4. Backend exchanges code for JWT token
 * 5. Token stored locally, user redirected to dashboard
 * 
 * States:
 * - idle: Ready to login
 * - loading: OAuth flow in progress
 * - error: Login failed (shows error message)
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Login() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

 /**
 * Check if already authenticated on mount
 * If yes, redirect to inbox
 */
useEffect(() => {
  checkExistingAuth();
}, []);

/**
 * Check for existing authentication
 */
const checkExistingAuth = async () => {
  try {
    if (!window.electronAPI) return;
    
    const authStatus = await window.electronAPI.checkAuth();
    
    if (authStatus.isAuthenticated) {
      console.log('✅ Already authenticated, redirecting...');
      router.push('/inbox');  // Changed from '/' to '/inbox'
    }
  } catch (err) {
    console.log('ℹ️ Not authenticated, showing login');
  }
};

  /**
   * Handle Google Sign-In button click
   * Triggers full OAuth flow
   */
  const handleGoogleSignIn = async () => {
    setLoading(true);
    setError(null);

    try {
      console.log('🔐 Starting login...');
      
      // Call Electron IPC to start OAuth flow
      const result = await window.electronAPI.googleLogin();
      
      if (result.success) {
        console.log('✅ Login successful!');
        console.log('👤 User:', result.user.email);
        
        // Redirect to dashboard using Next.js router
        router.push('/inbox');

        
      } else {
        // Login failed
        throw new Error(result.error || 'Login failed');
      }
      
    } catch (err) {
      console.error('❌ Login error:', err);
      setError(err.message || 'Failed to sign in. Please try again.');
      
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md">
        
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">LifeOS</h1>
          <p className="text-gray-600">Your AI-powered cognitive assistant</p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-3">
              <span className="text-red-600 text-xl">⚠️</span>
              <div>
                <p className="text-sm font-medium text-red-800">Login Failed</p>
                <p className="text-sm text-red-600 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Google Sign-In Button */}
        <button
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="w-full flex items-center justify-center gap-3 bg-white border-2 border-gray-300 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-50 hover:border-gray-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
        >
          {loading ? (
            <>
              <div className="w-5 h-5 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin" />
              <span>Signing in...</span>
            </>
          ) : (
            <>
              {/* Google Logo SVG */}
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              <span>Sign in with Google</span>
            </>
          )}
        </button>

        {/* Loading Status Text */}
        {loading && (
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-600">
              Please complete the login in your browser...
            </p>
          </div>
        )}

        {/* Terms */}
        <p className="text-center text-sm text-gray-500 mt-6">
          By signing in, you agree to our Terms of Service
        </p>

        {/* Debug Info (only in development) */}
        {process.env.NODE_ENV === 'development' && (
          <div className="mt-6 p-3 bg-gray-100 rounded text-xs text-gray-600">
            <p>🔧 Development Mode</p>
            <p className="mt-1">Backend: http://localhost:3001</p>
          </div>
        )}
      </div>
    </div>
  );
}