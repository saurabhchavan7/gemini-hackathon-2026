# LifeOS - Google Integration Documentation

## Overview
LifeOS now integrates with Google Calendar, Google Tasks, and Gmail to automatically organize your digital life.

## Features

### 1. Google Calendar Integration
- **Auto-create events** when Agent 2 detects meeting invitations
- **Conflict detection** warns about scheduling conflicts
- **Bi-directional sync** - events stored in both Google Calendar and Firestore

### 2. Google Tasks Integration
- **Auto-create tasks** for action items without specific times
- **Due date extraction** from natural language
- **Complete tasks** via API

### 3. Shopping List (Firestore)
- **Auto-add items** when products are detected
- **Price tracking** extracts prices from screenshots
- **Status management** (pending, purchased, dismissed)

## Architecture
```
Electron Capture
    ↓
Agent 1 (Perception) - OCR + Audio
    ↓
Agent 2 (Intent) - Categorization
    ↓
Event Bus (Non-blocking)
    ↓
Agent 3 (Orchestrator) - Tool Selection
    ├→ Google Calendar API
    ├→ Google Tasks API
    └→ Firestore (Shopping/Notes)
```

## API Endpoints

### Authentication
- `GET /api/google/sync-status` - Check if user authenticated
- `GET /api/google/auth-url` - Get OAuth URL for first-time setup
- `POST /api/google/authenticate` - Trigger OAuth flow

### Data Retrieval
- `GET /api/google/calendar/events` - Get upcoming calendar events
- `GET /api/google/tasks` - Get active tasks
- `GET /api/shopping-list` - Get shopping list items
- `GET /api/inbox` - Get all memories with AI insights

### Actions
- `POST /api/google/tasks/{task_id}/complete` - Mark task as done

## Setup Instructions

### For Development:
1. Enable APIs in Google Cloud Console
2. Create OAuth credentials (Desktop app)
3. Download `google_credentials.json`
4. Place in `backend/` folder
5. First user authenticates via OAuth flow
6. Token saved in `tokens/token_{user_id}.pickle`

### For Production (.exe):
1. Users click "Connect Google" in settings
2. Browser opens with OAuth consent
3. After approval, token saved locally
4. All future captures auto-sync

## Rate Limits & Optimization

### Current Optimizations:
- **Deterministic routing** - Simple intents skip Gemini (Purchase, Task, Reference)
- **Event bus delays** - 5 seconds between agent activations
- **Exponential backoff** - 10s, 20s, 30s retry delays
- **Batch processing** - Multiple captures grouped when possible

### Quotas (Gemini 2.0 Flash):
- 2,000 requests per minute
- Current usage: ~3-5 requests per capture
- Can handle ~400 captures per minute

## Data Flow

### When User Takes Screenshot:

1. **Electron** captures screenshot + context
2. **Agent 1** extracts text (OCR) and transcribes audio
3. **Agent 2** analyzes intent:
   - Event → Google Calendar
   - Task → Google Tasks
   - Purchase → Shopping List (Firestore)
   - Reference → Notes (Firestore)
4. **Agent 3** executes appropriate tool
5. **Agent 4** researches if needed (code errors)
6. **Agent 7** provides proactive tips (conflicts, prices)

### Data Storage:
```
Firestore Structure:
users/{userId}/
├── captures/              # Raw data
├── memories/              # AI analysis
├── google_calendar_events/  # Local cache + Google ID
├── google_tasks/          # Local cache + Google ID
├── shopping_lists/        # Firestore only
└── notes/                 # Firestore only
```

## Testing

Run these tests to verify:
```bash
# Test authentication
python test_google_auth.py

# Test individual services
python test_google_integrations.py

# Test agent pipeline
python test_full_pipeline.py

# Test complete flow
python test_real_flow.py
```

## Troubleshooting

### Issue: Rate Limit Errors
**Solution**: Already implemented exponential backoff and delays

### Issue: User not authenticated
**Solution**: Call `/api/google/auth-url` and direct user to OAuth

### Issue: Token expired
**Solution**: Auto-refresh implemented in `GoogleAuthService`

## Future Enhancements

1. **Gmail Integration** - Draft emails from screenshots
2. **Notion/Trello** - Export to project management tools
3. **Smart Suggestions** - ML-based task prioritization
4. **Conflict Resolution** - Auto-reschedule conflicts
5. **Voice Commands** - "Add this to my calendar"

## Security Notes

- OAuth tokens stored locally per user
- Tokens never sent to backend (handled on device)
- API credentials in `.gitignore`
- JWT authentication required for all endpoints