/**
 * preload.js - FIXED VERSION
 * No duplicates, clean structure
 */

const getBackendUrl = () => {
  // This will be injected from main process
  console.log('Backend URL from env:', process.env.BACKEND_URL);
  return process.env.BACKEND_URL;
};
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {

  apiGetCollections: () => ipcRenderer.invoke('api-get-collections'),

  apiGetThemeClusters: (numClusters) => 
  ipcRenderer.invoke('api-get-theme-clusters', numClusters),

  apiAskQuestion: (question, filterDomain) => 
  ipcRenderer.invoke('api-ask-question', question, filterDomain),

  onProactiveNotificationData: (callback) =>
  ipcRenderer.on('proactive-notification-data', (_, data) => callback(data)),
 
  apiGetCaptureById: (captureId) => ipcRenderer.invoke('api-get-capture-by-id', captureId),
  apiGetCaptureByIdV2: (captureId) => ipcRenderer.invoke('api-get-capture-v2', captureId),

  apiAskCapture: (captureId, question) => 
  ipcRenderer.invoke('api-ask-capture', captureId, question),

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

  openFileDialog: () =>
    ipcRenderer.invoke('open-file-dialog'),

  // TEXT NOTE APIs
openTextNoteWindow: () =>
    ipcRenderer.invoke('open-text-note-window'),

sendTextNote: (data) =>
    ipcRenderer.invoke('send-text-note', data),

onTextNoteData: (callback) =>
    ipcRenderer.on('text-note-data', (_, data) => callback(data)),

// AUDIO NOTE APIs
openAudioNoteWindow: () =>
    ipcRenderer.invoke('open-audio-note-window'),

sendAudioNote: (data) =>
    ipcRenderer.invoke('send-audio-note', data),

onAudioNoteData: (callback) =>
    ipcRenderer.on('audio-note-data', (_, data) => callback(data)),

getAppLogo: () => ({
  publicPath:
    process.env.APP_LOGO_PUBLIC_PATH || "/logo.png",
}),

  /**
   * Upload a file to the backend (PDF/DOCX)
   * @param {Object} opts - { path, name, size, type }
   * @returns {Promise<Object>} - { success, ... }
   */
  // uploadFileToBackend: async (opts) => {

  //   // Read file as buffer from main process
  //   const buffer = await ipcRenderer.invoke('read-file-buffer', opts.path);
  //   if (!buffer) return { success: false, error: 'Failed to read file' };
  //   // Get JWT token
  //   const token = await ipcRenderer.invoke('get-auth-token');
  //   if (!token) return { success: false, error: 'Not authenticated' };
  //   // Prepare FormData
  //   const formData = new FormData();
  //   const file = new File([buffer], opts.name, { type: opts.type });
  //   formData.append('file', file);
  //   // Optionally add capture_id if needed
  //   // formData.append('capture_id', ...);
  //   // Send to backend
  //   try {
  //     const res = await fetch('https://lifeos-backend-1056690364460.us-central1.run.app/api/upload-file', {
  //       method: 'POST',
  //       headers: { 'Authorization': `Bearer ${token}` },
  //       body: formData
  //     });
  //     const data = await res.json();
  //     return data;
  //   } catch (err) {
  //     return { success: false, error: err.message };
  //   }
  // },


  uploadFileToBackend: async (opts) => {
  const buffer = await ipcRenderer.invoke('read-file-buffer', opts.path);
  if (!buffer) return { success: false, error: 'Failed to read file' };
  
  const token = await ipcRenderer.invoke('get-auth-token');
  if (!token) return { success: false, error: 'Not authenticated' };
  
  const formData = new FormData();
  const file = new File([buffer], opts.name, { type: opts.type });
  formData.append('file', file);
  
  const backendUrl = getBackendUrl();
  console.log('📤 [PRELOAD] Uploading file to:', backendUrl);
  
  try {
    const res = await fetch(`${backendUrl}/api/upload-file`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
    const data = await res.json();
    return data;
  } catch (err) {
    console.error('❌ [PRELOAD] Upload failed:', err);
    return { success: false, error: err.message };
  }
},

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

  apiGetInbox: (params) => ipcRenderer.invoke('api-get-inbox', params),
  apiGetCaptureById: (captureId) => ipcRenderer.invoke('api-get-capture', captureId),

  // PLATFORM INFO
  platform: process.platform,

  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
  }
});

console.log('✅ Preload script loaded');