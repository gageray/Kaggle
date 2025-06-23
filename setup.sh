#!/bin/bash
# Kaggle + Google Drive CLI Setup Script
set -e

echo "🚀 KAGGLE + GOOGLE DRIVE CLI SETUP"
echo "=================================="

# Check if running in correct directory
if [ ! -f "setup.sh" ]; then
    echo "❌ Error: Run this script from the CLI Tools directory"
    exit 1
fi

# Install Python dependencies from config
echo "📦 Installing Python dependencies..."
python3 -c "
import yaml
with open('config/project.yaml', 'r') as f:
    config = yaml.safe_load(f)
    packages = ' '.join(config['dependencies']['python_packages'])
    print(packages)
" | xargs pip install

# Make CLI executable
echo "🔧 Setting up CLI tool..."
chmod +x scripts/kaggle_drive_cli.py

# Create symlink for easy access
if [ ! -L "/usr/local/bin/kdcli" ]; then
    echo "🔗 Creating global CLI command..."
    sudo ln -sf "$(pwd)/scripts/kaggle_drive_cli.py" /usr/local/bin/kdcli
    echo "✅ You can now use 'kdcli' from anywhere!"
fi

# Check for Kaggle API setup using config
echo "🔑 Checking Kaggle API setup..."
KAGGLE_KEY=$(python3 -c "
import yaml
with open('config/project.yaml', 'r') as f:
    config = yaml.safe_load(f)
    print(config['paths']['kaggle_credentials'])
")

if [ ! -f "$KAGGLE_KEY" ]; then
    echo "⚠️  Kaggle API not configured!"
    echo "   Expected location: $KAGGLE_KEY"
    echo "   1. Go to https://www.kaggle.com/account"
    echo "   2. Create new API token"
    echo "   3. Save as $KAGGLE_KEY"
    echo ""
    read -p "Have you set up your Kaggle API key? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Please set up Kaggle API first, then run this script again"
        exit 1
    fi
fi

# Check Kaggle CLI
echo "🧪 Testing Kaggle CLI..."
if kaggle --version > /dev/null 2>&1; then
    echo "✅ Kaggle CLI working"
else
    echo "❌ Kaggle CLI not working. Check your API setup."
    exit 1
fi

# Check for Google Drive credentials using config
echo "☁️  Checking Google Drive setup..."
DRIVE_KEY=$(python3 -c "
import yaml
with open('config/project.yaml', 'r') as f:
    config = yaml.safe_load(f)
    print(config['paths']['drive_credentials'])
")

if [ ! -f "$DRIVE_KEY" ]; then
    echo "⚠️  Google Drive credentials not found!"
    echo "   Expected location: $DRIVE_KEY"
    echo "   1. Go to https://console.cloud.google.com/apis/credentials"
    echo "   2. Create OAuth 2.0 credentials"
    echo "   3. Download and save as $DRIVE_KEY"
    echo ""
    echo "   Optional: Skip if you don't need Google Drive sync"
    read -p "Continue without Google Drive? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Please add Google Drive credentials first"
        exit 1
    fi
fi

# Run CLI setup
echo "⚙️  Initializing CLI configuration..."
python3 scripts/kaggle_drive_cli.py setup

echo ""
echo "🎉 SETUP COMPLETE!"
echo "=================="
echo ""
echo "📖 USAGE:"
echo "   kdcli status          # Show current status"
echo "   kdcli list            # List your Kaggle kernels"
echo "   kdcli sync --kernel <name>  # Sync kernel to Drive"
echo ""
echo "📁 PROJECT STRUCTURE:"
echo "   src/              # Main CLI source code"
echo "   scripts/          # Automation scripts"
echo "   templates/        # Project templates"
echo "   config/           # Configuration files"
echo ""
echo "🔐 SECURITY:"
echo "   • All API keys are in .gitignore"
echo "   • Never commit credentials to git"
echo ""
echo "▶️  Try: kdcli status"