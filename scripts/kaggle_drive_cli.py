#!/usr/bin/env python3
"""
Advanced Kaggle + Google Drive CLI Management Tool
Automates syncing, metadata tracking, and workflow management
"""

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

from config_loader import config, get_config, get_path, get_credentials_path

class KaggleDriveCLI:
    def __init__(self):
        # Load all paths from config
        self.config_dir = get_path('paths.config_dir')
        self.config_dir.mkdir(exist_ok=True)
        
        self.metadata_file = get_path('paths.metadata_file')
        self.drive_config = get_path('paths.drive_config_file')
        
        # Get settings from config
        self.scopes = get_config('google_drive.scopes')
        self.output_settings = config.get_output_settings()
        self.polling_settings = config.get_polling_settings()
        
        self.metadata = self.load_metadata()
        self.drive_service = None
        
    def load_metadata(self) -> Dict[str, Any]:
        """Load metadata tracking file"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {
            "kaggle_kernels": {},
            "drive_files": {},
            "sync_history": [],
            "last_sync": None
        }
    
    def save_metadata(self):
        """Save metadata to file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)
    
    def authenticate_drive(self) -> Optional[Any]:
        """Authenticate with Google Drive"""
        creds = None
        token_file = get_path('paths.drive_token')
        credentials_file = get_credentials_path('drive')
        
        if token_file.exists():
            creds = Credentials.from_authorized_user_file(str(token_file), self.scopes)
        
        if not creds or not creds.valid:
            if not credentials_file.exists():
                print(f"❌ ERROR: {credentials_file.name} not found in {credentials_file.parent}/")
                print("📥 Download from: https://console.cloud.google.com/apis/credentials")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_file), self.scopes)
            creds = flow.run_local_server(port=0)
            
            with open(token_file, 'w') as f:
                f.write(creds.to_json())
        
        self.drive_service = build('drive', 'v3', credentials=creds)
        return self.drive_service
    
    def setup_drive_structure(self):
        """Create organized Google Drive folder structure"""
        if not self.drive_service:
            if not self.authenticate_drive():
                return False
        
        # Get folder structure from config
        folders = config.get_drive_folders()
        
        print("🗂️  Setting up Google Drive folder structure...")
        
        for folder_path in folders.keys():
            folder_id = self.create_drive_folder(folder_path)
            folders[folder_path] = folder_id
            print(f"✅ Created: {folder_path}")
        
        # Save folder IDs to config
        drive_config = {
            "folder_structure": folders,
            "created_at": datetime.now().isoformat()
        }
        
        with open(self.drive_config, 'w') as f:
            json.dump(drive_config, f, indent=2)
        
        print("✅ Drive structure setup complete!")
        return True
    
    def create_drive_folder(self, folder_path: str) -> str:
        """Create folder in Google Drive with full path"""
        parts = folder_path.split('/')
        parent_id = None
        
        for part in parts:
            # Check if folder exists
            query = f"name='{part}' and mimeType='application/vnd.google-apps.folder'"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            else:
                query += " and 'root' in parents"
            
            results = self.drive_service.files().list(q=query).execute()
            items = results.get('files', [])
            
            if items:
                parent_id = items[0]['id']
            else:
                # Create folder
                folder_metadata = {
                    'name': part,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                if parent_id:
                    folder_metadata['parents'] = [parent_id]
                
                folder = self.drive_service.files().create(body=folder_metadata).execute()
                parent_id = folder['id']
        
        return parent_id
    
    def list_kaggle_kernels(self) -> List[Dict]:
        """List all Kaggle kernels"""
        try:
            result = subprocess.run(['kaggle', 'kernels', 'list', '--mine'], 
                                  capture_output=True, text=True, check=True)
            
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            kernels = []
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 4:
                        kernels.append({
                            'name': parts[0],
                            'title': ' '.join(parts[1:-2]),
                            'language': parts[-2],
                            'type': parts[-1]
                        })
            
            return kernels
        except subprocess.CalledProcessError as e:
            print(f"❌ Error listing Kaggle kernels: {e}")
            return []
    
    def sync_kernel_to_drive(self, kernel_name: str, project_folder: str = None):
        """Sync specific Kaggle kernel outputs to Google Drive"""
        if not self.drive_service:
            if not self.authenticate_drive():
                return False
        
        print(f"📤 Syncing kernel: {kernel_name}")
        
        # Download kernel outputs
        output_dir = Path(f"temp_outputs/{kernel_name}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            subprocess.run(['kaggle', 'kernels', 'output', kernel_name, 
                          '-p', str(output_dir)], check=True)
            
            # Upload to Drive
            if not project_folder:
                project_folder = self.get_drive_folder_id("Kaggle-CLI/Outputs")
            
            uploaded_files = []
            for file_path in output_dir.rglob('*'):
                if file_path.is_file():
                    file_id = self.upload_to_drive(str(file_path), project_folder)
                    if file_id:
                        uploaded_files.append({
                            'name': file_path.name,
                            'id': file_id,
                            'uploaded_at': datetime.now().isoformat()
                        })
            
            # Update metadata
            self.metadata['kaggle_kernels'][kernel_name] = {
                'last_sync': datetime.now().isoformat(),
                'files': uploaded_files,
                'drive_folder': project_folder
            }
            
            self.metadata['sync_history'].append({
                'type': 'kernel_sync',
                'kernel': kernel_name,
                'files_count': len(uploaded_files),
                'timestamp': datetime.now().isoformat()
            })
            
            self.save_metadata()
            
            print(f"✅ Synced {len(uploaded_files)} files from {kernel_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error syncing kernel {kernel_name}: {e}")
            return False
    
    def upload_to_drive(self, file_path: str, parent_folder_id: str) -> Optional[str]:
        """Upload file to Google Drive"""
        try:
            file_metadata = {
                'name': os.path.basename(file_path),
                'parents': [parent_folder_id]
            }
            
            media = MediaFileUpload(file_path, resumable=True)
            file = self.drive_service.files().create(
                body=file_metadata, media_body=media, fields='id'
            ).execute()
            
            return file['id']
        except Exception as e:
            print(f"❌ Error uploading {file_path}: {e}")
            return None
    
    def download_from_drive(self, file_id: str, destination: str):
        """Download file from Google Drive"""
        try:
            request = self.drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            with open(destination, 'wb') as f:
                f.write(fh.getvalue())
            
            return True
        except Exception as e:
            print(f"❌ Error downloading file: {e}")
            return False
    
    def get_drive_folder_id(self, folder_path: str) -> Optional[str]:
        """Get Google Drive folder ID from path"""
        if self.drive_config.exists():
            with open(self.drive_config, 'r') as f:
                config = json.load(f)
                return config.get('folder_structure', {}).get(folder_path)
        return None
    
    def status(self):
        """Show current status of Kaggle kernels and Drive sync"""
        print("📊 KAGGLE + DRIVE STATUS")
        print("=" * 50)
        
        # Kaggle kernels
        kernels = self.list_kaggle_kernels()
        print(f"🔬 Kaggle Kernels: {len(kernels)}")
        for kernel in kernels[:5]:  # Show first 5
            print(f"   • {kernel['name']} ({kernel['language']})")
        
        if len(kernels) > 5:
            print(f"   ... and {len(kernels) - 5} more")
        
        # Drive sync status
        synced_kernels = len(self.metadata['kaggle_kernels'])
        print(f"☁️  Synced to Drive: {synced_kernels} kernels")
        
        if self.metadata['last_sync']:
            print(f"🕐 Last Sync: {self.metadata['last_sync']}")
        
        # Recent sync history
        recent_syncs = self.metadata['sync_history'][-3:]
        if recent_syncs:
            print("\n📋 Recent Activity:")
            for sync in recent_syncs:
                print(f"   • {sync['type']}: {sync.get('kernel', 'N/A')} ({sync['timestamp'][:16]})")

