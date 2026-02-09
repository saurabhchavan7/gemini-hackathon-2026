const { BrowserWindow } = require('electron');
const http = require('http');
const url = require('url');

// // OAuth Configuration
// const GOOGLE_OAUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth';
// const REDIRECT_URI = 'http://localhost:3001/auth/callback';

// // TODO: Replace with your actual Google OAuth Client ID from GCP Console
// const CLIENT_ID = process.env.GOOGLE_CLIENT_ID || '1056690364460-apvbfvf53jk5m7i4p8hc0rbrn05np80e.apps.googleusercontent.com';

// OAuth Configuration
const GOOGLE_OAUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth';
const REDIRECT_URI = 'http://localhost:3001/auth/callback';

// TODO: Replace with your actual Google OAuth Client ID from GCP Console
const CLIENT_ID = process.env.GOOGLE_CLIENT_ID || '1056690364460-4a9srp0ioirfu8c3gbaomtsrher3bjj9.apps.googleusercontent.com';

// OAuth scopes needed for LifeOS

// OAuth scopes needed for LifeOS
const SCOPES = [
  'openid',
  'email',
  'profile',
  'https://www.googleapis.com/auth/calendar',
  'https://www.googleapis.com/auth/tasks',
  'https://www.googleapis.com/auth/gmail.readonly',
  'https://www.googleapis.com/auth/gmail.compose'
].join(' ');

/**
 * Start OAuth flow and return authorization code
 */
async function startOAuthFlow() {
  return new Promise((resolve, reject) => {
    // Build OAuth URL
    const authUrl = `${GOOGLE_OAUTH_URL}?` + 
      `client_id=${CLIENT_ID}&` +
      `redirect_uri=${encodeURIComponent(REDIRECT_URI)}&` +
      `response_type=code&` +
      `scope=${encodeURIComponent(SCOPES)}&` +
      `access_type=offline&` +
      `prompt=consent`;

    // Create local server to receive callback
    const server = http.createServer(async (req, res) => {
      try {
        const queryData = url.parse(req.url, true).query;

        if (queryData.code) {
          // Success - got authorization code
          res.writeHead(200, { 'Content-Type': 'text/html' });
          res.end(`
            <html>
              <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>Authentication Successful!</h1>
                <p>You can close this window and return to Mnemos App.</p>
                <script>window.close();</script>
              </body>
            </html>
          `);

          server.close();
          resolve(queryData.code);
        } else if (queryData.error) {
          // Error from Google
          res.writeHead(400, { 'Content-Type': 'text/html' });
          res.end(`
            <html>
              <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>❌ Authentication Failed</h1>
                <p>Error: ${queryData.error}</p>
                <p>You can close this window.</p>
              </body>
            </html>
          `);

          server.close();
          reject(new Error(queryData.error));
        }
      } catch (error) {
        server.close();
        reject(error);
      }
    });

    // Start server on port 3001
    server.listen(3001, () => {
      console.log('🔐 OAuth callback server listening on port 3001');
      
      // Open system browser with OAuth URL
      require('electron').shell.openExternal(authUrl);
    });

    // Handle server errors
    server.on('error', (error) => {
      reject(error);
    });

    // Timeout after 5 minutes
    setTimeout(() => {
      server.close();
      reject(new Error('OAuth flow timeout'));
    }, 5 * 60 * 1000);
  });
}

module.exports = {
  startOAuthFlow
};
