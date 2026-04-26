# 🚀 Taji Deployment Guide

## ⚠️ IMPORTANT: Duplicate Project Structure

Your project has **TWO copies** of the codebase:

1. **Root level** (for local development):
   - `templates/`, `core/`, `loans/`, `static/`

2. **Inside `taji/` folder** (what Render deploys):
   - `taji/templates/`, `taji/core/`, `taji/loans/`, `taji/static/`

## 🔧 How to Deploy Changes

### Option 1: Edit Files in `taji/` Folder Directly (Recommended)

Always edit files inside the `taji/` folder:
- ✅ `taji/templates/core/login.html`
- ✅ `taji/static/css/taji.css`
- ✅ `taji/core/views.py`

**NOT** the root-level files:
- ❌ `templates/core/login.html`
- ❌ `static/css/taji.css`
- ❌ `core/views.py`

### Option 2: Use the Sync Script

If you edited root-level files, run the sync script before committing:

**On Windows:**
```bash
./sync-to-taji.bat
```

**On Mac/Linux:**
```bash
bash sync-to-taji.sh
```

Then commit and push:
```bash
git add taji/
git commit -m "Your changes"
git push origin main
```

## 📱 Viewing Changes on Mobile

After pushing to GitHub:

1. **Wait 2-3 minutes** for Render to deploy
2. **Check Render dashboard** for "Deploy succeeded"
3. **Clear browser cache** on your phone:
   - iPhone: Settings → Safari → Clear History and Website Data
   - Android: Chrome Settings → Privacy → Clear browsing data
4. **Or use incognito/private mode** to bypass cache

## 🔍 Troubleshooting

### Changes not showing after deployment?

1. Check you edited files in `taji/` folder, not root
2. Verify Render deployment succeeded (check logs)
3. Clear browser cache or use incognito mode
4. Check the CSS version in base.html: `taji.css?v=1.1`

### How to verify which files Render uses?

Run locally from project root:
```bash
cd taji
python manage.py runserver
```

This mimics what Render does.

## 📂 Project Structure

```
Taji/
├── taji/                    ← RENDER DEPLOYS THIS
│   ├── templates/
│   ├── static/
│   ├── core/
│   ├── loans/
│   ├── manage.py
│   └── settings.py
├── templates/               ← Local development only
├── static/                  ← Local development only
├── core/                    ← Local development only
├── loans/                   ← Local development only
├── manage.py                ← Points to taji/settings.py
└── render.yaml              ← Deployment config
```
