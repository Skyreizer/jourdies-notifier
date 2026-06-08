# Quick Start Guide

## ✅ Installation Complete!

Your Haute-Savoie monitor is installed at: `/tmp/haute-savoie-monitor/`

## 📝 Next Steps

### 1. Configure Email Settings

```bash
cd /tmp/haute-savoie-monitor
nano config.json  # or vim, code, etc.
```

**Update these fields:**

- `email.from` - Your email address
- `email.to` - Where to send notifications
- `email.username` - Usually same as 'from'
- `email.password` - Gmail App Password (not your regular password!)

**Get Gmail App Password:**

1. Go to: https://myaccount.google.com/apppasswords
2. Enable 2FA if needed
3. Create app password for "Mail"
4. Copy the 16-character password
5. Paste into config.json

### 2. Test It

```bash
source venv/bin/activate.fish
python monitor.py
```

**Expected output:**

```
🔍 Starting Haute-Savoie Acts Monitor - 2026-06-08 ...
   Searching for: Jourdies, JOURDIES
📥 Scraping documents...
   Found X new document(s) to check
   [1/X] Processing: RAA_etat74_...
✓ Monitor completed
```

### 3. Set Up Cron Job

```bash
crontab -e
```

**Add one of these lines:**

```bash
# Check 3 times daily (9am, 1pm, 5pm)
0 9,13,17 * * * cd /tmp/haute-savoie-monitor && ./venv/bin/python monitor.py >> monitor.log 2>&1

# Check every 4 hours during business hours (8am-8pm)
0 8-20/4 * * * cd /tmp/haute-savoie-monitor && ./venv/bin/python monitor.py >> monitor.log 2>&1

# Check every 2 hours on weekdays
0 */2 * * 1-5 cd /tmp/haute-savoie-monitor && ./venv/bin/python monitor.py >> monitor.log 2>&1
```

### 4. Monitor Logs

```bash
# View recent activity
tail -f monitor.log

# See all matches found
cat state.json | grep -A5 matches_found
```

## 🎯 Customization

### Change Search Terms

Edit `config.json`:

```json
{
  "search_terms": [
    "Jourdies",
    "Your Name",
    "Another Term",
    "Multiple Words Work Too"
  ]
}
```

Search is **case-insensitive** with word boundaries.

### Change Year

```json
{
  "year": 2025 // Monitor a different year
}
```

### Increase Pages to Check

```json
{
  "max_pages_to_check": 5 // Check first 50 documents (10 per page)
}
```

## 🔧 Maintenance

### Reset State (Reprocess All Documents)

```bash
rm state.json
python monitor.py
```

### Update Dependencies

```bash
source venv/bin/activate.fish
pip install --upgrade -r requirements.txt
```

### View Processing History

```bash
cat state.json | jq '.matches_found'  # Requires jq
# Or just:
cat state.json
```

## 📧 Email Notification Format

When a match is found, you'll receive:

**Subject:** 🔔 1 match(es) found in Haute-Savoie Acts

**Content:**

- Document title with clickable link
- Publication date
- Which search terms were found
- Beautiful HTML formatting

## 🚨 Troubleshooting

### No email received?

1. Check spam folder
2. Verify Gmail App Password (not regular password)
3. Check `monitor.log` for errors
4. Test SMTP: `python -c "import smtplib; print('OK')"`

### Script not finding new documents?

- Check internet connection
- Website might be temporarily down
- Check `monitor.log` for errors

### Permissions error?

```bash
chmod +x monitor.py
chmod 600 config.json  # Protect credentials
```

## 📚 Files Explained

- `monitor.py` - Main script (don't edit unless you know Python)
- `config.json` - **Your settings** (edit this!)
- `state.json` - Auto-generated, tracks processed documents
- `monitor.log` - Auto-generated when run via cron
- `venv/` - Python virtual environment (don't touch)

## 🎓 Pro Tips

1. **Start small**: Let it run once manually first
2. **Check logs regularly**: `tail monitor.log`
3. **Backup state**: `cp state.json state.json.backup`
4. **Multiple searches**: Create different config files for different terms
5. **Security**: Never commit `config.json` to git (it's in `.gitignore`)

---

**Need help?** Check the full README.md for detailed documentation.