def main():
    parser = argparse.ArgumentParser(description='Kaggle + Google Drive CLI Manager')
    parser.add_argument('command', choices=[
        'setup', 'status', 'sync', 'list', 'upload', 'download',
        'create-project', 'list-projects', 'project-status'
    ], help='Command to run')
    
    parser.add_argument('--kernel', help='Kernel name for sync operations')
    parser.add_argument('--file', help='File path for upload/download')
    parser.add_argument('--destination', help='Destination path for downloads')
    parser.add_argument('--project', help='Project name for project operations')
    parser.add_argument('--username', help='Kaggle username for new projects')
    parser.add_argument('--description', help='Project description')
    
    args = parser.parse_args()
    
    cli = KaggleDriveCLI()
    
    if args.command == 'setup':
        print("🚀 Setting up Kaggle + Drive CLI...")
        if cli.setup_drive_structure():
            print("✅ Setup complete!")
        else:
            print("❌ Setup failed!")
            sys.exit(1)
    
    elif args.command == 'status':
        cli.status()
    
    elif args.command == 'sync':
        if not args.kernel:
            print("❌ --kernel required for sync command")
            sys.exit(1)
        cli.sync_kernel_to_drive(args.kernel)
    
    elif args.command == 'list':
        kernels = cli.list_kaggle_kernels()
        print(f"📋 Found {len(kernels)} Kaggle kernels:")
        for kernel in kernels:
            print(f"   • {kernel['name']} - {kernel['title']}")
    
    elif args.command == 'create-project':
        if not args.project or not args.username:
            print("❌ --project and --username required for create-project")
            sys.exit(1)
        
        if not cli.drive_service:
            if not cli.authenticate_drive():
                sys.exit(1)
        
        from project_manager import ProjectManager
        pm = ProjectManager(cli.drive_service)
        
        # Get Projects folder ID
        projects_folder_id = cli.get_drive_folder_id("Kaggle-CLI/Projects")
        if not projects_folder_id:
            print("❌ Projects folder not found. Run 'kdcli setup' first.")
            sys.exit(1)
        
        print(f"📁 Creating project: {args.project}")
        
        # Create project folder structure
        project_folder_id = pm.create_project_structure(projects_folder_id, args.project)
        
        # Create project config
        project_config = pm.create_project_config(
            args.project, 
            args.username,
            args.description or "",
            project_folder_id
        )
        
        # Save config to Drive
        config_file_id = pm.save_project_config(project_config, project_folder_id)
        
        print(f"✅ Project created successfully!")
        print(f"   Folder ID: {project_folder_id}")
        print(f"   Config ID: {config_file_id}")
    
    elif args.command == 'list-projects':
        if not cli.drive_service:
            if not cli.authenticate_drive():
                sys.exit(1)
        
        from project_manager import ProjectManager
        pm = ProjectManager(cli.drive_service)
        
        projects_folder_id = cli.get_drive_folder_id("Kaggle-CLI/Projects")
        if not projects_folder_id:
            print("❌ Projects folder not found. Run 'kdcli setup' first.")
            sys.exit(1)
        
        projects = pm.list_projects(projects_folder_id)
        print(f"📂 Found {len(projects)} projects:")
        for project in projects:
            config = project['config']
            status = config.get('project', {}).get('status', 'unknown')
            print(f"   • {project['name']} ({status})")
    
    elif args.command == 'project-status':
        if not args.project:
            print("❌ --project required for project-status")
            sys.exit(1)
        
        print(f"📊 Project status for: {args.project}")
        print("   (Project status implementation needed)")
    
    else:
        print(f"❌ Command '{args.command}' not implemented yet")

if __name__ == "__main__":
    main()