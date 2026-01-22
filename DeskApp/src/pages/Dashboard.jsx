/**
 * Dashboard.jsx
 * 
 * Purpose: Main application dashboard shown after successful login
 * 
 * Features:
 * - Displays user profile (email, name, picture) in header
 * - Logout functionality
 * - Loading states while fetching user data
 * - Error handling with redirect to login on auth failure
 * - Placeholder for future capture list/feed
 * 
 * Flow:
 * 1. Component mounts → fetch user info from backend
 * 2. Display user profile in header
 * 3. Main content area ready for captures/tasks
 * 4. Logout clears token and redirects to login
 */

import React, { useState, useEffect } from 'react';

export default function Dashboard() {
  // State management
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Fetch user information on component mount
   */
  useEffect(() => {
    fetchUserInfo();
  }, []);

  /**
   * Get current user data from backend
   */
  const fetchUserInfo = async () => {
    try {
      setLoading(true);
      setError(null);

      // Call backend via IPC (will implement in electron.js)
      const userData = await window.electronAPI.getCurrentUser();
      
      setUser(userData);
      console.log('✅ User data loaded:', userData.email);
      
    } catch (err) {
      console.error('❌ Failed to load user:', err);
      setError(err.message);
      
      // If authentication fails, redirect to login
      // (Will implement navigation later)
      setTimeout(() => {
        window.location.href = '/login';
      }, 2000);
      
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle logout - clear token and redirect
   */
  const handleLogout = async () => {
    try {
      console.log('🚪 Logging out...');
      
      // Clear authentication via IPC
      await window.electronAPI.logout();
      
      // Redirect to login
      window.location.href = '/login';
      
    } catch (err) {
      console.error('❌ Logout failed:', err);
      alert('Failed to logout. Please try again.');
    }
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Authentication Error</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <p className="text-sm text-gray-500">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  /**
   * Main dashboard view
   */
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with user profile */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            
            {/* Logo/Title */}
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">LifeOS</h1>
              <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">Beta</span>
            </div>

            {/* User Profile Section */}
            <div className="flex items-center gap-4">
              
              {/* User Info */}
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-gray-900">{user?.name || 'User'}</p>
                <p className="text-xs text-gray-500">{user?.email}</p>
              </div>

              {/* Profile Picture */}
              {user?.picture ? (
                <img 
                  src={user.picture} 
                  alt="Profile"
                  className="w-10 h-10 rounded-full border-2 border-gray-300"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
                  {user?.name?.charAt(0) || 'U'}
                </div>
              )}

              {/* Logout Button */}
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Welcome Message */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Welcome back, {user?.name?.split(' ')[0] || 'User'}! 👋
          </h2>
          <p className="text-gray-600">
            Your AI-powered cognitive assistant is ready to help you capture and organize your digital life.
          </p>
        </div>

        {/* Quick Stats (Placeholder) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Captures</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">0</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <span className="text-2xl">📸</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending Tasks</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">0</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <span className="text-2xl">✅</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">This Week</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">0</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <span className="text-2xl">📊</span>
              </div>
            </div>
          </div>

        </div>

        {/* Captures Feed (Placeholder) */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Captures</h3>
          
          {/* Empty State */}
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📸</div>
            <h4 className="text-lg font-medium text-gray-900 mb-2">No captures yet</h4>
            <p className="text-gray-600 mb-4">
              Use the floating button or press <kbd className="px-2 py-1 bg-gray-100 border border-gray-300 rounded text-sm">Ctrl+Shift+L</kbd> to capture anything on your screen
            </p>
          </div>
        </div>

      </main>
    </div>
  );
}
