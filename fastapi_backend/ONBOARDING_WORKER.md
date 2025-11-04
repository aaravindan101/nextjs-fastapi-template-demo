# Email Onboarding Worker

This document explains the onboarding mode implementation for automated email reading and labeling.

## Overview

The onboarding worker is a background process that:
1. Reads emails from Gmail (5 at a time)
2. Analyzes each email using Anthropic Claude AI
3. Automatically applies labels based on the analysis
4. Runs every 30 seconds until all emails are processed

## Architecture

### Components

1. **User Model Extensions** ([models.py](app/models.py))
   - `last_pointer`: Gmail pagination token
   - `onboarding_complete`: Flag (0 = in progress, 1 = complete)
   - `last_sync`: Timestamp of last email sync

2. **Gmail Service** ([services/gmail_service.py](app/services/gmail_service.py))
   - `email_reader()`: Fetches 5 emails with full thread context
   - `get_or_create_label_id()`: Manages Gmail labels
   - `modify_message_labels()`: Adds/removes labels from emails

3. **Labeling Service** ([services/labeling_service.py](app/services/labeling_service.py))
   - `label_email()`: Processes emails and applies AI-based labels
   - Uses Anthropic Claude to categorize emails into:
     - **ACTION_NEEDED**: Requires user action
     - **FYI**: Informational only
     - **SPAM**: Suspicious content
     - **EXTRA**: Everything else

4. **Onboarding Worker** ([workers/onboarding_worker.py](app/workers/onboarding_worker.py))
   - Background process that runs every 30 seconds
   - Processes all users with `onboarding_complete = 0`
   - Automatically marks onboarding as complete when done

## Setup

### 1. Install Dependencies

```bash
cd fastapi_backend
uv sync
```

This will install the new dependencies:
- `google-api-python-client`: Gmail API client
- `google-auth`: OAuth2 authentication
- `anthropic`: Claude AI client

### 2. Run Database Migration

```bash
cd fastapi_backend
# Run migration to add new fields to user table
alembic upgrade head
```

### 3. Configure Environment Variables

Add these to your `.env` file:

```bash
# Gmail API OAuth2 access token
GMAIL_TOKEN=your_gmail_oauth_token

# Anthropic API key for Claude
ANTHROPIC_API_KEY=your_anthropic_api_key
```

#### Getting a Gmail Token

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Gmail API
3. Create OAuth2 credentials
4. Generate an access token using the OAuth2 flow
5. Add the token to your `.env` file

#### Getting an Anthropic API Key

1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Create an API key
3. Add it to your `.env` file

## Running the Onboarding Worker

### Start the Worker

```bash
cd fastapi_backend
python run_worker.py
```

You should see output like:

```
============================================================
Email Onboarding Worker
============================================================

Onboarding worker started
Running every 30 seconds...

[2025-11-04T23:45:00] Running onboarding cycle...
Processing emails for 2 user(s)
Processing user: user@example.com
Labeled email abc123 as ACTION_NEEDED
Labeled email def456 as FYI
Processed 5 emails for user user@example.com, more emails remaining
Waiting 30 seconds until next cycle...
```

### Stop the Worker

Press `Ctrl+C` to gracefully stop the worker.

## How It Works

### Workflow

1. **Every 30 seconds**, the worker:
   - Queries database for users with `onboarding_complete = 0`
   - For each user:
     - Calls `email_reader()` with their `last_pointer`
     - Gets 5 emails with full thread context
     - Passes emails to `label_email()`
     - Updates `last_pointer` and `last_sync` in database

2. **Email Reading** (`email_reader`):
   - Fetches 5 messages from Gmail
   - For each message, gets the full thread
   - Extracts:
     - Headers (From, To, Subject, Date)
     - Body text (plain text or HTML)
     - Attachments info
   - Returns structured data with thread context

3. **Email Labeling** (`label_email`):
   - Skips emails that are part of a thread (not main email)
   - Combines all thread message bodies for context
   - Sends to Anthropic Claude for analysis
   - Removes existing Gmail system labels
   - Creates custom label if needed
   - Applies new label to email

4. **Completion**:
   - When `nextPointer` is `None`, no more emails remain
   - Worker sets `onboarding_complete = 1`
   - User is skipped in future cycles

### Email Categories

