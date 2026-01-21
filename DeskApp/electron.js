const { app, BrowserWindow, ipcMain, globalShortcut, desktopCapturer, screen, Notification } = require('electron');
const path = require('path');
const fs = require('fs');

// Import electron-store - it's an ES module, so we need to import it differently
let Store;
let store;

// Async initialization function
async function initializeStore() {
  Store = (await import('electron-store')).default;
  store = new Store({
    defaults: {
      buttonPosition: { x: 100, y: 100 },
      buttonVisible: true,
      captureShortcut: 'CommandOrControl+Shift+L'
    }
  });
}

let mainWindow = null;
let floatingButton = null;

// Backend URL - adjust as needed
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

// Ensure captures directory exists
const capturesDir = path.join(__dirname, 'captures', 'screenshots');
if (!fs.existsSync(capturesDir)) {
  fs.mkdirSync(capturesDir, { recursive: true });
}

// Create main dashboard window
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  // Load your Next.js app
  const startUrl = process.env.ELECTRON_START_URL || 'http://localhost:3000';
  mainWindow.loadURL(startUrl);

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Create floating capture button
function createFloatingButton() {
  // Get saved position or use default
  const savedPosition = store.get('buttonPosition');
  
  // Get primary display dimensions
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;
  
  // Ensure position is within screen bounds
  const x = Math.min(savedPosition.x, width - 90);
  const y = Math.min(savedPosition.y, height - 90);

  floatingButton = new BrowserWindow({
    width: 90,
    height: 90,
    x: x,
    y: y,
    frame: false,              // No window frame
    transparent: true,         // Transparent background
    alwaysOnTop: true,        // Always above other windows
    resizable: false,
    movable: true,
    skipTaskbar: true,        // Don't show in taskbar
    focusable: false,         // Don't steal focus
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  // Load the floating button HTML
  floatingButton.loadFile(path.join(__dirname, 'floating-button.html'));

  // Keep window on top with highest priority
  floatingButton.setAlwaysOnTop(true, 'screen-saver');
  floatingButton.setVisibleOnAllWorkspaces(true);

  // Set click-through for the window (allow clicking through transparent areas)
  floatingButton.setIgnoreMouseEvents(false);

  // Save position when window is moved
  floatingButton.on('moved', () => {
    const position = floatingButton.getPosition();
    store.set('buttonPosition', { x: position[0], y: position[1] });
  });

  floatingButton.on('closed', () => {
    floatingButton = null;
  });

  // Open DevTools in development (for debugging)
  if (process.env.NODE_ENV === 'development') {
    floatingButton.webContents.openDevTools({ mode: 'detach' });
  }
}

// Register global keyboard shortcut
function registerShortcuts() {
  const shortcut = store.get('captureShortcut');
  
  const registered = globalShortcut.register(shortcut, () => {
    console.log('Keyboard shortcut triggered:', shortcut);
    
    // Notify floating button to trigger capture
    if (floatingButton && !floatingButton.isDestroyed()) {
      floatingButton.webContents.send('capture-shortcut');
    }
  });

  if (registered) {
    console.log('✅ Keyboard shortcut registered:', shortcut);
  } else {
    console.log('❌ Failed to register keyboard shortcut:', shortcut);
  }
}

// Replace the getActiveWindowContext function in your electron.js with this:

// Get active window context using PowerShell (Windows)
async function getActiveWindowContext() {
  const context = {
    appName: 'Unknown',
    windowTitle: 'Unknown',
    url: null,
    timestamp: new Date().toISOString()
  };

  if (process.platform !== 'win32') {
    return context;
  }

  try {
    const { exec } = require('child_process');
    const { promisify } = require('util');
    const execAsync = promisify(exec);

    // Use external PowerShell script file (avoids escaping issues)
    const scriptPath = path.join(__dirname, 'get-window-context.ps1');
    
    const { stdout } = await execAsync(
      `powershell -ExecutionPolicy Bypass -File "${scriptPath}"`,
      { timeout: 5000 }
    );

    const result = JSON.parse(stdout.trim());
    context.appName = result.processName || 'Unknown';
    context.windowTitle = result.windowTitle || 'Unknown';

    // Try to get URL for browsers
    const browsers = ['chrome', 'msedge', 'brave', 'firefox', 'opera'];
    const isBrowser = browsers.some(b => 
      context.appName?.toLowerCase().includes(b)
    );
    
    if (isBrowser) {
      // For now, try to extract URL from window title (many browsers show it)
      // Full URL capture via clipboard can be added later
      const urlMatch = context.windowTitle.match(/https?:\/\/[^\s]+/);
      if (urlMatch) {
        context.url = urlMatch[0];
      }
    }

  } catch (error) {
    console.warn('⚠️ Could not get window context:', error.message);
  }

  return context;
}

// Get URL from browser using clipboard method
async function getBrowserUrl(browserProcess) {
  try {
    const { exec } = require('child_process');
    const { promisify } = require('util');
    const execAsync = promisify(exec);
    const { clipboard } = require('electron');

    // Save current clipboard
    const savedClipboard = clipboard.readText();

    // Simulate Ctrl+L, Ctrl+C, Escape to copy URL
    const psScript = `
      Add-Type -AssemblyName System.Windows.Forms
      Start-Sleep -Milliseconds 100
      [System.Windows.Forms.SendKeys]::SendWait("^l")
      Start-Sleep -Milliseconds 100
      [System.Windows.Forms.SendKeys]::SendWait("^c")
      Start-Sleep -Milliseconds 100
      [System.Windows.Forms.SendKeys]::SendWait("{ESC}")
    `;

    await execAsync(`powershell -Command "${psScript.replace(/"/g, '\\"').replace(/\n/g, ' ')}"`, {
      timeout: 2000
    });

    // Wait a bit for clipboard to update
    await new Promise(resolve => setTimeout(resolve, 200));

    // Get URL from clipboard
    const url = clipboard.readText();

    // Restore original clipboard
    clipboard.writeText(savedClipboard);

    // Validate it looks like a URL
    if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
      return url;
    }

  } catch (error) {
    console.warn('⚠️ Could not get browser URL:', error.message);
  }

  return null;
}

// Send capture to backend
async function sendToBackend(screenshotPath, context) {
  try {
    const FormData = (await import('form-data')).default;
    const fetch = (await import('node-fetch')).default;

    const form = new FormData();
    form.append('screenshot', fs.createReadStream(screenshotPath));
    form.append('app_name', context.appName || 'Unknown');
    form.append('window_title', context.windowTitle || 'Unknown');
    form.append('url', context.url || '');
    form.append('timestamp', context.timestamp);

    const response = await fetch(`${BACKEND_URL}/api/capture`, {
      method: 'POST',
      body: form,
      headers: form.getHeaders()
    });

    const result = await response.json();
    console.log('✅ Backend response:', result);
    return result;

  } catch (error) {
    console.error('❌ Backend error:', error.message);
    // Return a fallback response so the app doesn't crash
    return { success: false, error: error.message };
  }
}

// Handle screenshot capture
ipcMain.handle('capture-screenshot', async (event) => {
  console.log('📸 Capture screenshot requested');
  
  try {
    // FIRST: Get active window context BEFORE taking screenshot
    // This is important because the screenshot action might change focus
    const context = await getActiveWindowContext();
    console.log('📋 Window context:', context);

    // Small delay to let the context gathering complete
    await new Promise(resolve => setTimeout(resolve, 100));

    // Get all display sources (screens)
    const sources = await desktopCapturer.getSources({ 
      types: ['screen'],
      thumbnailSize: { width: 1920, height: 1080 }
    });
    
    if (sources.length === 0) {
      throw new Error('No screen sources available');
    }

    // Get primary screen
    const primarySource = sources[0];
    
    // Get screenshot as NativeImage
    const screenshot = primarySource.thumbnail;
    
    // Generate filename with timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `capture_${timestamp}.png`;
    const screenshotPath = path.join(capturesDir, filename);
    
    // Save screenshot to file
    fs.writeFileSync(screenshotPath, screenshot.toPNG());
    console.log('✅ Screenshot saved:', screenshotPath);

    // Send to backend (if available)
    let backendResult = null;
    try {
      backendResult = await sendToBackend(screenshotPath, context);
      console.log('✅ Sent to backend:', backendResult);
    } catch (backendError) {
      console.warn('⚠️ Backend unavailable:', backendError.message);
      // Continue without backend - save locally
    }

    // Show success notification
    showNotification('Screenshot Captured! 📸', context.windowTitle || 'Processing...');
    
    return { 
      success: true, 
      itemId: backendResult?.item_id || 'local_' + Date.now(),
      screenshotPath: screenshotPath,
      context: context,
      message: 'Screenshot captured successfully'
    };

  } catch (error) {
    console.error('❌ Capture failed:', error);
    showNotification('Capture Failed', error.message);
    
    return { 
      success: false, 
      error: error.message 
    };
  }
});

// Show desktop notification
function showNotification(title, body) {
  if (Notification.isSupported()) {
    new Notification({
      title: title,
      body: body,
      icon: path.join(__dirname, 'public', 'icon.png')
    }).show();
  }
}

// Handle window visibility toggle
ipcMain.on('toggle-button-visibility', (event, visible) => {
  if (floatingButton) {
    if (visible) {
      floatingButton.show();
    } else {
      floatingButton.hide();
    }
    store.set('buttonVisible', visible);
  }
});

// App lifecycle - INITIALIZE STORE FIRST
app.whenReady().then(async () => {
  console.log('🚀 LifeOS starting...');
  
  // IMPORTANT: Initialize electron-store first
  await initializeStore();
  console.log('✅ Store initialized');
  
  // Create main window
  createMainWindow();
  
  // Create floating button
  createFloatingButton();
  
  // Register keyboard shortcuts
  registerShortcuts();
  
  console.log('✅ LifeOS ready!');
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createMainWindow();
  }
  if (floatingButton === null) {
    createFloatingButton();
  }
});

app.on('will-quit', () => {
  // Unregister all shortcuts
  globalShortcut.unregisterAll();
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught exception:', error);
});