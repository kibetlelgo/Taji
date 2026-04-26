#!/bin/bash
# Sync changes from root folders to taji/ folder
# Run this script before committing to ensure Render gets your changes

echo "🔄 Syncing files to taji/ folder..."

# Sync CSS files
if [ -d "static/css" ]; then
    echo "📝 Syncing CSS files..."
    cp -r static/css/* taji/static/css/
fi

# Sync templates
if [ -d "templates" ]; then
    echo "📝 Syncing templates..."
    cp -r templates/* taji/templates/
fi

# Sync core app
if [ -d "core" ]; then
    echo "📝 Syncing core app..."
    cp -r core/* taji/core/
fi

# Sync loans app
if [ -d "loans" ]; then
    echo "📝 Syncing loans app..."
    cp -r loans/* taji/loans/
fi

echo "✅ Sync complete! Now you can commit and push."
echo ""
echo "Next steps:"
echo "  git add taji/"
echo "  git commit -m 'Your commit message'"
echo "  git push origin main"
