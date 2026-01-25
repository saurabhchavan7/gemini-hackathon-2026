/**
 * OAuth IPC Handlers for electron.js
 * 
 * Purpose: Add these handlers to your existing electron.js file
 * 
 * Instructions:
 * 1. Add these imports at the top of electron.js (after existing imports)
 * 2. Add these IPC handlers before app.whenReady()
 * 
 * These handlers allow the renderer process (React) to:
 * - Trigger Google OAuth login
 * - Get current user info
 * - Logout
 */

const GoogleAuth = require('./src/auth/GoogleAuth');
const TokenManager = require('./src/auth/TokenManager');
const CloudRunClient = require('./src/api/CloudRunClient');
const { app, BrowserWindow, ipcMain, globalShortcut, desktopCapturer, screen, Notification } = require('electron');
const path = require('path');
const fs = require('fs');

// Import electron-store - it's an ES module, so we need to import it differently
let Store;
let store;
let notificationWindow = null;

const audioDir = path.join(__dirname, 'captures', 'audio');
if (!fs.existsSync(audioDir)) {
  fs.mkdirSync(audioDir, { recursive: true });
}

let audioPath = null;

ipcMain.on('notification-send-capture', async (event, payload) => {
  console.log('📥 Capture received from notification');

  let audioPath = null;
  const transcript = payload.audioTranscript || null;

  try {
    // ✅ SAVE AUDIO FIRST
    if (payload.audioBuffer) {
      const audioFilename = `audio_${Date.now()}.webm`;
      audioPath = path.join(audioDir, audioFilename);

      fs.writeFileSync(
        audioPath,
        Buffer.from(payload.audioBuffer)
      );

      console.log('🎧 Audio saved:', audioPath);
    }

    // ✅ SEND FILE PATHS ONLY
    const result = await sendToBackend(
      payload.screenshotPath,
      payload.context,
      audioPath,
      payload.textNote || null,
      transcript
    );

    console.log('✅ Backend response:', result);

    // notify floating button safely
    if (floatingButton && !floatingButton.isDestroyed()) {
      floatingButton.webContents.send('capture-sent-success');
    }

  } catch (err) {
    console.error('❌ Failed to send capture:', err);

    if (floatingButton && !floatingButton.isDestroyed()) {
      floatingButton.webContents.send('capture-sent-failed');
    }
  }

  if (notificationWindow && !notificationWindow.isDestroyed()) {
    notificationWindow.close();
  }
  notificationWindow = null;
});



