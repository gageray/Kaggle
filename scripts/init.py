#!/usr/bin/env python3
"""
Kaggle CLI Automation Tool - Project Initializer
Creates a new automated Kaggle workflow project
"""

import os
import sys
import json
import argparse
from pathlib import Path

def create_project_structure(project_name, username):
    """Create the complete project directory structure"""
    
    project_path = Path(project_name)
    
    # Create directories
    directories = [
        project_path,
        project_path / "out",
        project_path / ".kaggle"
    ]
    
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create kernel-metadata.json
    kernel_metadata = {
        "id": f"{username}/{project_name.lower().replace(' ', '-')}",
        "title": f"{project_name} - Automated Kernel",
        "code_file": "script.py",
        "language": "python",
        "kernel_type": "script",
        "enable_gpu": True,
        "enable_internet": False,
        "is_private": True
    }
    
    with open(project_path / "kernel-metadata.json", "w") as f:
        json.dump(kernel_metadata, f, indent=2)
    print(f"Created kernel-metadata.json")
    
    # Create example script.py
    script_template = '''#!/usr/bin/env python3
"""
Your main ML/Data Science script
This runs on Kaggle's free GPU/TPU compute
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    print("STARTING: Kaggle automation script...")
    
    # Your ML code here
    # Example: Load data, train model, generate outputs
    
    # Save results to be downloaded
    results = {"status": "completed", "accuracy": 0.95}
    pd.DataFrame([results]).to_csv("results.csv", index=False)
    
    print("SUCCESS: Script completed successfully!")
    print("Results saved to results.csv")

if __name__ == "__main__":
    main()
'''
    
    with open(project_path / "script.py", "w") as f:
        f.write(script_template)
    print(f"SUCCESS: Created script.py template")
    
    # Create upload-to-drive.py
    drive_script = '''#!/usr/bin/env python3
"""
Upload Kaggle outputs to Google Drive
Requires Google Cloud credentials.json
"""

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate():
    """Authenticate with Google Drive API"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        if not os.path.exists('credentials.json'):
            print("ERROR: credentials.json not found!")
            print("Download it from Google Cloud Console:")
            print("https://console.cloud.google.com/apis/credentials")
            return None
        
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as f:
            f.write(creds.to_json())
    return creds

def upload_file(service, filepath, parent_folder_id=None):
    """Upload a single file to Google Drive"""
    file_metadata = {'name': os.path.basename(filepath)}
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]

    media = MediaFileUpload(filepath, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"UPLOAD: Uploaded {filepath} -> File ID: {file['id']}")

def main():
    """Upload all files in out/ directory to Google Drive"""
    creds = authenticate()
    if not creds:
        return
    
    service = build('drive', 'v3', credentials=creds)
    
    out_dir = 'out'
    if not os.path.exists(out_dir):
        print(f"ERROR: {out_dir} directory not found!")
        return
    
    files = os.listdir(out_dir)
    if not files:
        print(f"WARNING: No files found in {out_dir}/")
        return
    
    print(f"UPLOAD: Uploading {len(files)} files to Google Drive...")
    for filename in files:
        filepath = os.path.join(out_dir, filename)
        if os.path.isfile(filepath):
            upload_file(service, filepath)
    
    print("SUCCESS: Upload complete!")

if __name__ == '__main__':
    main()
'''
    
    with open(project_path / "upload-to-drive.py", "w") as f:
        f.write(drive_script)
    print(f"SUCCESS: Created upload-to-drive.py")
    
    # Create main automation script
    automation_script = f'''#!/bin/bash
# Kaggle CLI Automation Script
# Runs your code on Kaggle's free compute and downloads results

set -e

PROJECT_NAME="{project_name}"
KERNEL_ID="{username}/{project_name.lower().replace(' ', '-')}"

echo "STARTING: Kaggle automation workflow..."

# Push kernel to Kaggle
echo "UPLOAD: Pushing to Kaggle..."
kaggle kernels push

# Wait for execution to start
echo "WAITING: Waiting for kernel to start..."
sleep 30

# Monitor status
echo "MONITORING: Monitoring kernel status..."
while true; do
    STATUS=$(kaggle kernels status $KERNEL_ID --quiet | tail -1)
    echo "Status: $STATUS"
    
    if [[ "$STATUS" == *"complete"* ]]; then
        echo "SUCCESS: Kernel completed successfully!"
        break
    elif [[ "$STATUS" == *"error"* ]] || [[ "$STATUS" == *"failed"* ]]; then
        echo "ERROR: Kernel failed!"
        exit 1
    fi
    
    echo "Still running... checking again in 60 seconds"
    sleep 60
done

# Download outputs
echo "DOWNLOAD: Downloading outputs..."
mkdir -p out
kaggle kernels output $KERNEL_ID -p out/

# List downloaded files
echo "FILES: Downloaded files:"
ls -la out/

# Upload to Google Drive (optional)
if [ -f "credentials.json" ]; then
    echo "UPLOAD: Uploading to Google Drive..."
    python upload-to-drive.py
else
    echo "WARNING: Skipping Google Drive upload (no credentials.json found)"
fi

echo "SUCCESS: Workflow complete!"
'''
    
    with open(project_path / "run.sh", "w") as f:
        f.write(automation_script)
    os.chmod(project_path / "run.sh", 0o755)
    print(f"SUCCESS: Created run.sh automation script")
    
    # Create requirements.txt
    requirements = '''kaggle>=1.5.12
google-api-python-client>=2.0.0
google-auth-httplib2>=0.1.0
google-auth-oauthlib>=0.5.0
pandas>=1.3.0
numpy>=1.21.0
matplotlib>=3.4.0
seaborn>=0.11.0
'''
    
    with open(project_path / "requirements.txt", "w") as f:
        f.write(requirements)
    print(f"SUCCESS: Created requirements.txt")
    
    # Create .gitignore
    gitignore = '''# Kaggle API credentials
.kaggle/kaggle.json
kaggle.json

# Google Drive credentials
credentials.json
token.json

# Output files
out/
*.csv
*.pkl
*.h5
*.model

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
'''
    
    with open(project_path / ".gitignore", "w") as f:
        f.write(gitignore)
    print(f"SUCCESS: Created .gitignore")
    
    # Create setup instructions
    setup_md = f'''# {project_name} - Kaggle Automation

Automated workflow for running ML code on Kaggle's free GPU/TPU compute.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Kaggle API:**
   - Go to https://www.kaggle.com/account
   - Create new API token
   - Save as `.kaggle/kaggle.json`

3. **Configure Google Drive (optional):**
   - Go to Google Cloud Console
   - Download `credentials.json`
   - Place in project root

## Usage

1. **Edit your code:**
   ```bash
   vim script.py  # Add your ML code here
   ```

2. **Run the automation:**
   ```bash
   ./run.sh
   ```

3. **Check results:**
   ```bash
   ls out/  # Downloaded outputs from Kaggle
   ```

## Files

- `script.py` - Your main ML/data science code
- `kernel-metadata.json` - Kaggle kernel configuration  
- `run.sh` - Main automation script
- `upload-to-drive.py` - Google Drive sync
- `out/` - Downloaded results from Kaggle

## Security

Never commit API keys to git! They're in `.gitignore`.
'''
    
    with open(project_path / "README.md", "w") as f:
        f.write(setup_md)
    print(f"SUCCESS: Created README.md")
    
    return project_path

def main():
    parser = argparse.ArgumentParser(description='Initialize a new Kaggle automation project')
    parser.add_argument('project_name', help='Name of the project to create')
    parser.add_argument('--username', required=True, help='Your Kaggle username')
    
    args = parser.parse_args()
    
    print(f"INIT: Initializing Kaggle automation project: {args.project_name}")
    print(f"USER: Kaggle username: {args.username}")
    
    project_path = create_project_structure(args.project_name, args.username)
    
    print(f"\nSUCCESS: Project '{args.project_name}' created successfully!")
    print(f"LOCATION: {project_path.absolute()}")
    print(f"\nNEXT STEPS:")
    print(f"   cd {args.project_name}")
    print(f"   pip install -r requirements.txt")
    print(f"   # Add your Kaggle API key to .kaggle/kaggle.json")
    print(f"   # Edit script.py with your ML code")
    print(f"   ./run.sh")

if __name__ == "__main__":
    main()