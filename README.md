# Kaggle + Google Drive CLI Tools

Advanced CLI automation for Kaggle kernels with Google Drive integration, metadata tracking, and workflow management.

## 🚀 Quick Start

```bash
./setup.sh
kdcli status
```

## 📁 Project Structure

```
CLI Tools/
├── src/                    # Main source code
│   ├── kaggle_drive_cli.py # Advanced CLI tool
│   └── init.py            # Project generator
├── scripts/               # Automation scripts
│   └── run-kaggle.sh     # Basic automation
├── templates/            # Project templates
│   ├── script.py         # Kaggle kernel template
│   ├── upload-to-drive.py # Drive upload template
│   └── kernel-metadata.json # Kernel config template
├── config/               # Configuration files (created on setup)
│   ├── metadata.json     # Sync tracking
│   ├── drive_config.json # Drive folder structure
│   └── credentials.json  # Google API credentials (you provide)
└── setup.sh             # One-time setup script
```

## 🔧 Features

### CLI Commands
- `kdcli setup` - Initialize Google Drive folder structure
- `kdcli status` - Show Kaggle kernels and sync status
- `kdcli list` - List all your Kaggle kernels
- `kdcli sync --kernel <name>` - Sync kernel outputs to Drive

### Google Drive Structure
```
Kaggle-CLI/
├── Projects/    # Active project files
├── Datasets/    # Input datasets
├── Outputs/     # Kernel results
└── Archives/    # Completed projects
```

### Metadata Tracking
- Tracks all kernel syncs
- Maintains file relationships
- Sync history and timestamps
- Drive folder mappings

## 📋 Setup Requirements

1. **Kaggle API**: `~/.kaggle/kaggle.json`
2. **Google Drive API**: `config/credentials.json`
3. **Python packages**: Installed via `setup.sh`

## 🎯 Usage Examples

```bash
# Initial setup
./setup.sh

# Check status
kdcli status

# List your kernels
kdcli list

# Sync specific kernel to Drive
kdcli sync --kernel username/my-kernel

# Generate new project
python3 src/init.py "My ML Project" --username your-kaggle-username
```

## 🔐 Security

- All API credentials are gitignored
- OAuth tokens stored in `config/`
- Never commit sensitive files

## 🛠️ Development

The CLI tool is modular and extensible:
- `KaggleDriveCLI` class handles all operations
- JSON-based metadata tracking
- Google Drive API integration
- Subprocess calls to Kaggle CLI