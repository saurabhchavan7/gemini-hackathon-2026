const { app, BrowserWindow, ipcMain, desktopCapturer, globalShortcut } = require('electron');
const path = require('path');

let mainWindow;


function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  // Load from development server
  mainWindow.loadURL('http://localhost:3000');
  mainWindow.webContents.openDevTools();

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();

  // Register global shortcut: Ctrl+Shift+L
  globalShortcut.register('CommandOrControl+Shift+L', async () => {
    console.log('Global shortcut triggered: Ctrl+Shift+L');
    const result = await captureScreen();
    if (mainWindow && result.success) {
      mainWindow.webContents.send('screenshot-captured', result);
    }
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
});

// Screenshot capture function
async function captureScreen() {
  try {
    const sources = await desktopCapturer.getSources({
      types: ['screen'],
      thumbnailSize: { width: 1920, height: 1080 }
    });

    if (sources.length === 0) {
      return {
        success: false,
        error: 'No screen sources available'
      };
    }

    const primaryScreen = sources[0];
    const screenshot = primaryScreen.thumbnail.toDataURL();

    // Get active window info
    const activeWindow = {
      title: mainWindow?.getTitle() || 'Unknown',
      app: 'Electron'
    };

    return {
      success: true,
      screenshot: screenshot,
      timestamp: Date.now(),
      windowContext: activeWindow
    };
  } catch (error) {
    console.error('Screenshot capture failed:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

// IPC Handler: Capture screenshot
ipcMain.handle('capture-screen', captureScreen);