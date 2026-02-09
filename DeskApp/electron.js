/**
 * electron.js — MINIMAL PRODUCTION FIX
 *
 * ONLY 2 CHANGES from your original:
 *   1. Directory creation uses app.getPath('userData') in production  (fixes ENOTDIR)
 *   2. In production, starts a local Next.js server from bundled .next/  (fixes blank screen)
 *
 * Everything else is YOUR ORIGINAL CODE, untouched.
 */

require('dotenv').config();

const GoogleAuth = require('./src/auth/GoogleAuth');
const TokenManager = require('./src/auth/TokenManager');
const CloudRunClient = require('./src/api/CloudRunClient');
const axios = require('axios');
const { app, BrowserWindow, ipcMain, globalShortcut, desktopCapturer, screen, Notification, dialog } = require('electron');
const path = require('path');
const fs = require('fs');

let Store;
let authStore;
let store;
let notificationWindow = null;

// ============================================================
// FIX #1: DEFER directory creation — declare vars, create later
// ============================================================
let capturesDir;
let audioDir;
let audioPath = null;

// We'll call this AFTER app.whenReady()
function initializeDirectories() {
  const isDev = !app.isPackaged;
  const baseDir = isDev ? __dirname : app.getPath('userData');

  capturesDir = path.join(baseDir, 'captures', 'screenshots');
  audioDir    = path.join(baseDir, 'captures', 'audio');

  if (!fs.existsSync(capturesDir)) {
    fs.mkdirSync(capturesDir, { recursive: true });
    console.log('✅ Created capturesDir:', capturesDir);
  }
  if (!fs.existsSync(audioDir)) {
    fs.mkdirSync(audioDir, { recursive: true });
    console.log('✅ Created audioDir:', audioDir);
  }
}

// ============================================================
// FIX #2: FRONTEND_URL — in production, start local Next server
// ============================================================
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

let FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000';
const PRODUCTION_PORT = 3847; // random high port to avoid conflicts

async function startProductionFrontend() {
  // Only needed when packaged
  if (isDev) return;

  try {
    console.log('🚀 Starting production Next.js server...');
    const next = require('next');
    const http = require('http');
    const { parse } = require('url');

    const nextApp = next({
      dev: false,
      dir: __dirname,
      conf: { distDir: '.next' }
    });

    const handle = nextApp.getRequestHandler();
    await nextApp.prepare();

    const server = http.createServer((req, res) => {
      handle(req, res, parse(req.url, true));
    });

    await new Promise((resolve, reject) => {
      server.listen(PRODUCTION_PORT, '127.0.0.1', () => {
        FRONTEND_URL = `http://127.0.0.1:${PRODUCTION_PORT}`;
        console.log('✅ Frontend serving at:', FRONTEND_URL);
        resolve();
      });
      server.on('error', reject);
    });
  } catch (err) {
    console.error('❌ Could not start Next.js server:', err.message);
    // Fallback: try the dev URL anyway (won't work, but won't crash)
    FRONTEND_URL = 'http://localhost:3000';
  }
}

// ==========================
// EVERYTHING BELOW IS YOUR ORIGINAL CODE
// (only capturesDir/audioDir references are now variables set above)
// ==========================

