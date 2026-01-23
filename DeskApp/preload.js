/**
 * preload.js
 * 
 * Purpose: Bridge between Electron main process and renderer (React/Next.js)
 * 
 * Security:
 * - Uses contextBridge to safely expose APIs
 * - Prevents direct Node.js access from renderer
 * - Only exposes specific, controlled functions
 * 
 * Available APIs:
 * - Screenshot capture (existing)
 * - OAuth login flow (new)
 * - User authentication (new)
 * - Logout (new)
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose Electron APIs to renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  
  // ============================================
  // EXISTING CAPTURE APIs (keep these)
  // ============================================
  
  /**
   * Capture screenshot with context
   * @returns {Promise<object>} - Capture result
   */
  captureScreenshot: () => ipcRenderer.invoke('capture-screenshot'),
  
  /**
   * Listen for keyboard shortcut trigger
   * @param {function} callback - Function to call when shortcut pressed
   */
  onCaptureShortcut: (callback) => ipcRenderer.on('capture-shortcut', callback),
  
  /**
   * Toggle floating button visibility
   * @param {boolean} visible - Show/hide button
   */
  toggleButtonVisibility: (visible) => ipcRenderer.send('toggle-button-visibility', visible),
  
  // ============================================
  // NEW OAUTH & AUTH APIs
  // ============================================
  
  /**
   * Start Google OAuth login flow
   * Opens browser, returns user data on success
   * @returns {Promise<object>} - { success: boolean, user?: object, error?: string }
   */
  googleLogin: async () => {
    try {
      const result = await ipcRenderer.invoke('google-login');
      return result;
    } catch (error) {
      console.error('Login IPC error:', error);
      return { success: false, error: error.message };
    }
  },
  
  /**
   * Get current authenticated user
   * @returns {Promise<object>} - User data or error
   */
  getCurrentUser: async () => {
    try {
      const result = await ipcRenderer.invoke('get-current-user');
      
      if (result.success) {
        return result.user;
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      console.error('Get user IPC error:', error);
      throw error;
    }
  },
  
  /**
   * Logout and clear authentication
   * @returns {Promise<object>} - { success: boolean }
   */
  logout: async () => {
    try {
      const result = await ipcRenderer.invoke('logout');
      return result;
    } catch (error) {
      console.error('Logout IPC error:', error);
      return { success: false, error: error.message };
    }
  },
  
  /**
   * Check if user is authenticated
   * @returns {Promise<object>} - { isAuthenticated: boolean, user?: object }
   */
  checkAuth: async () => {
    try {
      const result = await ipcRenderer.invoke('check-auth');
      return result;
    } catch (error) {
      console.error('Check auth IPC error:', error);
      return { isAuthenticated: false, user: null };
    }
  },
  
  // ============================================
  // PLATFORM INFO (keep these)
  // ============================================
  
  /**
   * Get platform information
   */
  platform: process.platform,
  
  /**
   * Get version information
   */
  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
  }
});

console.log('✅ Preload script loaded with OAuth support');