ipcMain.on('show-capture-notification', (event, data) => {
  console.log('🔔 Creating capture notification window...');

  // Close any existing notification safely
  if (notificationWindow && !notificationWindow.isDestroyed()) {
    notificationWindow.close();
  }
  notificationWindow = null;

  notificationWindow = new BrowserWindow({
    width: 420,
    height: 360,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    skipTaskbar: true,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      devTools: true
      // IMPORTANT: do NOT add sandbox:true
    }
  });

  // Bottom-right like Teams
  const display = screen.getPrimaryDisplay();
  const { x, y, width, height } = display.workArea;
  const margin = 16;
  notificationWindow.setPosition(
    x + width - 420 - margin,
    y + height - 360 - margin
  );

  const notificationPath = path.join(__dirname, 'src', 'components', 'CaptureNotification.html');
  console.log('📄 Loading notification from:', notificationPath);

  // If load fails, log it clearly
  notificationWindow.webContents.on('did-fail-load', (e, code, desc) => {
    console.error('❌ Notification did-fail-load:', code, desc);
  });

  // If renderer throws JS errors, surface them
  notificationWindow.webContents.on('console-message', (e, level, message) => {
    console.log('🧩 Notification console:', message);
  });

  notificationWindow.loadFile(notificationPath).then(() => {
    // This always runs once loadFile finishes
    notificationWindow.webContents.send('capture-data', data);
    notificationWindow.show(); // doesn't steal focus
    console.log('✅ Notification window shown');
  }).catch((err) => {
    console.error('❌ Failed to load notification file:', err);
    if (notificationWindow && !notificationWindow.isDestroyed()) {
      notificationWindow.webContents.openDevTools();
    }
  });

  notificationWindow.on('closed', () => {
    notificationWindow = null;
  });
});



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
async function createMainWindow() {
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
  //const startUrl = process.env.ELECTRON_START_URL || 'http://localhost:3000';
  const isAuthenticated = await TokenManager.isAuthenticated();

  const startUrl = isAuthenticated
    ? 'http://localhost:3000/inbox'
    : 'http://localhost:3000/login';

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
    width: 400,  // ← Wider to fit horizontal menu
    height: 160,// ← Changed from 90 (to fit menu)
    x: x,
    y: y,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    movable: true,
    skipTaskbar: true,
    focusable: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  // Load the floating button HTML
  floatingButton.loadFile(path.join(__dirname, 'src', 'components', 'floating-button.html'));

  floatingButton.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('❌ Floating button failed to load:', errorCode, errorDescription);
  });

  floatingButton.webContents.on('did-finish-load', () => {
    console.log('✅ Floating button loaded successfully');
  });
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
// Send capture to backend (PATHS ONLY)
async function sendToBackend(screenshotPath, context, audioPath, textNote, audioTranscript) {
  try {
    const FormData = (await import('form-data')).default;
    const fetch = (await import('node-fetch')).default;

    // Get JWT token
    const token = await TokenManager.getToken();

    if (!token) {
      console.warn('⚠️ No JWT token found, skipping backend upload');
      return { success: false, error: 'Not authenticated' };
    }

    const form = new FormData();

    // ✅ REQUIRED — backend expects this
    form.append('screenshot_path', screenshotPath);

    // ✅ OPTIONAL metadata (keep as-is if backend uses them)
    if (context?.appName) form.append('app_name', context.appName);
    if (context?.windowTitle) form.append('window_title', context.windowTitle);
    if (context?.url) form.append('url', context.url);
    if (context?.timestamp) form.append('timestamp', context.timestamp);
    if (textNote) form.append('text_note', textNote);
    if (audioPath) form.append('audio_path', audioPath);
    if (audioTranscript) form.append('audio_transcript', audioTranscript);


    const headers = {
      ...form.getHeaders(),
      Authorization: `Bearer ${token}`
    };

    const response = await fetch(`${BACKEND_URL}/api/capture`, {
      method: 'POST',
      body: form,
      headers
    });

    const result = await response.json();
    console.log('✅ Backend response:', result);
    return result;

  } catch (error) {
    console.error('❌ Backend error:', error.message);
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

    // // Send to backend (if available)
    // let backendResult = null;
    // try {
    //   backendResult = await sendToBackend(screenshotPath, context);
    //   console.log('✅ Sent to backend:', backendResult);
    // } catch (backendError) {
    //   console.warn('⚠️ Backend unavailable:', backendError.message);
    //   // Continue without backend - save locally
    // }

    // Show success notification
    showNotification('Screenshot Captured! 📸', context.windowTitle || 'Processing...');

    // return {
    //   success: true,
    //   itemId: backendResult?.item_id || 'local_' + Date.now(),
    //   screenshotPath: screenshotPath,
    //   context: context,
    //   message: 'Screenshot captured successfully'
    // };

    return {
      success: true,
      screenshotPath,
      context,
      capturedAt: Date.now()
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

ipcMain.handle('send-capture-to-backend', async (event, payload) => {
  const { screenshotPath, context } = payload;

  try {
    const result = await sendToBackend(screenshotPath, context, audioPath);
    return { success: true, result };
  } catch (err) {
    return { success: false, error: err.message };
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

/**
 * Handle Google OAuth login flow
 * Called from Login.jsx when user clicks "Sign in with Google"
 */
ipcMain.handle('google-login', async (event) => {
  try {
    console.log('🔐 Starting Google OAuth flow...');

    // Step 1: Open browser and get authorization code
    const authCode = await GoogleAuth.startOAuthFlow();
    console.log('✅ Got authorization code');

    // Step 2: Send code to backend, get JWT token
    const { token, user } = await CloudRunClient.login(authCode);
    console.log('✅ Login successful:', user.email);

    return {
      success: true,
      user: user
    };

  } catch (error) {
    console.error('❌ Login failed:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

/**
 * Get current user information
 * Called from Dashboard.jsx on mount
 */
ipcMain.handle('get-current-user', async (event) => {
  try {
    console.log('👤 Getting current user...');


    // Check if authenticated first
    const isAuth = await TokenManager.isAuthenticated();
    console.log('🔐 Is authenticated?', isAuth);

    // Fetch user from backend
    const token = await TokenManager.getToken();
    console.log('🔐 JWT token exists?', !!token);

    //const user = await CloudRunClient.getCurrentUser();

    if (!isAuth) {
      console.log('🚫 Not authenticated, skipping user fetch');
      return { success: false };
    }

    const user = await CloudRunClient.getCurrentUser();


    return {
      success: true,
      user: user
    };

  } catch (error) {
    console.error('❌ Failed to get user:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

/**
 * Handle logout
 * Called from Dashboard.jsx logout button
 */
ipcMain.handle('logout', async (event) => {
  try {
    console.log('🚪 Logging out...');

    // Clear all authentication data
    await TokenManager.clearToken();

    console.log('✅ Logout successful');

    return {
      success: true
    };

  } catch (error) {
    console.error('❌ Logout failed:', error);
    return {
      success: false,
      error: error.message
    };
  }
});

/**
 * Check authentication status
 * Useful for route guards and auto-login
 */
ipcMain.handle('check-auth', async (event) => {
  try {
    const isAuth = await TokenManager.isAuthenticated();
    const user = isAuth ? await TokenManager.getUser() : null;

    return {
      isAuthenticated: isAuth,
      user: user
    };

  } catch (error) {
    console.error('❌ Auth check failed:', error);
    return {
      isAuthenticated: false,
      user: null
    };
  }
});

ipcMain.handle('get-auth-token', async () => {
  try {
    const token = await TokenManager.getToken();
    return token || null;
  } catch (e) {
    console.error('❌ get-auth-token failed:', e);
    return null;
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