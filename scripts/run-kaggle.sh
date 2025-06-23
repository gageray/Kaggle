#!/bin/bash
set -e

echo "UPLOAD: Pushing to Kaggle..."
kaggle kernels push

echo "WAITING: Waiting for execution..."
sleep 60  # Give it time to start

echo "DOWNLOAD: Downloading outputs..."
mkdir -p out
kaggle kernels output yourusername/my-cli-kernel -p out/

echo "UPLOAD: Uploading to Google Drive..."
python upload-to-drive.py

echo "Complete!"