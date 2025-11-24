# Simple ZOOM Panel for Enigma2

[![Python package](https://github.com/Belfagor2005/SimpleZooomPanel/actions/workflows/pylint.yml/badge.svg)](https://github.com/Belfagor2005/SimpleZooomPanel/actions/workflows/pylint.yml)
[![Visitors](https://komarev.com/ghpvc/?username=Belfagor2005&label=Visitors&color=blue)](https://github.com/Belfagor2005/SimpleZooomPanel)
![Python Version](https://img.shields.io/badge/Python-2.7%20%7C%203.x-blue.svg)
![Enigma2](https://img.shields.io/badge/Enigma2-Plugin-green.svg)

A comprehensive Enigma2 plugin that provides free server access, personal lines management, and various utilities in a user-friendly interface.

## 🌟 Features

### 🛠️ Tools Section
- **Free Cline Access** - Automated free server updates
- **FCA Script Update** - Keep your scripts up to date
- **Personal Lines Management** - Save and preserve your private lines

### 🎯 Extras Section
- **Addons Installation**
  - AJPanel
  - Levi45 Addon
  - LinuxsatPanel addons
- **Media Players**
  - ArchivCZSK
  - CSFD
- **Dependencies**
  - CURL, WGET, Python
  - CCCAM/OSCAM configuration files
- **CAM Support**
  - SoftCAM feed installation
  - "HomeMade" optimized configs

### ⚙️ Settings
- **Panel Updates** - Easy one-click updates
- **Automatic backup** of personal configurations

### ⏰ CronTimer
- **Automated script execution**
- **Scheduled updates**
- **Service management** (start/stop)

### ❓ Help & Support
- **Comprehensive FAQ**
- **Contact information**
- **Plugin information**

## 🔧 Personal Lines Management

The plugin includes advanced personal lines management:

### Automatic Preservation
- Personal lines are automatically saved and restored during updates
- Support for CCcam, OSCam, and NCam formats
- Prevents loss of private configurations

### File Locations
- **CCcam personal lines**: `/etc/cccamx.txt`
- **OSCam personal lines**: `/etc/oscamx.txt` 
- **NCam personal lines**: `/etc/ncamx.txt`
- **Backup directory**: `/usr/lib/enigma2/python/Plugins/Extensions/SimpleZOOMPanel/personal_lines/`

### Features
- ✅ Automatic backup before updates
- ✅ Smart restoration after updates
- ✅ Duplicate prevention
- ✅ Conversion between CAM formats
- ✅ Manual save/restore options

## 📦 Installation

### IPK Installation
1. Download the latest `.ipk` file from releases
2. Transfer to your Enigma2 receiver
3. Install via package manager or command line:
   ```bash
   opkg install simplezoom-panel_*.ipk
   ```

### Manual Installation
```bash
cd /tmp
wget https://github.com/Belfagor2005/SimpleZooomPanel/releases/latest/download/simplezoom-panel.ipk
opkg install simplezoom-panel.ipk
```

## 🚀 Usage

1. **Access the plugin** through your Enigma2 plugin menu
2. **Navigate** using left/right arrow keys or colored buttons
3. **Select options** with OK button
4. **Manage personal lines** through the Tools menu

### Quick Start with Personal Lines
1. Create your personal line files:
   ```bash
   echo "C: server.example.com 12000 user pass" > /etc/cccamx.txt
   ```
2. Use "Save Personal Lines" in Tools menu to backup them
3. Your lines will be automatically preserved during updates

## 🛡️ Backup & Restore

### Automatic Backup
The plugin automatically creates backups of:
- Personal C-lines and readers
- Configuration files
- Script settings

### Manual Backup
Use "Save Personal Lines" feature to manually backup your current configuration.

## 🔄 Update Process

1. **Pre-update**: Personal lines are automatically backed up
2. **Update**: New version is installed
3. **Post-update**: Personal lines are restored automatically
4. **Conversion**: Lines are converted to appropriate formats if needed

## 📋 Requirements

- **Enigma2** based receiver
- **Python** 2.7 or 3.x
- **Internet connection** for updates and features

## 🤝 Contributors

### Core Team
- **E2W!zard** - Project lead and main development
- **HIUMAN** - Co-developer and testing
- **BextrH** - Original CCcam free server downloader (ZOOM) concept

### Special Thanks
- **Lululla** - Python 3 adaptation and DreamOS support
- **Viliam** - Testing and feedback
- **Lvicek07** - Community support
- **Kakamus** - Technical assistance
- **Axy** - Feature suggestions

## 🌐 Community & Support

### Official Discussion
- **LinuxSat Support**: [Simple ZOOM Panel Thread](https://www.linuxsat-support.com/thread/157589-simple-zoom-panel/)

### Issue Reporting
Please report bugs and feature requests via:
1. Official forum thread
2. GitHub issues (if available)

## 📝 Version History

- **v1.0** - Initial release with basic features
- **v2.0** - Added personal lines management
- **Current** - Enhanced stability and Python 3 support

## 🔒 Privacy & Security

- Personal lines are stored locally on your device
- No data is transmitted to external servers
- All free servers are from publicly available sources

## 📄 License

This project is provided for educational and personal use. Please respect the terms of service of any services you access through this plugin.

## ⚠️ Disclaimer

This plugin is provided "as is" without any warranty. Users are responsible for complying with their local laws and service agreements. The developers are not responsible for any misuse or damages resulting from this software.

---

**Enjoy Simple ZOOM Panel!** 🎉

*Made with ❤️ for the Enigma2 community*
```
