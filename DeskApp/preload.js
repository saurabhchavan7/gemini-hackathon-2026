const { contextBridge, ipcRenderer } = require('electron');

// Expose Electron APIs to renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  // Capture screenshot
  captureScreenshot: () => ipcRenderer.invoke('capture-screenshot'),
  
  // Listen for keyboard shortcut
  onCaptureShortcut: (callback) => ipcRenderer.on('capture-shortcut', callback),
  
  // Toggle button visibility (for future settings)
  toggleButtonVisibility: (visible) => ipcRenderer.send('toggle-button-visibility', visible),
  
  // Platform info
  platform: process.platform,
  
  // Version info
  versions: {
    node: process.versions.node,
    chrome: process.versions.chrome,
    electron: process.versions.electron
  }
});

console.log('✅ Preload script loaded');