The AI analyzes emails and assigns one of four labels:

| Label | Description | Example |
|-------|-------------|---------|
| `ACTION_NEEDED` | User must take action | Meeting requests, tasks, replies needed |
| `FYI` | Informational only | Newsletters, status updates, announcements |
| `SPAM` | Suspicious content | Short URLs, suspicious attachments |
| `EXTRA` | Everything else | Social media notifications, promotions |

## Database Schema

The migration adds these fields to the `user` table:

```sql
ALTER TABLE user ADD COLUMN last_pointer VARCHAR NULL;
ALTER TABLE user ADD COLUMN onboarding_complete INTEGER DEFAULT 0;
ALTER TABLE user ADD COLUMN last_sync DATETIME NULL;
```

## Monitoring

### Check Onboarding Status

Query the database to see user onboarding status:

```sql
SELECT
    email,
    onboarding_complete,
    last_sync,
    last_pointer
FROM user;
```

### Worker Logs

The worker prints detailed logs:
- Number of users being processed
- Emails labeled and their categories
- Completion status
- Errors (if any)

## Troubleshooting

### Worker Won't Start

**Error**: `Gmail token or Anthropic API key not configured`

**Solution**: Check your `.env` file has both `GMAIL_TOKEN` and `ANTHROPIC_API_KEY` set.

### Gmail API Errors

**Error**: `Gmail API error: 401 Unauthorized`

**Solution**: Your Gmail token may have expired. Generate a new token.

**Error**: `Gmail API error: 403 Forbidden`

**Solution**: Ensure Gmail API is enabled in Google Cloud Console.

### No Emails Processed

**Cause**: Users have `onboarding_complete = 1`

**Solution**: Reset the flag for testing:

```sql
UPDATE user SET onboarding_complete = 0, last_pointer = NULL WHERE email = 'test@example.com';
```

## Testing

### Manual Test

1. Create a test user in the database
2. Ensure `onboarding_complete = 0`
3. Start the worker
4. Check logs for email processing
5. Verify labels in Gmail

### Reset Onboarding

To reprocess emails for a user:

```sql
UPDATE user
SET onboarding_complete = 0, last_pointer = NULL, last_sync = NULL
WHERE email = 'user@example.com';
```

## Production Considerations

1. **Rate Limiting**: Gmail API has quotas. Monitor usage in Google Cloud Console.

2. **Token Refresh**: Implement OAuth2 refresh token flow for long-running workers.

3. **Error Handling**: The worker continues on errors but logs them. Monitor logs.

4. **Scaling**: Run multiple workers for different user segments.

5. **Monitoring**: Add metrics (emails processed, errors, latency) for production.

## Next Steps

After implementing onboarding mode, you can:
1. Implement **Live Mode** with Gmail webhooks (Pub/Sub)
2. Add a frontend UI to trigger onboarding
3. Show onboarding progress to users
4. Allow users to customize label categories

## File Structure

```
fastapi_backend/
├── app/
│   ├── models.py                      # User model with Gmail fields
│   ├── config.py                      # Settings with Gmail/Anthropic config
│   ├── services/
│   │   ├── gmail_service.py           # Gmail API integration
│   │   └── labeling_service.py        # AI-powered labeling
│   └── workers/
│       └── onboarding_worker.py       # Background worker
├── alembic_migrations/
│   └── versions/
│       └── b1f2c3d4e5f6_add_gmail_fields_to_user.py  # Migration
├── run_worker.py                      # Worker entry point
└── ONBOARDING_WORKER.md              # This file
```

## API Reference

### `GmailService.email_reader(last_pointer)`

**Parameters:**
- `last_pointer` (str, optional): Pagination token

**Returns:**
```python
{
    "nextPointer": str | None,
    "emails": [
        {
            "threadId": str,
            "historyId": str,
            "mainEmail": {...},
            "threadMessages": [...]
        }
    ]
}
```

### `LabelingService.label_email(email_reader_output)`

**Parameters:**
- `email_reader_output`: Output from `email_reader()`

**Returns:**
- `"Labeling complete"` (str)

**Side Effects:**
- Modifies Gmail labels for each email
- Creates new labels if needed

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify API keys and tokens are valid
3. Ensure database migration ran successfully
4. Check Gmail API quotas in Google Cloud Console
