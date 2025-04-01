import json
import os
from pathlib import Path
from datetime import datetime
import shutil
from PyQt6.QtCore import Qt

class Session:
    """Class representing a single session."""
    
    def __init__(self, name, host, username="", password="", group="", 
                 tags=None, description="", key_file="", params=""):
        """Initialize a session with connection details."""
        self.name = name
        self.host = host
        self.username = username
        self.password = password  # This will be encrypted
        self.group = group
        self.tags = tags or []
        self.description = description
        self.last_connection = None
        self.connection_count = 0
        self.key_file = key_file
        self.params = params
    
    def to_dict(self):
        """Convert session to dictionary for serialization."""
        return {
            "name": self.name,
            "host": self.host,
            "username": self.username,
            "password": self.password,  # Encryption should happen in the manager
            "group": self.group,
            "tags": self.tags,
            "description": self.description,
            "last_connection": self.last_connection,
            "connection_count": self.connection_count,
            "key_file": self.key_file,
            "params": self.params
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create session from dictionary."""
        session = cls(
            name=data["name"],
            host=data["host"],
            username=data.get("username", ""),
            password=data.get("password", ""),
            group=data.get("group", ""),
            tags=data.get("tags", []),
            description=data.get("description", ""),
            key_file=data.get("key_file", ""),
            params=data.get("params", "")
        )
        session.last_connection = data.get("last_connection")
        session.connection_count = data.get("connection_count", 0)
        return session


class SessionManager:
    """Manager for handling sessions, storage, and operations."""
    
    def __init__(self, config):
        """Initialize session manager with config."""
        self.config = config
        self.sessions = {}  # Dictionary of sessions by name
        
        # Use AppData for user-specific data
        app_data = Path.home() / 'AppData' / 'Local' / 'ASSHM'
        self.session_file = app_data / 'sessions.json'
        self.backup_dir = app_data / 'backups'
        self.max_backups = config.get("general", "max_backups", 5)
        
        # Ensure directories exist
        app_data.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing sessions
        self._load_sessions()
    
    def _load_sessions(self):
        """Load sessions from storage file."""
        if not self.session_file.exists():
            return
        
        try:
            with open(self.session_file, 'r') as f:
                data = json.load(f)
            
            for session_data in data:
                try:
                    session = Session.from_dict(session_data)
                    self.sessions[session.name] = session
                except Exception as session_error:
                    print(f"Error loading session {session_data.get('name', 'unknown')}: {str(session_error)}")
                    continue
                
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading sessions file: {e}")
    
    def save_sessions(self):
        """Save sessions to storage file with backup."""
        # Create backup first
        self._create_backup()
        
        # Convert sessions to list of dicts for serialization
        session_data = [session.to_dict() for session in self.sessions.values()]
        
        try:
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=4)
            return True
        except IOError as e:
            print(f"Error saving sessions: {e}")
            return False
    
    def _create_backup(self):
        """Create a backup of the current sessions file."""
        if not self.session_file.exists():
            return
        
        try:
            # Get max_backups from config
            max_backups = self.config.get("general", "max_backups", 5)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"sessions_backup_{timestamp}.json"
            
            # Ensure backup directory exists (in case it was deleted after initialization)
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy current sessions file to backup
            shutil.copy2(self.session_file, backup_file)
            
            # Manage maximum number of backups
            backup_files = sorted(self.backup_dir.glob("sessions_backup_*.json"))
            if len(backup_files) > max_backups:
                # Remove oldest backups
                for old_file in backup_files[:-max_backups]:
                    try:
                        old_file.unlink()
                    except PermissionError:
                        print(f"Warning: Could not delete old backup file: {old_file}")
                        continue
                
        except Exception as e:
            print(f"Warning: Failed to create backup: {e}")
            # Continue execution even if backup fails
            # The main sessions.json save operation will still proceed
    
    def add_session(self, session):
        """Add a new session."""
        # Ensure session has a valid name
        if not session.name.strip():
            raise ValueError("Session name cannot be empty")
        
        if session.name in self.sessions:
            raise ValueError(f"Session with name '{session.name}' already exists")
        
        self.sessions[session.name] = session
        self.save_sessions()
        return True
    
    def update_session(self, session):
        """Update an existing session."""
        # Ensure session has a valid name
        if not session.name.strip():
            raise ValueError("Session name cannot be empty")
        
        if session.name not in self.sessions:
            raise ValueError(f"Session with name '{session.name}' not found")
        
        self.sessions[session.name] = session
        self.save_sessions()
        return True
    
    def delete_session(self, session_name):
        """Delete a session by name."""
        if session_name not in self.sessions:
            raise ValueError(f"Session with name '{session_name}' not found")
        
        del self.sessions[session_name]
        self.save_sessions()
        return True
    
    def get_session(self, session_name):
        """Get a session by name."""
        return self.sessions.get(session_name)
    
    def get_all_sessions(self):
        """Get all sessions."""
        return list(self.sessions.values())
    
    def get_groups(self):
        """Get a list of all unique group names being used by sessions."""
        groups = set()
        for session in self.sessions.values():
            if session.group and session.group.strip():
                groups.add(session.group)
        return sorted(list(groups))
    
    def get_tags(self):
        """Get all unique tags."""
        all_tags = set()
        for session in self.sessions.values():
            all_tags.update(session.tags)
        return sorted(all_tags)
    
    def filter_sessions(self, group=None, tag=None, search_term=None):
        """Filter sessions by group, tag, or search term."""
        filtered = list(self.sessions.values())
        
        if group:
            filtered = [s for s in filtered if s.group == group]
            
        if tag:
            filtered = [s for s in filtered if tag in s.tags]
            
        if search_term and search_term.strip():
            search_term = search_term.lower().strip()
            filtered = [s for s in filtered if 
                       search_term in s.name.lower() or
                       search_term in s.host.lower() or
                       search_term in s.description.lower()]
            
        return filtered
    
    def update_connection_stats(self, session_name):
        """Update the connection statistics for a session."""
        if session_name in self.sessions:
            session = self.sessions[session_name]
            session.last_connection = datetime.now().isoformat()
            session.connection_count += 1
            self.save_sessions()

    def _on_connect_sftp(self):
        """Connect to the selected session via SFTP using WinSCP."""
        from PyQt6.QtWidgets import QMessageBox
        import subprocess
        import os
        
        # Get the selected session
        selected_items = self.session_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Connect SFTP", "Please select a session to connect to")
            return
        
        # Ensure it's a session, not a group
        selected_item = selected_items[0]
        if selected_item.parent() is None:
            QMessageBox.information(self, "Connect SFTP", "Please select a session, not a group")
            return
        
        session_name = selected_item.data(0, Qt.ItemDataRole.UserRole)
        session = self.session_manager.get_session(session_name)
        
        if not session:
            QMessageBox.warning(self, "Error", f"Session '{session_name}' not found")
            return
        
        # List of possible WinSCP locations in order of preference
        winscp_locations = [
            "C:\\Program Files\\WinSCP\\WinSCP.exe",
            "C:\\Program Files (x86)\\WinSCP\\WinSCP.exe",
            "C:\\Program Files\\WinSCP\\WinSCP.com",
            "C:\\Program Files (x86)\\WinSCP\\WinSCP.com"
        ]
        
        # Find WinSCP executable
        winscp_path = None
        for location in winscp_locations:
            if os.path.exists(location):
                winscp_path = location
                break
        
        if not winscp_path:
            QMessageBox.warning(
                self, 
                "WinSCP Not Found", 
                "WinSCP executable not found. Please install WinSCP or verify its installation path."
            )
            return
        
        try:
            # Directly construct the SFTP URL
            sftp_url = "sftp://"
            
            # Create a safe URL for logging (without password)
            safe_url = "sftp://"
            
            # Add username and password if available
            if session.username:
                sftp_url += session.username
                safe_url += session.username
                if session.password:
                    sftp_url += ":" + session.password
                    safe_url += ":********"  # Mask password in safe URL
                sftp_url += "@"
                safe_url += "@"
            
            # Add hostname
            sftp_url += session.host
            safe_url += session.host
            
            # Launch WinSCP with the SFTP URL
            print(f"Launching WinSCP with URL: {safe_url}")
            subprocess.Popen([winscp_path, sftp_url])
            
            # Update statistics
            self.session_manager.update_connection_stats(session_name)
            self.statusBar.showMessage(f"Launched WinSCP for session '{session.name}'")
            
        except Exception as e:
            QMessageBox.warning(self, "Connection Error", f"Failed to launch WinSCP: {str(e)}")