ipcMain.on('notification-send-capture', async (event, payload) => {
  console.log('📥 Capture received from notification');

  let audioPathLocal = null;
  const transcript = payload.audioTranscript || null;

  try {
    if (!payload.context.timezone) {
      payload.context.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    }

    if (payload.audioBuffer) {
      const audioFilename = `audio_${Date.now()}.webm`;
      audioPathLocal = path.join(audioDir, audioFilename);
      fs.writeFileSync(audioPathLocal, Buffer.from(payload.audioBuffer));
      console.log('🎧 Audio saved:', audioPathLocal);
    }

    const result = await sendToBackend(
      payload.screenshotPath,
      payload.context,
      audioPathLocal,
      payload.textNote || null,
      transcript
    );

    console.log('✅ Backend response:', result);

    if (floatingButton && !floatingButton.isDestroyed()) {
      floatingButton.webContents.send('capture-sent-success');
    }

  } catch (err) {
    console.error('❌ Failed to send capture:', err.message || err);

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

  if (notificationWindow && !notificationWindow.isDestroyed()) {
    notificationWindow.close();
  }
  notificationWindow = null;

  try {
    const notifWidth = 520;
    const notifHeight = 420;
    const margin = 10;

    notificationWindow = new BrowserWindow({
      icon: resolvePublicAsset(LOGO_PUBLIC_PATH),
      width: notifWidth,
      height: notifHeight,
      frame: false,
      transparent: true,
      alwaysOnTop: true,
      resizable: false,
      skipTaskbar: true,
      show: false,
      autoHideMenuBar: true,
      webPreferences: {
        preload: path.join(__dirname, 'preload.js'),
        contextIsolation: true,
        nodeIntegration: false,
        devTools: true
      }
    });

    notificationWindow.setAlwaysOnTop(true, 'screen-saver');
    notificationWindow.setVisibleOnAllWorkspaces(true);

    const display = screen.getPrimaryDisplay();
    const { x, y, width, height } = display.workArea;

    let posX = x + width - notifWidth - margin;
    let posY = y + height - notifHeight - margin;
    if (posX < x + margin) posX = x + margin;
    if (posY < y + margin) posY = y + margin;
    notificationWindow.setPosition(posX, posY);

    const notificationPath = path.join(__dirname, 'src', 'components', 'CaptureNotification.html');
    console.log('📄 Loading notification from:', notificationPath);

    notificationWindow.webContents.on('did-fail-load', (e, code, desc) => {
      console.error('❌ Notification did-fail-load:', code, desc);
    });

    notificationWindow.webContents.on('console-message', (e, level, message) => {
      console.log('🧩 Notification console:', message);
    });

    await notificationWindow.loadFile(notificationPath);

    notificationWindow.webContents.send('capture-data', data);
    notificationWindow.show();
    console.log('✅ Notification window shown');

    notificationWindow.on('closed', () => {
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

ipcMain.handle('api-get-capture-v2', async (event, captureId) => {
  try {
    console.log('📄 [IPC V2] Getting enhanced capture:', captureId);
    const result = await CloudRunClient.getCaptureByIdV2(captureId);
    return result;
  } catch (error) {
    console.error('❌ [IPC V2] Failed to get capture:', error);
    console.log('📄 [IPC V2] Falling back to v1');
    return CloudRunClient.getCaptureById(captureId);
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
    return { success: false, error: error.response?.data?.detail || error.message };
  }
});


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

const LOGO_PUBLIC_PATH =
  process.env.APP_LOGO_PUBLIC_PATH || "/logo.png";

function resolvePublicAsset(publicPath) {
  const cleanPath = publicPath.startsWith("/")
    ? publicPath.slice(1)
    : publicPath;

  if (app.isPackaged) {
    return path.join(process.resourcesPath, "public", cleanPath);
  }

  return path.join(__dirname, "public", cleanPath);
}


let mainWindow = null;
let floatingButton = null;

const BACKEND_URL = process.env.BACKEND_URL || 'https://lifeos-backend-1056690364460.us-central1.run.app';

console.log('🌐 [ELECTRON] Backend URL:', BACKEND_URL);
console.log('🌐 [ELECTRON] isDev:', isDev);

// --- NO directory creation at top level any more (moved to initializeDirectories) ---


// Create main dashboard window
async function createMainWindow() {
  mainWindow = new BrowserWindow({
    icon: resolvePublicAsset(LOGO_PUBLIC_PATH),
    width: 1200,
    height: 800,
    autoHideMenuBar: true,

    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  const isAuthenticated = await TokenManager.isAuthenticated();

  const startUrl = isAuthenticated
    ? `${FRONTEND_URL}/inbox`
    : `${FRONTEND_URL}/login`;

  console.log('🌐 Loading:', startUrl);
  await mainWindow.loadURL(startUrl);

  if (isAuthenticated) {
    const token = await TokenManager.getToken();
    if (token) {
      mainWindow.webContents.executeJavaScript(`
        localStorage.setItem('token', '${token}');
        console.log('Token injected into localStorage');
      `);
    }
  }

  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}


function createFloatingButton() {
  console.log('🔍 [DEBUG] createFloatingButton called');

  const savedPosition = store.get('buttonPosition');

  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;

  const x = Math.min(savedPosition.x, width - 90);
  const y = Math.min(savedPosition.y, height - 90);

  floatingButton = new BrowserWindow({
    icon: resolvePublicAsset(LOGO_PUBLIC_PATH),
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
    show: true,
    autoHideMenuBar: true,

    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  const buttonPath = path.join(__dirname, 'src', 'components', 'floating-button.html');
  console.log('🔍 [DEBUG] Loading from path:', buttonPath);
  console.log('🔍 [DEBUG] File exists?', fs.existsSync(buttonPath));

  floatingButton.loadFile(buttonPath);

  floatingButton.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('❌ [DEBUG] Floating button failed to load:', errorCode, errorDescription);
  });

  floatingButton.webContents.on('did-finish-load', () => {
    console.log('✅ [DEBUG] Floating button loaded successfully');
    floatingButton.show();
  });

  floatingButton.setAlwaysOnTop(true, 'screen-saver');
  floatingButton.setVisibleOnAllWorkspaces(true);
  floatingButton.setIgnoreMouseEvents(false);

  floatingButton.on('moved', () => {
    const position = floatingButton.getPosition();
    store.set('buttonPosition', { x: position[0], y: position[1] });
  });

  floatingButton.on('closed', () => {
    floatingButton = null;
  });

  if (isDev) {
    floatingButton.webContents.openDevTools({ mode: 'detach' });
  }
}


function registerShortcuts() {
  const shortcut = store.get('captureShortcut');

  const registered = globalShortcut.register(shortcut, () => {
    console.log('Keyboard shortcut triggered:', shortcut);

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


async function getActiveWindowContext() {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  const context = {
    appName: 'Unknown',
    windowTitle: 'Unknown',
    url: null,
    timestamp: new Date().toISOString(),
    timezone: timezone
  };

  if (process.platform !== 'win32') {
    return context;
  }

  try {
    const { exec } = require('child_process');
    const { promisify } = require('util');
    const execAsync = promisify(exec);

    const scriptPath = path.join(__dirname, 'get-window-context.ps1');

    const { stdout } = await execAsync(
      `powershell -ExecutionPolicy Bypass -File "${scriptPath}"`,
      { timeout: 5000 }
    );

    const result = JSON.parse(stdout.trim());
    context.appName = result.processName || 'Unknown';
    context.windowTitle = result.windowTitle || 'Unknown';

    const browsers = ['chrome', 'msedge', 'brave', 'firefox', 'opera'];
    const isBrowser = browsers.some(b =>
      context.appName?.toLowerCase().includes(b)
    );

    if (isBrowser) {
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


async function sendToBackend(screenshotPath, context, audioFilePath, textNote, transcript = null) {
  try {
    console.log('📤 [ELECTRON] Sending to backend:', BACKEND_URL);

    const FormData = require('form-data');
    const token = await TokenManager.getToken();

    const userTimezone = context.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;

    const form = new FormData();

    const screenshotBuffer = fs.readFileSync(screenshotPath);
    form.append('screenshot_file', screenshotBuffer, {
      filename: path.basename(screenshotPath),
      contentType: 'image/png'
    });

    if (audioFilePath && fs.existsSync(audioFilePath)) {
      const audioBuffer = fs.readFileSync(audioFilePath);
      form.append('audio_file', audioBuffer, {
        filename: path.basename(audioFilePath),
        contentType: 'audio/webm'
      });
    }

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


ipcMain.handle('capture-screenshot', async (event) => {
  console.log('📸 Capture screenshot requested');

  try {
    const context = await getActiveWindowContext();
    console.log('📋 Window context:', context);

    await new Promise(resolve => setTimeout(resolve, 100));

    const sources = await desktopCapturer.getSources({
      types: ['screen'],
      thumbnailSize: { width: 1920, height: 1080 }
    });

    if (sources.length === 0) {
      throw new Error('No screen sources available');
    }

    const primarySource = sources[0];
    const screenshot = primarySource.thumbnail;

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `capture_${timestamp}.png`;
    const screenshotPath = path.join(capturesDir, filename);

    fs.writeFileSync(screenshotPath, screenshot.toPNG());
    console.log('✅ Screenshot saved:', screenshotPath);

    showNotification('Screenshot Captured! 📸', context.windowTitle || 'Processing...');

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


function showNotification(title, body) {
  if (Notification.isSupported()) {
    new Notification({
      title: title,
      body: body,
      icon: resolvePublicAsset(LOGO_PUBLIC_PATH)
    }).show();
  }
}


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


ipcMain.handle('google-login', async (event) => {
  try {
    const authCode = await GoogleAuth.startOAuthFlow();
    const { token, user } = await CloudRunClient.login(authCode);

    console.log('✅ Login successful, injecting token...');

    if (mainWindow && !mainWindow.isDestroyed()) {
      await mainWindow.webContents.executeJavaScript(`
        localStorage.setItem('token', '${token}');
        console.log('✅ Token saved to localStorage');
      `);

      await mainWindow.loadURL(`${FRONTEND_URL}/inbox`);
      console.log('✅ Redirected to inbox');
    }

    if (!floatingButton || floatingButton.isDestroyed()) {
      createFloatingButton();
    }

    return { success: true, user: user };
  } catch (error) {
    console.error('❌ Login failed:', error);
    return { success: false, error: error.message };
  }
});


ipcMain.handle('get-current-user', async (event) => {
  try {
    const isAuth = await TokenManager.isAuthenticated();

    if (!isAuth) {
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


ipcMain.handle('logout', async (event) => {
  try {
    await TokenManager.clearToken();

    if (floatingButton && !floatingButton.isDestroyed()) {
      floatingButton.close();
      floatingButton = null;
    }

    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});


ipcMain.handle('check-auth', async (event) => {
  try {
    const isAuth = await TokenManager.isAuthenticated();
    const user = isAuth ? await TokenManager.getUser() : null;

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

    if (!['.pdf', '.docx'].includes(fileExtension)) {
      return {
        success: false,
        filePath: null,
        error: `Invalid file type: ${fileExtension}. Only .pdf and .docx files are allowed.`
      };
    }

    const fileSize = fs.statSync(filePath).size;

    const maxSize = 50 * 1024 * 1024;
    if (fileSize > maxSize) {
      return {
        success: false,
        filePath: null,
        error: `File too large. Maximum size is 50MB.`
      };
    }

    return {
      success: true,
      filePath: filePath,
      fileName: fileName,
      fileSize: fileSize,
      fileType: fileExtension.substring(1).toUpperCase(),
      message: 'File selected successfully'
    };
  } catch (error) {
    return { success: false, filePath: null, error: error.message };
  }
});


ipcMain.handle('read-file-buffer', async (event, filePath) => {
  try {
    const data = fs.readFileSync(filePath);
    return data.buffer;
  } catch (err) {
    console.error('❌ Failed to read file buffer:', err);
    return null;
  }
});


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
      icon: resolvePublicAsset(LOGO_PUBLIC_PATH),
      width: 450,
      height: 380,
      frame: false,
      transparent: true,
      alwaysOnTop: true,
      resizable: false,
      skipTaskbar: true,
      autoHideMenuBar: true,

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
    return { success: false, error: error.message };
  }
});

ipcMain.handle('send-text-note', async (event, data) => {
  try {
    const FormData = require('form-data');
    const token = await TokenManager.getToken();

    const userTimezone = data.context?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;

    const form = new FormData();
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

    if (floatingButton && !floatingButton.isDestroyed()) {
      floatingButton.webContents.send('capture-sent-success');
    }

    return { success: true, result: response.data };
  } catch (error) {
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
      icon: resolvePublicAsset(LOGO_PUBLIC_PATH),
      width: 450,
      height: 460,
      frame: false,
      transparent: true,
      alwaysOnTop: true,
      resizable: false,
      skipTaskbar: true,
      autoHideMenuBar: true,

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
    return { success: false, error: error.message };
  }
});

ipcMain.handle('send-audio-note', async (event, data) => {
  try {
    const FormData = require('form-data');
    const token = await TokenManager.getToken();

    const userTimezone = data.context?.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone;

    const form = new FormData();

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

    if (floatingButton && !floatingButton.isDestroyed()) {
      floatingButton.webContents.send('capture-sent-success');
    }

    return { success: true, result: response.data };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('api-get-collections', async (event) => {
  try {
    return await CloudRunClient.getCollections();
  } catch (error) {
    return { success: false, collections: [], total: 0 };
  }
});

ipcMain.handle('api-get-theme-clusters', async (event, numClusters = 4) => {
  try {
    return await CloudRunClient.getThemeClusters(numClusters);
  } catch (error) {
    return { success: false, clusters: [], total: 0 };
  }
});

ipcMain.handle('api-ask-question', async (event, question, filterDomain) => {
  try {
    const TokenManager = require('./src/auth/TokenManager');
    const token = await TokenManager.getToken();

    if (!token) {
      throw new Error('Not authenticated');
    }

    const result = await CloudRunClient.askQuestion(question, filterDomain, token);
    return result;
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('api-get-proactive-notifications', async (event) => {
  try {
    return await CloudRunClient.getProactiveNotifications();
  } catch (error) {
    return { success: false, notifications: [], count: 0 };
  }
});

ipcMain.handle('api-get-capture-by-id', async (event, captureId) => {
  try {
    return await CloudRunClient.getCaptureById(captureId);
  } catch (error) {
    return { success: false, error: error.message };
  }
});


// Proactive notification system
let notificationInterval = null;

function startProactiveNotifications() {
  console.log('🔔 Starting proactive notification system...');

  const checkInterval = 10 * 60 * 1000;

  notificationInterval = setInterval(async () => {
    try {
      const isAuth = await TokenManager.isAuthenticated();
      if (!isAuth) return;

      const result = await CloudRunClient.getProactiveNotifications();

      if (result.notifications && result.notifications.length > 0) {
        showProactiveNotification(result.notifications[0]);
      }
    } catch (error) {
      console.error('❌ Proactive notification check failed:', error);
    }
  }, checkInterval);

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
  }, 300000);
}

function showProactiveNotification(notification) {
  console.log('🔔 Showing proactive notification:', notification.title);

  if (notificationWindow && !notificationWindow.isDestroyed()) {
    notificationWindow.close();
  }
  notificationWindow = null;

  try {
    notificationWindow = new BrowserWindow({
      icon: resolvePublicAsset(LOGO_PUBLIC_PATH),
      width: 420,
      height: 300,
      frame: false,
      transparent: true,
      alwaysOnTop: true,
      resizable: false,
      skipTaskbar: true,
      show: false,
      autoHideMenuBar: true,

      webPreferences: {
        preload: path.join(__dirname, 'preload.js'),
        contextIsolation: true,
        nodeIntegration: false,
        devTools: true
      }
    });

    const display = screen.getPrimaryDisplay();
    const { x, y, width, height } = display.workArea;
    const margin = 16;
    notificationWindow.setPosition(
      x + width - 420 - margin,
      y + height - 300 - margin
    );

    const notificationPath = path.join(__dirname, 'src', 'components', 'ProactiveNotification.html');

    notificationWindow.loadFile(notificationPath);

    notificationWindow.webContents.on('did-finish-load', () => {
      notificationWindow.webContents.send('proactive-notification-data', notification);
      notificationWindow.show();
    });

    notificationWindow.on('closed', () => {
      notificationWindow = null;
    });

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


// ============================================================
// APP LIFECYCLE — with both fixes applied
// ============================================================
app.whenReady().then(async () => {
  console.log('🚀 Mnemos starting...');
  console.log('📦 app.isPackaged:', app.isPackaged);
  console.log('📂 userData:', app.getPath('userData'));

  // FIX #1: Create directories AFTER app is ready
  initializeDirectories();

  await initializeStores();

  // FIX #2: Start production frontend server if packaged
  await startProductionFrontend();

  console.log('🌐 FRONTEND_URL is now:', FRONTEND_URL);

  createMainWindow();

  const isAuthenticated = await TokenManager.isAuthenticated();
  if (isAuthenticated) {
    console.log('✅ User already authenticated, creating floating button...');
    store.set('buttonPosition', { x: 300, y: 300 });
    createFloatingButton();

    startProactiveNotifications();
  }

  registerShortcuts();

  console.log('✅ Mnemos ready!');
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
  globalShortcut.unregisterAll();
});

process.on('uncaughtException', (error) => {
  console.error('❌ Uncaught exception:', error);
});