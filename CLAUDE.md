# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup and Development Commands

```bash
# Initial setup (installs dependencies, creates global kdcli command)
./setup.sh

# Run the main CLI tool
python3 scripts/kaggle_drive_cli.py <command>
# OR (after setup)
kdcli <command>

# Generate new Kaggle project
python3 scripts/init.py "Project Name" --username your-kaggle-username

# Basic Kaggle automation
./scripts/run-kaggle.sh
```

## Architecture Overview

This is a Kaggle + Google Drive automation CLI with two main components:

### 1. Main CLI Tool (`scripts/kaggle_drive_cli.py`)
- **KaggleDriveCLI Class**: Central orchestrator for all operations
- **Metadata System**: JSON-based tracking in `config/metadata.json` stores sync history, kernel mappings, and Drive file relationships
- **Drive Integration**: Creates structured folder hierarchy (`Kaggle-CLI/{Projects,Datasets,Outputs,Archives}`) and manages OAuth flow
- **Kaggle API**: Uses subprocess calls to kaggle CLI for kernel operations

Commands:
- `setup`: Initialize Google Drive folder structure
- `status`: Show kernel sync status and recent activity  
- `list`: List user's Kaggle kernels
- `sync --kernel <name>`: Download kernel outputs and upload to Drive

### 2. Project Generator (`scripts/init.py`)
- Creates new Kaggle automation projects with complete structure
- Generates kernel-metadata.json, automation scripts, and templates
- Sets up project-specific configurations

## Configuration and Authentication

**API Keys Location**: 
- Kaggle: `config/kaggle.json` (project-local) OR `~/.kaggle/kaggle.json` (global)
- Google Drive: `config/client_secret_*.json` (OAuth credentials file)
- Generated tokens stored in `config/token.json`

**Important**: Never delete files matching `*key*.json` or `*secret*.json` - these contain irreplaceable API credentials.

**Metadata Tracking**: 
- `config/metadata.json`: Tracks all sync operations, file mappings, and history
- `config/drive_config.json`: Stores Google Drive folder structure and IDs

## Templates System

The `templates/` directory contains reusable components:
- `script.py`: Kaggle kernel template with ML/data science structure
- `upload-to-drive.py`: Standalone Drive upload script  
- `kernel-metadata.json`: Kaggle kernel configuration template

## Critical Notes

- The CLI tool expects to find API credentials in the `config/` directory
- All credential files are gitignored for security
- The setup script creates a global `kdcli` symlink to `scripts/kaggle_drive_cli.py`
- Drive folder structure is automatically created and managed via Google Drive API
- Kaggle operations use subprocess calls to the official kaggle CLI tool