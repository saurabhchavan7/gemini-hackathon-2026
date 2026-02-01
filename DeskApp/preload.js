/**
 * preload.js - FIXED VERSION
 * No duplicates, clean structure
 */

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {

  // CAPTURE APIs
  getAuthToken: () => ipcRenderer.invoke('get-auth-token'),

  captureScreenshot: () => ipcRenderer.invoke('capture-screenshot'),
  
  showCaptureNotification: (data) =>
    ipcRenderer.invoke('show-capture-notification', data),


  sendCaptureToBackend: (payload) =>
    ipcRenderer.invoke('send-capture-to-backend', payload),

  sendCaptureFromNotification: (data) =>
    ipcRenderer.send('notification-send-capture', data),

  onCaptureShortcut: (callback) =>
    ipcRenderer.on('capture-shortcut', callback),

  onCaptureSentSuccess: (cb) =>
    ipcRenderer.on('capture-sent-success', cb),

  onCaptureSentFailed: (cb) =>
    ipcRenderer.on('capture-sent-failed', cb),

  onCaptureNotificationClosed: (cb) =>
    ipcRenderer.on('capture-notification-closed', cb),

  onCaptureData: (callback) =>
    ipcRenderer.on('capture-data', (_, data) => callback(data)),

  toggleButtonVisibility: (visible) => 
    ipcRenderer.send('toggle-button-visibility', visible),

  // AUTH APIs
  googleLogin: async () => {
    try {
      const result = await ipcRenderer.invoke('google-login');
      return result;
    } catch (error) {
      console.error('Login IPC error:', error);
      return { success: false, error: error.message };
    }
  },

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

  logout: async () => {
    try {
      const result = await ipcRenderer.invoke('logout');
      return result;
    } catch (error) {
      console.error('Logout IPC error:', error);
      return { success: false, error: error.message };
    }
  },

  checkAuth: async () => {
    try {
      const result = await ipcRenderer.invoke('check-auth');
      return result;
    } catch (error) {
      console.error('Check auth IPC error:', error);
      return { isAuthenticated: false, user: null };
    }
  },

  // PLATFORM INFO
  platform: process.platform,

  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
  }
});

console.log('✅ Preload script loaded');