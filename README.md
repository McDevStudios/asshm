# ASSHM (Advanced SSH Manager)
ASSHM is a powerful session manager that streamlines PuTTY and WinSCP connections with integrated IP Address Management. It enables IT professionals to efficiently organize and access remote connections with minimal effort.

Developed in Python 3 and optimized for Windows, ASSHM is easily adaptable to Linux with minor modifications. The application combines an intuitive interface with a lightweight footprint for maximum efficiency.

## Table of Contents
- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Setup and Deployment](#setup-and-deployment)
- [Usage](#usage)
- [Development](#development)
- [License](#license)

## Overview
This Python-based desktop application allows users to:
1. **Manage Sessions**: Organize and launch SSH/SFTP/RDP sessions efficiently
2. **Track IP Addresses**: Integrated IPAM system for IP address management
3. **Secure Connections**: Support for both password and key-based authentication
4. **Transfer Files**: Integration with WinSCP for file transfers

## Tech Stack
- **Frontend**: PyQt6 for modern GUI
- **Storage**: JSON-based configuration and session storage
- **Integration**: PuTTY and WinSCP
- **Security**: Built-in SSH key management
- **Packaging**: PyInstaller for executable creation and Inno Setup for installer packaging

## Features

### 1. Session Management
- Comprehensive session organization with:
  - Group-based session organization
  - Tag support
  - Password and SSH key management
  - Connection history tracking
  - Bulk import/export capabilities

### 2. IPAM Integration
- Built-in IP Address Management including:
  - Subnet tracking and organization
  - IP address status monitoring
  - Session-to-IP mapping

### 3. Tool Integration
- Seamless integration with:
  - PuTTY for SSH connections
  - WinSCP for file transfers
  - MSTSC for RDP sessions
  - Credential passing support

### 4. Automation Support
- Easy bulk session import through AppData:
  - Sessions are stored in your AppData folder: `C:\Users\<YourUsername>\AppData\Local\ASSHM\sessions.json`
  - Simply paste your session configurations into sessions.json
  - Application automatically loads sessions on startup
  - Perfect for quickly adding multiple network devices

Example sessions.json (paste this into your AppData ASSHM folder):
```json
[
    {
        "name": "web-server",
        "host": "192.168.1.10",
        "username": "webadmin",
        "password": "",
        "group": "Web Servers",
        "tags": ["apache", "production"],
        "description": "Production Web Server",
        "key_file": "C:/ssh_keys/web.ppk",
        "params": ""
    },
    {
        "name": "database",
        "host": "192.168.1.11",
        "username": "dbadmin",
        "password": "",
        "group": "Databases",
        "tags": ["mysql"],
        "description": "Main Database Server",
        "key_file": "C:/ssh_keys/db.ppk",
        "params": ""
    }
]
```

Note: Always use SSH keys instead of passwords when possible for better security. The SSH key file must be .PPK as per PuTTY and WinSCP demands. 

## Setup and Deployment

### Prerequisites
- Python 3.10 or higher
- PuTTY installed
- WinSCP installed
- Inno Setup 6.4.2 or higher (for building installer, this is for the dev more than the user). 

### Installation
1. Go to releases and download the .exe, then run the .exe. This should work in an offline or air-gapped enviroment, as the .exe packages installers for PuTTY and WinSCP. 

OR 

1. Clone the repository:
   ```bash
   git clone https://github.com/McDevStudios/asshm.git
   cd asshm
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python src/main.py
   ```

### Building Installer
More for me as the dev, but feel free to use this also to create your own .exes
1. Build using the batch script:
   ```bash
   build_offline.bat
   ```
   This will:
   - Use PyInstaller to create the executable
   - Use Inno Setup to package the installer

## Usage
1. Launch the application
2. Add new sessions manually or import sessions via sessions.json
3. Organize sessions into groups and add tags
4. Use the IPAM feature to manage IP addresses
5. Launch SSH connections or file transfers with a single click

## Development
Project structure:
- `.venv/`: for venv...
- `Installers/`: Not pushed to github but contains: 
  - `innosetup-6.4.2.exe/`: for .exe creation. 
  - `putty-arm64-0.79-installer.msi/`: PuTTY installer. 
  - `python-3.13.2-amd64.exe/`: Python installer.
  - `WinSCP-6.3.7-Setup.exe/`: WinSCP installer.
- `src/`: Application source code
  - `ui/`: PyQt6 interface components
  - `core/`: Core functionality and managers
  - `assets/`: Application icons and resources
- Root level files for configuration and building such as build_offline.bat, requirments.txt, etc. 

## License
This project is licensed under the MIT License. See the LICENSE file for details.

**Third-Party Licenses:**
- PyQt6 - GPL v3 License
- PyInstaller - GPL v2 License
- Inno Setup - No-cost license
- PuTTY - MIT License
- WinSCP - GPL v3 License