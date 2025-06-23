#!/usr/bin/env python3
"""
Configuration loader for Kaggle CLI Tools
Loads all settings from project.yaml
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, List

class ConfigLoader:
    def __init__(self, config_file: str = "./config/project.yaml"):
        self.config_file = Path(config_file)
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        
        with open(self.config_file, 'r') as f:
            return yaml.safe_load(f)
    
    def get(self, key_path: str, default=None):
        """Get config value using dot notation (e.g., 'paths.config_dir')"""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_path(self, key_path: str) -> Path:
        """Get a path from config and return as Path object"""
        path_str = self.get(key_path)
        if path_str is None:
            raise ValueError(f"Path not found in config: {key_path}")
        return Path(path_str)
    
    def get_credentials_path(self, service: str) -> Path:
        """Get credentials path for a specific service"""
        if service == 'kaggle':
            return self.get_path('paths.kaggle_credentials')
        elif service == 'drive':
            return self.get_path('paths.drive_credentials')
        else:
            raise ValueError(f"Unknown service: {service}")
    
    def get_drive_folders(self) -> Dict[str, str]:
        """Get Google Drive folder structure"""
        root = self.get('google_drive.folder_structure.root')
        subfolders = self.get('google_drive.folder_structure.subfolders', [])
        
        folders = {root: None}
        for subfolder in subfolders:
            folders[f"{root}/{subfolder}"] = None
        
        return folders
    
    def get_sensitive_patterns(self) -> List[str]:
        """Get list of sensitive file patterns"""
        files = self.get('security.sensitive_files', [])
        dirs = self.get('security.sensitive_dirs', [])
        return files + dirs
    
    def get_dependencies(self) -> List[str]:
        """Get list of Python dependencies"""
        return self.get('dependencies.python_packages', [])
    
    def get_kernel_defaults(self) -> Dict[str, Any]:
        """Get default kernel settings"""
        return self.get('kaggle.kernel_defaults', {})
    
    def get_polling_settings(self) -> Dict[str, int]:
        """Get Kaggle polling settings"""
        return self.get('kaggle.polling', {})
    
    def get_cli_commands(self) -> Dict[str, str]:
        """Get CLI commands and descriptions"""
        return self.get('cli.commands', {})
    
    def get_output_settings(self) -> Dict[str, Any]:
        """Get output formatting settings"""
        return self.get('cli.output', {})
    
    def validate_config(self) -> bool:
        """Validate that all required config sections exist"""
        required_sections = [
            'project',
            'paths',
            'google_drive',
            'kaggle',
            'cli'
        ]
        
        for section in required_sections:
            if section not in self.config:
                print(f"❌ Missing required config section: {section}")
                return False
        
        return True
    
    def ensure_directories(self):
        """Create directories specified in config"""
        dirs_to_create = [
            'paths.config_dir',
            'paths.scripts_dir', 
            'paths.templates_dir',
            'paths.temp_dir'
        ]
        
        for dir_path in dirs_to_create:
            path = self.get_path(dir_path)
            path.mkdir(parents=True, exist_ok=True)
    
    def check_credentials(self) -> Dict[str, bool]:
        """Check if credential files exist"""
        kaggle_exists = self.get_credentials_path('kaggle').exists()
        drive_exists = self.get_credentials_path('drive').exists()
        
        return {
            'kaggle': kaggle_exists,
            'drive': drive_exists
        }

# Global config instance
config = ConfigLoader()

# Convenience functions
def get_config(key_path: str, default=None):
    """Get config value using dot notation"""
    return config.get(key_path, default)

def get_path(key_path: str) -> Path:
    """Get path from config"""
    return config.get_path(key_path)

def get_credentials_path(service: str) -> Path:
    """Get credentials path for service"""
    return config.get_credentials_path(service)