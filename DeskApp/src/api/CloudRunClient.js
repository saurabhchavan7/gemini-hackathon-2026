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

// Backend URL - reads from environment variable
const BASE_URL = process.env.BACKEND_URL || 'https://lifeos-backend-1056690364460.us-central1.run.app';


console.log('🌐 [CloudRunClient] Using backend:', BASE_URL);
/**
 * Create axios instance with base configuration
 */
const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 60000, // 60 second timeout
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

      const token = await TokenManager.getToken();
      if (!token) {
        throw new Error('No token available');
      }

      const response = await fetch(`${BASE_URL}/api/user/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log('📥 Raw response status:', response.status);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const user = await response.json();   // ✅ THIS WAS MISSING

      // Validate payload
      if (!user || !user.email) {
        throw new Error('Invalid user payload');
      }

      await TokenManager.saveUser(user);

      console.log('✅ User info retrieved:', user.email);
      return user;

    } catch (error) {
      console.error('❌ Failed to get user info:', error.message);
      throw new Error('Failed to retrieve user information');
    }
  }
  ,

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
  },

  /**
 * Get inbox items (captures/memories)
 * @param {object} params - { limit, filter_intent, filter_domain }
 * @returns {Promise<array>} - Array of memory items
 */
async getInbox(params = {}) {
  try {
    const { limit = 50, filter_intent, filter_domain } = params;
    
    console.log('📥 [CloudRunClient] Fetching inbox from:', BASE_URL);
    
    const queryParams = new URLSearchParams();
    if (limit) queryParams.append('limit', limit);
    if (filter_intent) queryParams.append('filter_intent', filter_intent);
    if (filter_domain) queryParams.append('filter_domain', filter_domain);
    
    const response = await apiClient.get(`/api/inbox?${queryParams}`);
    
    console.log(`✅ [CloudRunClient] Retrieved ${response.data.memories?.length || 0} items`);
    
    return {
      success: true,
      items: response.data.memories || [],
      total: response.data.total || 0
    };
    
  } catch (error) {
    console.error('❌ [CloudRunClient] Failed to get inbox:', error.message);
    
    if (error.response?.status === 401) {
      throw new Error('Unauthorized - please login again');
    }
    
    throw new Error('Failed to retrieve inbox items');
  }
},

/**
 * Get single capture by ID
 * @param {string} captureId - Capture ID
 * @returns {Promise<object>} - Capture details
 */
async getCaptureById(captureId) {
  try {
    console.log('📄 [CloudRunClient] Fetching capture:', captureId);
    
    const response = await apiClient.get(`/api/capture/${captureId}/full`);
    
    console.log('✅ [CloudRunClient] Capture retrieved');
    
    return {
      success: true,
      capture: response.data.capture
    };
    
  } catch (error) {
    console.error('❌ [CloudRunClient] Failed to get capture:', error.message);
    throw new Error('Failed to retrieve capture details');
  }
},

async getCollections() {
  try {
    console.log('📁 [CloudRunClient] Fetching collections');
    
    const response = await apiClient.get('/api/collections');
    
    console.log(`✅ [CloudRunClient] Retrieved ${response.data.collections?.length || 0} collections`);
    
    return {
      success: true,
      collections: response.data.collections || [],
      total: response.data.total || 0
    };
    
  } catch (error) {
    console.error('❌ [CloudRunClient] Failed to get collections:', error.message);
    throw new Error('Failed to retrieve collections');
  }
},

async getThemeClusters(numClusters = 4) {
  try {
    console.log('🎨 [CloudRunClient] Fetching theme clusters');
    
    const response = await apiClient.get(`/api/synthesis/clusters?num_clusters=${numClusters}`);
    
    console.log(`✅ [CloudRunClient] Retrieved ${response.data.clusters?.length || 0} clusters`);
    
    return {
      success: true,
      clusters: response.data.clusters || [],
      total: response.data.total || 0,
      message: response.data.message
    };
    
  } catch (error) {
    console.error('❌ [CloudRunClient] Failed to get theme clusters:', error.message);
    throw new Error('Failed to retrieve theme clusters');
  }
},

async askQuestion(question, filterDomain = null, token = null) {
  try {
    console.log('🤔 [CloudRunClient] Asking question:', question);
    
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const FormData = require('form-data');
    const form = new FormData();
    form.append('question', question);
    if (filterDomain) {
      form.append('filter_domain', filterDomain);
    }
    
    const response = await apiClient.post('/api/ask', form, {
      headers: {
        ...form.getHeaders(),
        'Authorization': `Bearer ${token}`
      }
    });
    
    console.log('✅ [CloudRunClient] Got answer');
    
    return {
      success: true,
      question: response.data.question,
      answer: response.data.answer,
      sources: response.data.sources || [],
      confidence: response.data.confidence || 'medium'
    };
    
  } catch (error) {
    console.error('❌ [CloudRunClient] Failed to ask question:', error.message);
    throw new Error('Failed to get answer');
  }
},

async getProactiveNotifications() {
  try {
    console.log('🔔 [CloudRunClient] Fetching proactive notifications');
    
    const response = await apiClient.get('/api/notifications/proactive');
    
    console.log(`✅ [CloudRunClient] Got ${response.data.notifications?.length || 0} notifications`);
    
    return {
      success: true,
      notifications: response.data.notifications || [],
      count: response.data.count || 0
    };
    
  } catch (error) {
    console.error('❌ [CloudRunClient] Failed to get notifications:', error.message);
    return { success: false, notifications: [], count: 0 };
  }
},

async getCaptureById(captureId) {
  try {
    console.log(`🔍 [CloudRunClient] Fetching capture: ${captureId}`);
    const response = await apiClient.get(`/api/capture/${captureId}/full`);
    return { success: true, capture: response.data.capture };
  } catch (error) {
    console.error('❌ [CloudRunClient] Failed:', error.message);
    return { success: false, error: error.message };
  }
},

async getCaptureByIdV2(captureId) {
  try {
    console.log(`🔍 [CloudRunClient V2] Fetching enhanced capture: ${captureId}`);
    const response = await apiClient.get(`/api/v2/capture/${captureId}/full`);
    console.log(`✅ [CloudRunClient V2] Got ${response.data.metadata.research_sources_count} research sources`);
    console.log(`📚 [CloudRunClient V2] Got ${response.data.metadata.resources_count} learning resources`);
    return { success: true, capture: response.data.capture, metadata: response.data.metadata };
  } catch (error) {
    console.error('❌ [CloudRunClient V2] Failed:', error.message);
    return { success: false, error: error.message };
  }
},



};

module.exports = CloudRunClient;
