const { contextBridge, ipcRenderer } = require('electron');

// Expose Electron APIs to React
contextBridge.exposeInMainWorld('electron', {
  // Capture screenshot
  captureScreen: () => ipcRenderer.invoke('capture-screen'),
  
  // Listen for global shortcut captures
  onScreenshotCaptured: (callback) => {
    ipcRenderer.on('screenshot-captured', (event, data) => callback(data));
  }
});