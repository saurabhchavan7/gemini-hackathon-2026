/**
 * CloudRunClient.js
 * 
 * Purpose: Handles all HTTP communication with the FastAPI backend
 * 
 * Features:
 * - Centralized API client for all backend requests
 * - Automatic JWT token injection in headers
 * - Error handling with user-friendly messages
 * - Request/response interceptors
 * - Configurable base URL for local dev and production
 * 
 * Usage:
 * - Import and call methods: CloudRunClient.login(code)
 * - All methods return Promise with data or throw error
 */

const axios = require('axios');
const TokenManager = require('../auth/TokenManager');

// Backend URL - change this when backend is deployed to Cloud Run
// For local development: http://localhost:8000
// For production: https://lifeos-backend-xxxxx.run.app
const BASE_URL = process.env.BACKEND_URL || 'http://localhost:8000';

/**
 * Create axios instance with base configuration
 */
const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 30 second timeout
  headers: {
    'Content-Type': 'application/json',
  }
});

/**
 * Request interceptor - automatically adds JWT token to all requests
 */
apiClient.interceptors.request.use(
  async (config) => {
    // Get token from storage
    const token = await TokenManager.getToken();
    
    // Add Authorization header if token exists
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    console.log(`📤 API Request: ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ Request interceptor error:', error);
    return Promise.reject(error);
  }
);

/**
 * Response interceptor - handles common errors
 */
apiClient.interceptors.response.use(
  (response) => {
    console.log(`📥 API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  async (error) => {
    console.error('❌ API Error:', error.message);
    
    // Handle 401 Unauthorized - token expired or invalid
    if (error.response && error.response.status === 401) {
      console.log('🔐 Unauthorized - clearing token');
      await TokenManager.clearToken();
      // Could trigger a re-login flow here
    }
    
    return Promise.reject(error);
  }
);

/**
 * CloudRunClient - All API methods
 */
const CloudRunClient = {
  
  /**
   * Login with Google OAuth authorization code
   * @param {string} authCode - Authorization code from Google OAuth
   * @returns {Promise<object>} - { token, user: { email, name, picture } }
   */
  async login(authCode) {
    try {
      console.log('🔐 Sending authorization code to backend...');
      
      const response = await apiClient.post('/auth/google/login', {
        code: authCode
      });
      
      const { token, user } = response.data;
      
      // Save token and user info
      await TokenManager.saveToken(token);
      await TokenManager.saveUser(user);
      
      console.log('✅ Login successful:', user.email);
      return { token, user };
      
    } catch (error) {
      console.error('❌ Login failed:', error.message);
      
      // Provide user-friendly error messages
      if (error.response) {
        // Server responded with error
        throw new Error(error.response.data.detail || 'Login failed');
      } else if (error.request) {
        // No response from server
        throw new Error('Cannot reach backend server. Is it running?');
      } else {
        // Request setup error
        throw new Error('Failed to send login request');
      }
    }
  },

  /**
   * Get current user information
   * @returns {Promise<object>} - { email, name, picture, user_id }
   */
  async getCurrentUser() {
    try {
      console.log('👤 Fetching user info...');
      
      const response = await apiClient.get('/api/user/me');
      const user = response.data;
      
      // Update stored user info
      await TokenManager.saveUser(user);
      
      console.log('✅ User info retrieved:', user.email);
      return user;
      
    } catch (error) {
      console.error('❌ Failed to get user info:', error.message);
      
      if (error.response && error.response.status === 401) {
        throw new Error('Not authenticated. Please log in again.');
      }
      
      throw new Error('Failed to retrieve user information');
    }
  },

  /**
   * Upload capture (screenshot + context)
   * @param {object} captureData - { screenshot, timestamp, windowContext }
   * @returns {Promise<object>} - { item_id, message }
   */
  async uploadCapture(captureData) {
    try {
      console.log('📸 Uploading capture...');
      
      const response = await apiClient.post('/api/capture', captureData);
      
      console.log('✅ Capture uploaded:', response.data.item_id);
      return response.data;
      
    } catch (error) {
      console.error('❌ Failed to upload capture:', error.message);
      throw new Error('Failed to upload capture');
    }
  },

  /**
   * Get user's captures
   * @param {object} params - { limit, offset, filter }
   * @returns {Promise<array>} - Array of capture items
   */
  async getCaptures(params = {}) {
    try {
      console.log('📋 Fetching captures...');
      
      const response = await apiClient.get('/api/captures', { params });
      
      console.log(`✅ Retrieved ${response.data.length} captures`);
      return response.data;
      
    } catch (error) {
      console.error('❌ Failed to get captures:', error.message);
      throw new Error('Failed to retrieve captures');
    }
  },

  /**
   * Search captures
   * @param {string} query - Search query
   * @returns {Promise<array>} - Array of matching captures
   */
  async searchCaptures(query) {
    try {
      console.log('🔍 Searching captures:', query);
      
      const response = await apiClient.post('/api/search', { query });
      
      console.log(`✅ Found ${response.data.results.length} results`);
      return response.data.results;
      
    } catch (error) {
      console.error('❌ Search failed:', error.message);
      throw new Error('Search failed');
    }
  },

  /**
   * Health check - test backend connectivity
   * @returns {Promise<boolean>} - true if backend is reachable
   */
  async healthCheck() {
    try {
      await apiClient.get('/health');
      console.log('✅ Backend is healthy');
      return true;
    } catch (error) {
      console.error('❌ Backend health check failed:', error.message);
      return false;
    }
  }

};

module.exports = CloudRunClient;
