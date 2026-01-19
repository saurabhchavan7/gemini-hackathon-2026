// setup-electron.js
const fs = require('fs');
const path = require('path');

// Electron main process
const electronMain = `const { app, BrowserWindow } = require('electron');
const path = require('path');
const isDev = process.env.NODE_ENV === 'development';

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  const startUrl = isDev 
    ? 'http://localhost:3000'
    : \`file://\${path.join(__dirname, 'dist/index.html')}\`;
  
  mainWindow.loadURL(startUrl);
  
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
`;

// Write electron.js
fs.writeFileSync('electron.js', electronMain);
console.log('✅ Created electron.js');

// Update package.json
const packageJsonPath = 'package.json';
if (fs.existsSync(packageJsonPath)) {
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  
  packageJson.main = 'electron.js';
  packageJson.scripts = {
    ...packageJson.scripts,
    'electron': 'electron .',
    'electron-dev': 'concurrently "npm run dev" "wait-on http://localhost:3000 && cross-env NODE_ENV=development electron ."'
  };
  
  fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
  console.log('✅ Updated package.json');
}

console.log('\n🎉 Electron setup complete!');
console.log('\nNext steps:');
console.log('1. Run: npm run dev (in one terminal)');
console.log('2. Run: npm run electron (in another terminal)');
console.log('\nOr run both together: npm run electron-dev');