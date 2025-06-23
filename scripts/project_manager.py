#!/usr/bin/env python3
"""
Project Configuration Manager
Handles individual project configs stored on Google Drive
"""

import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from string import Template

from config_loader import get_path, get_config

class ProjectManager:
    def __init__(self, drive_service):
        self.drive_service = drive_service
        self.template_path = get_path('paths.templates_dir') / 'project_config.yaml'
    
    def create_project_config(self, 
                            project_name: str,
                            kaggle_username: str,
                            project_description: str = "",
                            drive_folder_id: str = None) -> Dict[str, Any]:
        """Create a new project configuration from template"""
        
        # Load template
        with open(self.template_path, 'r') as f:
            template_content = f.read()
        
        # Generate values
        kernel_slug = project_name.lower().replace(' ', '-').replace('_', '-')
        created_date = datetime.now().isoformat()
        
        # Replace template variables
        template = Template(template_content)
        config_content = template.substitute(
            project_name=project_name,
            project_description=project_description or f"Machine learning project: {project_name}",
            created_date=created_date,
            kaggle_username=kaggle_username,
            kernel_slug=kernel_slug,
            drive_folder_id=drive_folder_id or "TBD"
        )
        
        # Parse as YAML
        project_config = yaml.safe_load(config_content)
        
        return project_config
    
    def save_project_config(self, project_config: Dict[str, Any], drive_folder_id: str) -> str:
        """Save project config to Google Drive"""
        
        # Convert config to YAML
        config_yaml = yaml.dump(project_config, default_flow_style=False, indent=2)
        
        # Create temp file
        temp_file = Path("/tmp/project_config.yaml")
        with open(temp_file, 'w') as f:
            f.write(config_yaml)
        
        # Upload to Drive
        file_metadata = {
            'name': 'project_config.yaml',
            'parents': [drive_folder_id]
        }
        
        from googleapiclient.http import MediaFileUpload
        media = MediaFileUpload(str(temp_file), mimetype='text/yaml')
        
        file = self.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        # Clean up temp file
        temp_file.unlink()
        
        return file['id']
    
    def load_project_config(self, drive_folder_id: str) -> Optional[Dict[str, Any]]:
        """Load project config from Google Drive folder"""
        
        # Search for project_config.yaml in the folder
        query = f"name='project_config.yaml' and '{drive_folder_id}' in parents"
        results = self.drive_service.files().list(q=query).execute()
        files = results.get('files', [])
        
        if not files:
            return None
        
        # Download the config file
        file_id = files[0]['id']
        
        from googleapiclient.http import MediaIoBaseDownload
        import io
        
        request = self.drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        # Parse YAML
        config_content = fh.getvalue().decode('utf-8')
        return yaml.safe_load(config_content)
    
    def update_project_config(self, drive_folder_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing project config"""
        
        # Load current config
        current_config = self.load_project_config(drive_folder_id)
        if not current_config:
            return False
        
        # Apply updates (deep merge)
        def deep_merge(base: dict, updates: dict):
            for key, value in updates.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(current_config, updates)
        
        # Save updated config
        self.save_project_config(current_config, drive_folder_id)
        return True
    
    def list_projects(self, root_folder_id: str) -> list:
        """List all projects (folders with project_config.yaml)"""
        
        # Get all folders in the Projects directory
        query = f"mimeType='application/vnd.google-apps.folder' and '{root_folder_id}' in parents"
        results = self.drive_service.files().list(q=query).execute()
        folders = results.get('files', [])
        
        projects = []
        for folder in folders:
            # Check if folder has a project config
            config = self.load_project_config(folder['id'])
            if config:
                projects.append({
                    'name': folder['name'],
                    'folder_id': folder['id'],
                    'config': config
                })
        
        return projects
    
    def create_project_structure(self, parent_folder_id: str, project_name: str) -> str:
        """Create project folder structure on Google Drive"""
        
        # Create main project folder
        project_metadata = {
            'name': project_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        
        project_folder = self.drive_service.files().create(body=project_metadata).execute()
        project_folder_id = project_folder['id']
        
        # Create subfolders based on template structure
        subfolders = ['code', 'data', 'outputs', 'docs', 'notebooks']
        
        for subfolder in subfolders:
            subfolder_metadata = {
                'name': subfolder,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [project_folder_id]
            }
            self.drive_service.files().create(body=subfolder_metadata).execute()
        
        return project_folder_id
    
    def validate_project_config(self, config: Dict[str, Any]) -> list:
        """Validate project configuration and return any errors"""
        errors = []
        
        # Required fields
        required_fields = [
            'project.name',
            'project.kaggle_username',
            'kaggle.kernel_id'
        ]
        
        for field in required_fields:
            keys = field.split('.')
            current = config
            for key in keys:
                if not isinstance(current, dict) or key not in current:
                    errors.append(f"Missing required field: {field}")
                    break
                current = current[key]
        
        # Validate kernel_id format
        kernel_id = config.get('kaggle', {}).get('kernel_id', '')
        if kernel_id and '/' not in kernel_id:
            errors.append("Invalid kernel_id format. Should be 'username/kernel-name'")
        
        return errors