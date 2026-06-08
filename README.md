# Haute-Savoie Administrative Acts Monitor

Automated monitoring tool that scrapes the Haute-Savoie prefecture's administrative acts, searches for specific terms, and sends email notifications.

## Features

- 📥 Scrapes new documents from the prefecture website
- 🔍 Searches PDF content for configurable terms (case-insensitive)
- 📧 Sends HTML email notifications with matches
- 💾 Tracks processed documents to avoid duplicates
- ⚙️ Fully configurable via JSON
- 🔄 Designed for cron job execution

## Setup

### 1. Install Dependencies

```fish
cd /tmp/haute-savoie-monitor
python3 -m venv venv
source venv/bin/activate.fish
pip install -r requirements.txt
```

### 2. Configure Email

Edit `config.json` and set your email settings:

#### For Gmail:

1. Enable 2-factor authentication in your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the app password (not your regular password) in `config.json`

```json
{
  "email": {
    "server": "smtp.gmail.com",
    "port": 587,
    "from": "your-email@gmail.com",
    "to": "recipient@example.com",
    "username": "your-email@gmail.com",
    "password": "your-16-char-app-password"
  }
}
```

#### For other email providers:

- **Outlook/Hotmail**: `smtp.office365.com:587`
- **Yahoo**: `smtp.mail.yahoo.com:587`
- **Custom SMTP**: Use your provider's settings

### 3. Configure Search Terms

Edit the `search_terms` array in `config.json`:

```json
{
  "search_terms": ["Jourdies", "JOURDIES", "Another Term", "Multiple Words"]
}
```

Search is case-insensitive with word boundary matching.

### 4. Test Run

```fish
python monitor.py
```

Check the output for any errors. A `state.json` file will be created to track processed documents.

## Cron Job Setup

### Run every 4 hours during business hours

```fish
# Edit crontab
crontab -e

# Add this line (adjust path to your installation):
0 8,12,16 * * * cd /tmp/haute-savoie-monitor && ./venv/bin/python monitor.py >> monitor.log 2>&1
```

This runs at 8am, 12pm, and 4pm daily.

### Other scheduling options:

```bash
# Every 2 hours (8am to 6pm)
0 8-18/2 * * * cd /tmp/haute-savoie-monitor && ./venv/bin/python monitor.py >> monitor.log 2>&1

# Twice daily (9am and 5pm)
0 9,17 * * * cd /tmp/haute-savoie-monitor && ./venv/bin/python monitor.py >> monitor.log 2>&1

# Every hour on weekdays
0 * * * 1-5 cd /tmp/haute-savoie-monitor && ./venv/bin/python monitor.py >> monitor.log 2>&1
```

## Configuration Reference

### `config.json` Options

| Option               | Description                                 | Default        |
| -------------------- | ------------------------------------------- | -------------- |
| `year`               | Year to monitor                             | 2026           |
| `max_pages_to_check` | How many pages to scrape (10 docs per page) | 3              |
| `state_file`         | Where to store processing state             | state.json     |
| `search_terms`       | Array of terms to search for                | ["Jourdies"]   |
| `email.server`       | SMTP server address                         | smtp.gmail.com |
| `email.port`         | SMTP port (usually 587 for TLS)             | 587            |
| `email.from`         | Sender email address                        | -              |
| `email.to`           | Recipient email address                     | -              |
| `email.username`     | SMTP username (usually same as from)        | -              |
| `email.password`     | SMTP password or app password               | -              |

### State File (`state.json`)

Automatically managed by the script:

```json
{
  "last_check": "2026-06-08T10:30:00",
  "processed_docs": ["51276", "51275", ...],
  "matches_found": [
    {
      "id": "51276",
      "title": "RAA_etat74_20260608_227",
      "url": "https://...",
      "found_terms": ["Jourdies"],
      "found_at": "2026-06-08T10:30:00"
    }
  ]
}
```

## Logs

View recent activity:

```fish
tail -f monitor.log
```

## Troubleshooting

### No email received:

1. Check spam folder
2. Verify SMTP credentials in `config.json`
3. For Gmail, ensure App Password is used (not regular password)
4. Check `monitor.log` for errors

### PDFs not parsing:

- Some scanned PDFs may need OCR (not included by default)
- Check if PDF is actually downloadable manually
- Verify internet connection

### Reset state (reprocess all documents):

```fish
rm state.json
```

## Security Notes

⚠️ **Important**: `config.json` contains sensitive credentials!

```fish
# Set proper permissions
chmod 600 config.json

# Or use environment variables (advanced)
# Modify monitor.py to read from os.environ
```

## Advanced Usage

### Multiple search configurations:

Create different config files and run separately:

```fish
python monitor.py config_jourdies.json
python monitor.py config_other_terms.json
```

### Custom year monitoring:

Change the `year` in config.json to monitor different years (2025, 2024, etc.)

## License

MIT License - Free to use and modify
# jourdies-notifier
