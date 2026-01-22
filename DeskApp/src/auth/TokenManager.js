/**
 * TokenManager.js
 * 
 * Purpose: Manages JWT token storage, retrieval, and validation for user authentication
 * 
 * Features:
 * - Saves JWT token to persistent storage using electron-store
 * - Retrieves token for API requests
 * - Checks if user is authenticated
 * - Validates token expiration
 * - Clears token on logout
 * 
 * Storage Location: Uses electron-store (stores in OS-specific app data directory)
 * - Windows: %APPDATA%\lifeos\config.json
 * - macOS: ~/Library/Application Support/lifeos/config.json
 * - Linux: ~/.config/lifeos/config.json
 */

// Note: electron-store must be imported dynamically since it's an ES module
let Store;
let store;

/**
 * Initialize the store (must be called before using any methods)
 */
async function initStore() {
  if (!store) {
    Store = (await import('electron-store')).default;
    store = new Store({
      name: 'auth',
      defaults: {
        token: null,
        tokenExpiration: null,
        user: null
      }
    });
  }
}

/**
 * Save JWT token to persistent storage
 * @param {string} token - JWT token from backend
 * @returns {boolean} - Success status
 */
async function saveToken(token) {
  try {
    await initStore();
    
    // Decode JWT to get expiration (without verification, just reading)
    const payload = JSON.parse(Buffer.from(token.split('.')[1], 'base64').toString());
    const expirationTimestamp = payload.exp * 1000; // Convert to milliseconds
    
    // Save token and expiration
    store.set('token', token);
    store.set('tokenExpiration', expirationTimestamp);
    
    console.log('✅ Token saved successfully');
    console.log('📅 Token expires:', new Date(expirationTimestamp).toLocaleString());
    
    return true;
  } catch (error) {
    console.error('❌ Failed to save token:', error);
    return false;
  }
}

/**
 * Retrieve stored JWT token
 * @returns {string|null} - JWT token or null if not found
 */
async function getToken() {
  try {
    await initStore();
    const token = store.get('token');
    
    if (!token) {
      console.log('ℹ️ No token found');
      return null;
    }
    
    // Check if token is expired
    if (isTokenExpired()) {
      console.log('⚠️ Token expired, clearing...');
      await clearToken();
      return null;
    }
    
    return token;
  } catch (error) {
    console.error('❌ Failed to retrieve token:', error);
    return null;
  }
}

/**
 * Check if token exists and is valid (not expired)
 * @returns {boolean} - True if user is authenticated
 */
async function isAuthenticated() {
  const token = await getToken();
  return token !== null;
}

/**
 * Check if stored token is expired
 * @returns {boolean} - True if token is expired
 */
function isTokenExpired() {
  try {
    const expiration = store.get('tokenExpiration');
    
    if (!expiration) {
      return true;
    }
    
    const now = Date.now();
    const isExpired = now >= expiration;
    
    if (isExpired) {
      console.log('⏰ Token expired at:', new Date(expiration).toLocaleString());
    }
    
    return isExpired;
  } catch (error) {
    console.error('❌ Failed to check token expiration:', error);
    return true; // Assume expired on error
  }
}

/**
 * Save user information
 * @param {object} user - User data (email, name, picture)
 */
async function saveUser(user) {
  try {
    await initStore();
    store.set('user', user);
    console.log('✅ User info saved:', user.email);
  } catch (error) {
    console.error('❌ Failed to save user:', error);
  }
}

/**
 * Get stored user information
 * @returns {object|null} - User data or null
 */
async function getUser() {
  try {
    await initStore();
    return store.get('user');
  } catch (error) {
    console.error('❌ Failed to retrieve user:', error);
    return null;
  }
}

/**
 * Clear all authentication data (logout)
 * @returns {boolean} - Success status
 */
async function clearToken() {
  try {
    await initStore();
    store.delete('token');
    store.delete('tokenExpiration');
    store.delete('user');
    console.log('✅ Authentication data cleared');
    return true;
  } catch (error) {
    console.error('❌ Failed to clear token:', error);
    return false;
  }
}

/**
 * Get time until token expires
 * @returns {number} - Milliseconds until expiration, or 0 if expired
 */
function getTimeUntilExpiration() {
  try {
    const expiration = store.get('tokenExpiration');
    if (!expiration) return 0;
    
    const now = Date.now();
    const timeLeft = expiration - now;
    
    return timeLeft > 0 ? timeLeft : 0;
  } catch (error) {
    console.error('❌ Failed to get expiration time:', error);
    return 0;
  }
}

// Export all functions
module.exports = {
  saveToken,
  getToken,
  isAuthenticated,
  isTokenExpired,
  saveUser,
  getUser,
  clearToken,
  getTimeUntilExpiration
};
