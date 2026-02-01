# Deployment Checklist

## Before Building .exe

### Backend Setup
- [ ] All test files removed or in `.gitignore`
- [ ] `google_credentials.json` in project root
- [ ] `tokens/` folder in `.gitignore`
- [ ] Environment variables in `.env` file
- [ ] All dependencies in `requirements.txt`

### Testing
- [ ] `python test_google_auth.py` passes
- [ ] `python test_google_integrations.py` passes
- [ ] `python test_full_pipeline.py` passes
- [ ] All 7 agents working independently

### Security
- [ ] No API keys in code (only in `.env`)
- [ ] `.gitignore` covers all sensitive files
- [ ] JWT secret is randomized
- [ ] OAuth credentials are user-specific

### API Endpoints
- [ ] `/api/capture` working with Electron
- [ ] `/api/google/calendar/events` returns data
- [ ] `/api/google/tasks` returns data
- [ ] `/api/shopping-list` returns data
- [ ] `/api/inbox` returns memories

## After Building .exe

### User Flow
- [ ] User logs in with Google (OAuth)
- [ ] User connects Google Calendar/Tasks (OAuth)
- [ ] User takes first screenshot
- [ ] Event auto-created in Google Calendar
- [ ] User can view events in app

### Distribution
- [ ] Include setup instructions
- [ ] Include OAuth setup guide
- [ ] Test on clean Windows machine
- [ ] Verify no hardcoded paths