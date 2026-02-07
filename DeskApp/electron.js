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

require('dotenv').config();

const GoogleAuth = require('./src/auth/GoogleAuth');
const TokenManager = require('./src/auth/TokenManager');
const CloudRunClient = require('./src/api/CloudRunClient');
const axios = require('axios');
const { app, BrowserWindow, ipcMain, globalShortcut, desktopCapturer, screen, Notification, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
// Import electron-store - it's an ES module, so we need to import it differently
let Store;
let authStore;
let store;
let notificationWindow = null;

const audioDir = path.join(__dirname, 'captures', 'audio');
if (!fs.existsSync(audioDir)) {
  fs.mkdirSync(audioDir, { recursive: true });
}

let audioPath = null;

ipcMain.on('notification-send-capture', async (event, payload) => {
  console.log('🔥 Capture received from notification');

  let audioPath = null;
  const transcript = payload.audioTranscript || null;

  try {
    // ✅ ENSURE CONTEXT HAS TIMEZONE
    if (!payload.context.timezone) {
      payload.context.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      console.log('🌍 Added timezone to context:', payload.context.timezone);
    }
    
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
    console.error('❌ Failed to send capture:', err.message || err);
    console.error('❌ Full error:', err);

    // notify floating button of failure
    if (floatingButton && !floatingButton.isDestroyed()) {
      floatingButton.webContents.send('capture-sent-failed', {
        error: err.message || 'Unknown error'
      });
    }
  }

  if (notificationWindow && !notificationWindow.isDestroyed()) {
    notificationWindow.close();
  }
  notificationWindow = null;
});



ipcMain.handle('show-capture-notification', async (event, data) => {
  console.log('🔔 Creating capture notification window...');

  // Close any existing notification safely
  if (notificationWindow && !notificationWindow.isDestroyed()) {
    notificationWindow.close();
  }
  notificationWindow = null;

  try {
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

    await notificationWindow.loadFile(notificationPath);
    
    // Send capture data to notification
    notificationWindow.webContents.send('capture-data', data);
    notificationWindow.show(); // doesn't steal focus
    console.log('✅ Notification window shown');

    notificationWindow.on('closed', () => {
      console.log('🔔 Notification window closed, resetting floating button state');
      // Reset floating button state when notification closes
      if (floatingButton && !floatingButton.isDestroyed()) {
        floatingButton.webContents.send('capture-notification-closed');
      }
      notificationWindow = null;
    });

    return { success: true, message: 'Notification window created' };

  } catch (err) {
    console.error('❌ Failed to show notification:', err);
    if (notificationWindow && !notificationWindow.isDestroyed()) {
      notificationWindow.close();
      notificationWindow = null;
    }
    throw err;
  }
});



ipcMain.handle('api-get-inbox', async (event, params) => {
  try {
    console.log('📥 [IPC] Getting inbox with params:', params);
    const result = await CloudRunClient.getInbox(params);
    console.log('✅ [IPC] Inbox retrieved:', result.total, 'items');
    return result;
  } catch (error) {
    console.error('❌ [IPC] Failed to get inbox:', error);
    console.error('❌ [IPC] Error details:', error.response?.data || error.message);
    return { success: false, items: [], total: 0, error: error.message };
  }
});

ipcMain.handle('api-get-capture', async (event, captureId) => {
  try {
    console.log('📄 [IPC] Getting capture:', captureId);
    const result = await CloudRunClient.getCaptureById(captureId);
    return result;
  } catch (error) {
    console.error('❌ [IPC] Failed to get capture:', error);
    return { success: false, error: error.message };
  }
});



ipcMain.handle('api-ask-capture', async (event, captureId, question) => {
  try {
    console.log('💬 [IPC] Asking about capture:', captureId, 'Question:', question);
    
    const token = await TokenManager.getToken();
    if (!token) {
      return { success: false, error: 'Not authenticated' };
    }
    
    const params = new URLSearchParams();
    params.append('question', question);
    
    const response = await axios.post(
      `${BACKEND_URL}/api/inbox/${captureId}/ask`,
      params,
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    console.log('✅ [IPC] Answer received:', response.data.answer);
    return response.data;
    
  } catch (error) {
    console.error('❌ [IPC] Failed to ask about capture:', error.message);
    console.error('❌ [IPC] Error details:', error.response?.data || error.response || error);
    return { success: false, error: error.response?.data?.detail || error.message };
  }
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

async function initializeStores() {
  Store = (await import('electron-store')).default;
  
  authStore = new Store({ name: 'auth' });
  
  store = new Store({
    defaults: {
      buttonPosition: { x: 100, y: 100 },
      buttonVisible: true,
      captureShortcut: 'CommandOrControl+Shift+L'
    }
  });
  
  console.log('✅ Stores initialized');
}

let mainWindow = null;
let floatingButton = null;

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
console.log('🌐 [ELECTRON] Backend URL:', BACKEND_URL);

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

  const isAuthenticated = await TokenManager.isAuthenticated();

  const startUrl = isAuthenticated
    ? 'http://localhost:3000/inbox'
    : 'http://localhost:3000/login';

  await mainWindow.loadURL(startUrl);

  // ⭐ ADD THIS: Inject token into web page after load
  if (isAuthenticated) {
    const token = await TokenManager.getToken();
    if (token) {
      mainWindow.webContents.executeJavaScript(`
        localStorage.setItem('token', '${token}');
        console.log('Token injected into localStorage');
      `);
    }
  }

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Create floating capture button
// function createFloatingButton() {
//   // Get saved position or use default
//   const savedPosition = store.get('buttonPosition');

//   // Get primary display dimensions
//   const primaryDisplay = screen.getPrimaryDisplay();
//   const { width, height } = primaryDisplay.workAreaSize;

//   // Ensure position is within screen bounds
//   const x = Math.min(savedPosition.x, width - 90);
//   const y = Math.min(savedPosition.y, height - 90);

//   floatingButton = new BrowserWindow({
//     width: 280,  // ← Reduced from 600 to fit just the menu
//     height: 280,
//     x: x,
//     y: y,
//     frame: false,
//     transparent: true,
//     alwaysOnTop: true,
//     resizable: false,
//     movable: true,
//     skipTaskbar: true,
//     focusable: false,
//     webPreferences: {
//       preload: path.join(__dirname, 'preload.js'),
//       contextIsolation: true,
//       nodeIntegration: false
//     }
//   });

//   // Load the floating button HTML
//   floatingButton.loadFile(path.join(__dirname, 'src', 'components', 'floating-button.html'));

//   floatingButton.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
//     console.error('❌ Floating button failed to load:', errorCode, errorDescription);
//   });

//   floatingButton.webContents.on('did-finish-load', () => {
//     floatingButton.show();
//     console.log('✅ Floating button loaded successfully');
//   });
//   // Keep window on top with highest priority
//   floatingButton.setAlwaysOnTop(true, 'screen-saver');
//   floatingButton.setVisibleOnAllWorkspaces(true);

//   // Set click-through for the window (allow clicking through transparent areas)
//   floatingButton.setIgnoreMouseEvents(false);

//   // Save position when window is moved
//   floatingButton.on('moved', () => {
//     const position = floatingButton.getPosition();
//     store.set('buttonPosition', { x: position[0], y: position[1] });
//   });

//   floatingButton.on('closed', () => {
//     floatingButton = null;
//   });

//   // Open DevTools in development (for debugging)
//   if (process.env.NODE_ENV === 'development') {
//     floatingButton.webContents.openDevTools({ mode: 'detach' });
//   }
// }

// Debug code to add to electron.js in createFloatingButton() function

function createFloatingButton() {
  console.log('🔍 [DEBUG] createFloatingButton called');
  
  // Get saved position or use default
  const savedPosition = store.get('buttonPosition');
  console.log('🔍 [DEBUG] Saved position:', savedPosition);

  // Get primary display dimensions
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;
  console.log('🔍 [DEBUG] Screen size:', { width, height });

  // Ensure position is within screen bounds
  const x = Math.min(savedPosition.x, width - 90);
  const y = Math.min(savedPosition.y, height - 90);
  console.log('🔍 [DEBUG] Button position:', { x, y });

  floatingButton = new BrowserWindow({
    width: 280,
    height: 280,
    x: x,
    y: y,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    movable: true,
    skipTaskbar: true,
    focusable: false,
    show: true,  // ⭐ Try with this first
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  console.log('🔍 [DEBUG] BrowserWindow created');
  console.log('🔍 [DEBUG] floatingButton exists?', !!floatingButton);
  console.log('🔍 [DEBUG] floatingButton.isVisible()?', floatingButton.isVisible());
  console.log('🔍 [DEBUG] floatingButton.isDestroyed()?', floatingButton.isDestroyed());

  // Load the floating button HTML
  const buttonPath = path.join(__dirname, 'src', 'components', 'floating-button.html');
  console.log('🔍 [DEBUG] Loading from path:', buttonPath);
  console.log('🔍 [DEBUG] File exists?', fs.existsSync(buttonPath));

  floatingButton.loadFile(buttonPath);

  floatingButton.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('❌ [DEBUG] Floating button failed to load:', errorCode, errorDescription);
  });

  floatingButton.webContents.on('did-finish-load', () => {
    console.log('✅ [DEBUG] Floating button loaded successfully');
    console.log('🔍 [DEBUG] After load - isVisible?', floatingButton.isVisible());
    console.log('🔍 [DEBUG] After load - getBounds:', floatingButton.getBounds());
    
    // Force show
    floatingButton.show();
    floatingButton.focus(); // Try to focus it
    
    console.log('🔍 [DEBUG] After show() - isVisible?', floatingButton.isVisible());
    console.log('🔍 [DEBUG] After show() - isFocused?', floatingButton.isFocused());
  });

  // Keep window on top with highest priority
  floatingButton.setAlwaysOnTop(true, 'screen-saver');
  floatingButton.setVisibleOnAllWorkspaces(true);
  console.log('🔍 [DEBUG] Set always on top and visible on all workspaces');

  // Set click-through for the window (allow clicking through transparent areas)
  floatingButton.setIgnoreMouseEvents(false);

  // Save position when window is moved
  floatingButton.on('moved', () => {
    const position = floatingButton.getPosition();
    console.log('🔍 [DEBUG] Button moved to:', position);
    store.set('buttonPosition', { x: position[0], y: position[1] });
  });

  floatingButton.on('closed', () => {
    console.log('🔍 [DEBUG] Floating button closed');
    floatingButton = null;
  });

  // Open DevTools in development (for debugging)
  if (process.env.NODE_ENV === 'development') {
    console.log('🔍 [DEBUG] Opening DevTools for floating button');
    floatingButton.webContents.openDevTools({ mode: 'detach' });
  }
  
  console.log('🔍 [DEBUG] createFloatingButton completed');
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
  // Get user's timezone from system
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  
  const context = {
    appName: 'Unknown',
    windowTitle: 'Unknown',
    url: null,
    timestamp: new Date().toISOString(),
    timezone: timezone  // ← ADD THIS LINE
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
async function sendToBackend(screenshotPath, context, audioPath, textNote, transcript = null) {
  try {
    console.log('📤 [ELECTRON] Sending to backend:', BACKEND_URL);

    const FormData = require('form-data');
    const axios = require('axios');
    const token = await TokenManager.getToken();

    const userTimezone = context.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;

    const form = new FormData();
    
    // Upload screenshot FILE (not path)
    const screenshotBuffer = fs.readFileSync(screenshotPath);
    form.append('screenshot_file', screenshotBuffer, {
      filename: path.basename(screenshotPath),
      contentType: 'image/png'
    });
    
    // Upload audio FILE if exists
    if (audioPath && fs.existsSync(audioPath)) {
      const audioBuffer = fs.readFileSync(audioPath);
      form.append('audio_file', audioBuffer, {
        filename: path.basename(audioPath),
        contentType: 'audio/webm'
      });
    }
    
    // Add metadata as form fields
    form.append('app_name', context.appName || 'Unknown');
    form.append('window_title', context.windowTitle || 'Unknown');
    form.append('url', context.url || '');
    form.append('timestamp', context.timestamp);
    form.append('timezone', userTimezone);
    
    if (textNote) form.append('text_note', textNote);
    if (transcript) form.append('audio_transcript', transcript);

    const response = await axios.post(`${BACKEND_URL}/api/capture`, form, {
      headers: {
        ...form.getHeaders(),
        'Authorization': `Bearer ${token}`
      }
    });

    return response.data;
  } catch (error) {
    console.error('❌ Backend upload failed:', error.message);
    throw error;
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
// ipcMain.handle('google-login', async (event) => {
//   try {
//     console.log('🔐 Starting Google OAuth flow...');

//     // Step 1: Open browser and get authorization code
//     const authCode = await GoogleAuth.startOAuthFlow();
//     console.log('✅ Got authorization code');

//     // Step 2: Send code to backend, get JWT token
//     const { token, user } = await CloudRunClient.login(authCode);
//     console.log('✅ Login successful:', user.email);

//     return {
//       success: true,
//       user: user
//     };

//   } catch (error) {
//     console.error('❌ Login failed:', error);
//     return {
//       success: false,
//       error: error.message
//     };
//   }
// });



ipcMain.handle('google-login', async (event) => {
  try {
    const authCode = await GoogleAuth.startOAuthFlow();
    const { token, user } = await CloudRunClient.login(authCode);

    console.log('✅ Login successful, injecting token...');

    // Inject token into renderer localStorage
    if (mainWindow && !mainWindow.isDestroyed()) {
      await mainWindow.webContents.executeJavaScript(`
        localStorage.setItem('token', '${token}');
        console.log('✅ Token saved to localStorage');
      `);
      
      // Redirect to inbox
      await mainWindow.loadURL('http://localhost:3000/inbox');
      console.log('✅ Redirected to inbox');
    }

    // Create floating button
    if (!floatingButton || floatingButton.isDestroyed()) {
      createFloatingButton();
    }

    return { success: true, user: user };
  } catch (error) {
    console.error('❌ Login failed:', error);
    return { success: false, error: error.message };
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
// ipcMain.handle('logout', async (event) => {
//   try {
//     await TokenManager.clearToken();

//     // ADD THIS: Destroy the floating button on logout
//     if (floatingButton && !floatingButton.isDestroyed()) {
//       floatingButton.close();
//       floatingButton = null;
//     }

//     return { success: true };
//   } catch (error) {
//     return { success: false, error: error.message };
//   }
// });

ipcMain.handle('logout', async (event) => {
  try {
    await TokenManager.clearToken();

    // ADD THIS: Close the button on logout
    if (floatingButton && !floatingButton.isDestroyed()) {
      floatingButton.close();
      floatingButton = null;
    }

    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

/**
 * Check authentication status
 * Useful for route guards and auto-login
 */
// ipcMain.handle('check-auth', async (event) => {
//   try {
//     const isAuth = await TokenManager.isAuthenticated();
//     const user = isAuth ? await TokenManager.getUser() : null;

//     return {
//       isAuthenticated: isAuth,
//       user: user
//     };

//   } catch (error) {
//     console.error('❌ Auth check failed:', error);
//     return {
//       isAuthenticated: false,
//       user: null
//     };
//   }
// });

ipcMain.handle('check-auth', async (event) => {
  try {
    const isAuth = await TokenManager.isAuthenticated();
    const user = isAuth ? await TokenManager.getUser() : null;

    // ADD THIS: If user is already authenticated (auto-login), show button
    if (isAuth && (!floatingButton || floatingButton.isDestroyed())) {
      createFloatingButton();
    }

    return { isAuthenticated: isAuth, user: user };
  } catch (error) {
    return { isAuthenticated: false, user: null };
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

// File Dialog Handler - Optimized for Speed - PDF and DOCX Only
ipcMain.handle('open-file-dialog', async () => {
  try {
    const result = await dialog.showOpenDialog({
      title: 'Select a file to attach (PDF or DOCX only)',
      defaultPath: app.getPath('documents') || app.getPath('home'),
      buttonLabel: 'Select',
      properties: ['openFile'],
      filters: [
        { name: 'PDF & Word Documents (*.pdf, *.docx)', extensions: ['pdf', 'docx'] }
      ]
    });

    if (result.canceled) {
      return { success: false, filePath: null, message: 'File selection canceled' };
    }

    const filePath = result.filePaths[0];
    const fileName = path.basename(filePath);
    const fileExtension = path.extname(filePath).toLowerCase();

    // Validate file type
    if (!['.pdf', '.docx'].includes(fileExtension)) {
      console.warn('⚠️ Invalid file type:', fileExtension);
      return {
        success: false,
        filePath: null,
        error: `Invalid file type: ${fileExtension}. Only .pdf and .docx files are allowed.`
      };
    }

    const fileSize = fs.statSync(filePath).size;

    // Check file size (limit to 50MB)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (fileSize > maxSize) {
      console.warn('⚠️ File too large:', (fileSize / 1024 / 1024).toFixed(2), 'MB');
      return {
        success: false,
        filePath: null,
        error: `File too large. Maximum size is 50MB. Your file is ${(fileSize / 1024 / 1024).toFixed(2)}MB.`
      };
    }

    console.log('✅ File selected:', fileName, `(${(fileSize / 1024 / 1024).toFixed(2)} MB)`);

    return {
      success: true,
      filePath: filePath,
      fileName: fileName,
      fileSize: fileSize,
      fileType: fileExtension.substring(1).toUpperCase(),
      message: 'File selected successfully'
    };
  } catch (error) {
    console.error('❌ File dialog error:', error);
    return {
      success: false,
      filePath: null,
      error: error.message
    };
  }
});


// App lifecycle - INITIALIZE STORE FIRST
// IPC: Read file as buffer for renderer upload
ipcMain.handle('read-file-buffer', async (event, filePath) => {
  try {
    const data = fs.readFileSync(filePath);
    return data.buffer;
  } catch (err) {
    console.error('❌ Failed to read file buffer:', err);
    return null;
  }
});

// IPC: Get JWT token for renderer

// TEXT NOTE HANDLER
let textNoteWindow = null;

ipcMain.handle('open-text-note-window', async () => {
  try {
    if (textNoteWindow && !textNoteWindow.isDestroyed()) {
      textNoteWindow.focus();
      return { success: true };
    }

    const context = await getActiveWindowContext();

    textNoteWindow = new BrowserWindow({
      width: 450,
      height: 380,
      frame: false,
      transparent: true,
      alwaysOnTop: true,
      resizable: false,
      skipTaskbar: true,
      webPreferences: {
        preload: path.join(__dirname, 'preload.js'),
        contextIsolation: true,
        nodeIntegration: false
      }
    });

    const display = screen.getPrimaryDisplay();
    const { x, y, width, height } = display.workArea;
    textNoteWindow.setPosition(
      Math.floor(x + (width - 450) / 2),
      Math.floor(y + (height - 380) / 2)
    );

    await textNoteWindow.loadFile(path.join(__dirname, 'src', 'components', 'TextNoteWindow.html'));
    
    textNoteWindow.webContents.send('text-note-data', { context });

    textNoteWindow.on('closed', () => {
      textNoteWindow = null;
    });

    return { success: true };
  } catch (error) {
    console.error('Failed to open text note window:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('send-text-note', async (event, data) => {
  try {
    const FormData = require('form-data');
    const axios = require('axios');
    const token = await TokenManager.getToken();

    const userTimezone = data.context?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;

    const form = new FormData();
    
    // No screenshot or audio for text-only note
    form.append('app_name', data.context?.appName || 'Unknown');
    form.append('window_title', data.context?.windowTitle || 'Unknown');
    form.append('url', data.context?.url || '');
    form.append('timestamp', new Date().toISOString());
    form.append('timezone', userTimezone);
    form.append('text_note', data.text);

    const response = await axios.post(`${BACKEND_URL}/api/capture`, form, {
      headers: {
        ...form.getHeaders(),
        'Authorization': `Bearer ${token}`
      }
    });

    console.log('Text note sent successfully:', response.data);
    
    if (floatingButton && !floatingButton.isDestroyed()) {
      floatingButton.webContents.send('capture-sent-success');
    }

    return { success: true, result: response.data };
  } catch (error) {
    console.error('Failed to send text note:', error);
    return { success: false, error: error.message };
  }
});

// AUDIO NOTE HANDLER
let audioNoteWindow = null;

ipcMain.handle('open-audio-note-window', async () => {
  try {
    if (audioNoteWindow && !audioNoteWindow.isDestroyed()) {
      audioNoteWindow.focus();
      return { success: true };
    }

    const context = await getActiveWindowContext();

    audioNoteWindow = new BrowserWindow({
      width: 450,
      height: 460,
      frame: false,
      transparent: true,
      alwaysOnTop: true,
      resizable: false,
      skipTaskbar: true,
      webPreferences: {
        preload: path.join(__dirname, 'preload.js'),
        contextIsolation: true,
        nodeIntegration: false
      }
    });

    const display = screen.getPrimaryDisplay();
    const { x, y, width, height } = display.workArea;
    audioNoteWindow.setPosition(
      Math.floor(x + (width - 450) / 2),
      Math.floor(y + (height - 460) / 2)
    );

    await audioNoteWindow.loadFile(path.join(__dirname, 'src', 'components', 'AudioRecordWindow.html'));
    
    audioNoteWindow.webContents.send('audio-note-data', { context });

    audioNoteWindow.on('closed', () => {
      audioNoteWindow = null;
    });

    return { success: true };
  } catch (error) {
    console.error('Failed to open audio note window:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('send-audio-note', async (event, data) => {
  try {
    const FormData = require('form-data');
    const axios = require('axios');
    const token = await TokenManager.getToken();

    const userTimezone = data.context?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;

    const form = new FormData();
    
    // Upload audio only
    const audioBuffer = Buffer.from(data.audioBuffer);
    form.append('audio_file', audioBuffer, {
      filename: `audio_${Date.now()}.webm`,
      contentType: 'audio/webm'
    });
    
    form.append('app_name', data.context?.appName || 'Unknown');
    form.append('window_title', data.context?.windowTitle || 'Unknown');
    form.append('url', data.context?.url || '');
    form.append('timestamp', new Date().toISOString());
    form.append('timezone', userTimezone);

    const response = await axios.post(`${BACKEND_URL}/api/capture`, form, {
      headers: {
        ...form.getHeaders(),
        'Authorization': `Bearer ${token}`
      }
    });

    console.log('Audio note sent successfully:', response.data);
    
    if (floatingButton && !floatingButton.isDestroyed()) {
      floatingButton.webContents.send('capture-sent-success');
    }

    return { success: true, result: response.data };
  } catch (error) {
    console.error('Failed to send audio note:', error);
    return { success: false, error: error.message };
  }
});

ipcMain.handle('api-get-collections', async (event) => {
  try {
    console.log('📁 [IPC] Getting collections');
    const result = await CloudRunClient.getCollections();
    console.log('✅ [IPC] Collections retrieved:', result.total);
    return result;
  } catch (error) {
    console.error('❌ [IPC] Failed to get collections:', error);
    return { success: false, collections: [], total: 0 };
  }
});

ipcMain.handle('api-get-theme-clusters', async (event, numClusters = 4) => {
  try {
    console.log('🎨 [IPC] Getting theme clusters');
    const result = await CloudRunClient.getThemeClusters(numClusters);
    console.log('✅ [IPC] Clusters retrieved:', result.total);
    return result;
  } catch (error) {
    console.error('❌ [IPC] Failed to get clusters:', error);
    return { success: false, clusters: [], total: 0 };
  }
});

ipcMain.handle('api-ask-question', async (event, question, filterDomain) => {
  try {
    console.log('🤔 [IPC] Asking question:', question);
    
    // Get token from TokenManager (which knows the correct key)
    const TokenManager = require('./src/auth/TokenManager');
    const token = await TokenManager.getToken();
    
    if (!token) {
      throw new Error('Not authenticated');
    }
    
    const result = await CloudRunClient.askQuestion(question, filterDomain, token);
    console.log('✅ [IPC] Got answer');
    return result;
  } catch (error) {
    console.error('❌ [IPC] Failed to ask question:', error);
    return { success: false, error: error.message };
  }
});

// Add IPC handler for getting proactive notifications
ipcMain.handle('api-get-proactive-notifications', async (event) => {
  try {
    console.log('🔔 [IPC] Getting proactive notifications');
    const result = await CloudRunClient.getProactiveNotifications();
    console.log('✅ [IPC] Got', result.count, 'notifications');
    return result;
  } catch (error) {
    console.error('❌ [IPC] Failed to get proactive notifications:', error);
    return { success: false, notifications: [], count: 0 };
  }
});

// Proactive notification system
let notificationInterval = null;

function startProactiveNotifications() {
  console.log('🔔 Starting proactive notification system...');
  
  // Check every 30 minutes (1800000 ms)
  // For testing, use 2 minutes: 2 * 60 * 1000
  const checkInterval = 2 * 60 * 1000;
  
  notificationInterval = setInterval(async () => {
    try {
      const isAuth = await TokenManager.isAuthenticated();
      if (!isAuth) {
        console.log('⚠️ Not authenticated, skipping proactive check');
        return;
      }
      
      console.log('🔔 Checking for proactive notifications...');
      const result = await CloudRunClient.getProactiveNotifications();
      
      if (result.notifications && result.notifications.length > 0) {
        console.log('✅ Found', result.notifications.length, 'proactive notifications');
        
        // Show the highest priority notification
        const topNotif = result.notifications[0];
        showProactiveNotification(topNotif);
      } else {
        console.log('ℹ️ No proactive notifications at this time');
      }
      
    } catch (error) {
      console.error('❌ Proactive notification check failed:', error);
    }
  }, checkInterval);
  
  // Also check immediately on startup (after 30 seconds)
  setTimeout(async () => {
    try {
      const isAuth = await TokenManager.isAuthenticated();
      if (!isAuth) return;
      
      const result = await CloudRunClient.getProactiveNotifications();
      if (result.notifications && result.notifications.length > 0) {
        showProactiveNotification(result.notifications[0]);
      }
    } catch (error) {
      console.error('❌ Initial proactive check failed:', error);
    }
  }, 30000);
}

function showProactiveNotification(notification) {
  console.log('🔔 Showing proactive notification:', notification.title);
  
  // Close existing notification if open
  if (notificationWindow && !notificationWindow.isDestroyed()) {
    notificationWindow.close();
  }
  notificationWindow = null;
  
  try {
    notificationWindow = new BrowserWindow({
      width: 420,
      height: 300,
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
      }
    });

    // Bottom-right positioning
    const display = screen.getPrimaryDisplay();
    const { x, y, width, height } = display.workArea;
    const margin = 16;
    notificationWindow.setPosition(
      x + width - 420 - margin,
      y + height - 300 - margin
    );

    // Load HTML
    const notificationPath = path.join(__dirname, 'src', 'components', 'ProactiveNotification.html');
    
    notificationWindow.loadFile(notificationPath);
    
    // Send notification data
    notificationWindow.webContents.on('did-finish-load', () => {
      notificationWindow.webContents.send('proactive-notification-data', notification);
      notificationWindow.show();
      console.log('✅ Proactive notification shown');
    });

    notificationWindow.on('closed', () => {
      console.log('🔔 Proactive notification closed');
      notificationWindow = null;
    });

    // Auto-close after 10 seconds
    setTimeout(() => {
      if (notificationWindow && !notificationWindow.isDestroyed()) {
        notificationWindow.close();
      }
    }, 10000);

  } catch (err) {
    console.error('❌ Failed to show proactive notification:', err);
    if (notificationWindow && !notificationWindow.isDestroyed()) {
      notificationWindow.close();
      notificationWindow = null;
    }
  }
}

// In app.whenReady()
app.whenReady().then(async () => {
  console.log('🚀 LifeOS starting...');

  await initializeStores();

  createMainWindow();

  const isAuthenticated = await TokenManager.isAuthenticated();
  if (isAuthenticated) {
    console.log('✅ User already authenticated, creating floating button...');
    store.set('buttonPosition', { x: 300, y: 300 });
    createFloatingButton();
    
    // START PROACTIVE NOTIFICATIONS
    startProactiveNotifications();
  }

  registerShortcuts();

  console.log('✅ LifeOS ready!');
});


// app.whenReady().then(async () => {
//   console.log('🚀 LifeOS starting...');

//   // Initialize stores FIRST
//   await initializeStores();

//   // Create main window
//   createMainWindow();

//   // Check if user is already authenticated (auto-login)
//   const isAuthenticated = await TokenManager.isAuthenticated();
//   if (isAuthenticated) {
//     console.log('✅ User already authenticated, creating floating button...');
//     store.set('buttonPosition', { x: 300, y: 300 });
//     createFloatingButton();
//   }

//   // Register keyboard shortcuts
//   registerShortcuts();

//   console.log('✅ LifeOS ready!');
// });

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