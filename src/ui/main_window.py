from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QPushButton, QTreeWidget, QTreeWidgetItem, QLabel, QMenu, 
    QMessageBox, QDialog, QFileDialog, QTabWidget, QStatusBar,
    QApplication, QDialogButtonBox, QScrollArea
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction

from pathlib import Path
import json
import sys
import os

# Add src directory to the Python path to make imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now the imports should work
from core.session_manager import SessionManager, Session
from core.launcher import Launcher
from core.config_manager import ConfigManager
from core.ipam import IPAMManager
from core.ssh_key_converter import SSHKeyConverter

# Also use relative imports for UI modules
from ui.session_dialog import SessionDialog
from ui.preferences_dialog import PreferencesDialog
from ui.ipam_window import IPAMWidget, IPAMWindow

class MainWindow(QMainWindow):
    """Main application window for the session manager."""
    
    def __init__(self, config, session_manager, launcher, parent=None):
        """Initialize the main window with config."""
        super().__init__(parent)
        self.config = config
        self.session_manager = session_manager
        self.launcher = launcher
        
        # Set window properties
        self.setWindowTitle("ASSHM - Advanced SSH Manager")
        self.resize(1000, 700)
        
        # Initialize managers
        self._init_managers()
        
        # Create UI components
        self._create_menus()
        self._create_toolbar()
        self._create_central_widget()
        self._create_statusbar()
        
        # Populate session tree
        self._populate_session_tree()
    
    def _init_managers(self):
        """Initialize the various managers if not provided."""
        # Only create new instances if not provided in constructor
        if not hasattr(self, 'session_manager') or self.session_manager is None:
            self.session_manager = SessionManager(self.config)
        
        if not hasattr(self, 'launcher') or self.launcher is None:
            self.launcher = Launcher(self.config)
        
        if not hasattr(self, 'ipam_manager') or self.ipam_manager is None:
            self.ipam_manager = IPAMManager(self.config, self.session_manager)
    
    def _create_menus(self):
        """Create application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_session_action = file_menu.addAction("&New Session")
        new_session_action.triggered.connect(self._on_new_session)
        
        file_menu.addSeparator()
        
        import_action = file_menu.addAction("&Import Sessions...")
        import_action.triggered.connect(self._on_import)
        
        export_action = file_menu.addAction("&Export Sessions...")
        export_action.triggered.connect(self._on_export)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("E&xit")
        exit_action.triggered.connect(self.close)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        edit_action = edit_menu.addAction("&Edit Session")
        edit_action.triggered.connect(self._on_edit_session)
        
        delete_action = edit_menu.addAction("&Delete Session")
        delete_action.triggered.connect(self._on_delete_session)
        
        edit_menu.addSeparator()
        
        preferences_action = edit_menu.addAction("&Preferences")
        preferences_action.triggered.connect(self._on_preferences)
        
        # Help menu (renamed from About)
        help_menu = menubar.addMenu("&Help")
        about_action = help_menu.addAction("&About ASSHM")
        about_action.triggered.connect(self._on_about_asshm)
        
        help_info_action = help_menu.addAction("&Help && Information")
        help_info_action.triggered.connect(self._on_show_help_info)
        
        license_action = help_menu.addAction("&License")
        license_action.triggered.connect(self._on_show_license)
    
    def _create_toolbar(self):
        """Create the main toolbar."""
        self.toolbar = self.addToolBar("Main Toolbar")
        self.toolbar.setIconSize(QSize(24, 24))
        
        # New Session
        new_action = QAction("New Session", self)
        new_action.triggered.connect(self._on_new_session)
        self.toolbar.addAction(new_action)
        
        # Edit Session
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(self._on_edit_session)
        self.toolbar.addAction(edit_action)
        
        # Delete Session
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self._on_delete_session)
        self.toolbar.addAction(delete_action)
        
        # Separator
        self.toolbar.addSeparator()
        
        # Connection buttons will be moved to the session details tab
        
        # Separator
        self.toolbar.addSeparator()
        
        # Preferences
        prefs_action = QAction("Preferences", self)
        prefs_action.triggered.connect(self._on_preferences)
        self.toolbar.addAction(prefs_action)
        
        # Show the toolbar based on config
        self.toolbar.setVisible(self.config.get("ui", "show_toolbar", True))
    
    def _create_central_widget(self):
        """Create the central widget containing session list."""
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # Create splitter for session tree and tabs
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self.main_splitter)
        
        # Create session tree widget (left side)
        self._create_session_tree()
        
        # Create tab widget (right side)
        self._create_tab_widget()
        
        # Set initial splitter sizes (30% for tree, 70% for tabs)
        self.main_splitter.setSizes([300, 700])
        
        self.setCentralWidget(central_widget)
        
        # Connect signals
        self.session_tree.currentItemChanged.connect(self._on_session_selected)
    
    def _create_statusbar(self):
        """Create the status bar."""
        self.statusBar = QStatusBar()
        self.statusBar.showMessage("Ready")
        self.setStatusBar(self.statusBar)
    
    def _populate_session_tree(self):
        """Populate the session tree with sessions."""
        # Clear the existing items
        self.session_tree.clear()
        
        # Get all sessions from manager
        sessions = self.session_manager.get_all_sessions()
        
        # Group sessions by their group property
        grouped_sessions = {}
        for session in sessions:
            group = session.group if session.group else "Ungrouped"
            if group not in grouped_sessions:
                grouped_sessions[group] = []
            grouped_sessions[group].append(session)
        
        # Add sessions to tree
        for group_name, group_sessions in grouped_sessions.items():
            group_item = QTreeWidgetItem(self.session_tree, [group_name])
            for session in group_sessions:
                session_item = QTreeWidgetItem(group_item, [session.name])
                session_item.setData(0, Qt.ItemDataRole.UserRole, session.name)
    
    def _on_new_session(self):
        """Handle new session button click."""
        dialog = SessionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            session_data = dialog.get_session_data()
            try:
                # Create a new Session object
                session = Session(
                    name=session_data["name"],
                    host=session_data["host"],
                    username=session_data["username"],
                    password=session_data["password"],
                    group=session_data["group"],
                    tags=session_data["tags"],
                    description=session_data["description"],
                    key_file=session_data["key_file"],
                    params=session_data["params"]
                )
                
                # Add the session
                self.session_manager.add_session(session)
                
                # Add to IPAM if it's a valid IP
                if hasattr(self, 'ipam_tab'):
                    self.ipam_tab.add_session_to_ipam(session)
                
                # Refresh session tree
                self._populate_session_tree()
                
                # Select the new session
                self._select_session_by_name(session.name)
                
                # Update status bar
                self.statusBar.showMessage(f"Created new session: {session.name}")
                
            except ValueError as e:
                QMessageBox.warning(self, "Error", f"Failed to create session: {str(e)}")
    
    def _on_import(self):
        """Import sessions from a JSON file."""
        # Get file path from user
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Sessions",
            str(Path.home()),
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return  # User canceled
        
        try:
            # Read file
            with open(file_path, 'r') as f:
                session_data = json.load(f)
            
            if not session_data:
                QMessageBox.information(self, "Import Sessions", "No sessions found in the file.")
                return
            
            # Check for existing sessions with same names
            existing_sessions = set()
            for data in session_data:
                if data.get("name") in self.session_manager.sessions:
                    existing_sessions.add(data.get("name"))
            
            # Ask about overwriting if there are duplicates
            overwrite_existing = False
            if existing_sessions:
                reply = QMessageBox.question(
                    self,
                    "Import Sessions",
                    f"Found {len(existing_sessions)} sessions with names that already exist. "
                    f"Do you want to overwrite them?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                overwrite_existing = reply == QMessageBox.StandardButton.Yes
            
            # Import sessions
            imported = 0
            skipped = 0
            for data in session_data:
                name = data.get("name")
                
                # Skip if exists and not overwriting
                if name in self.session_manager.sessions and not overwrite_existing:
                    skipped += 1
                    continue
                
                # Create new session
                session = Session(
                    name=name,
                    host=data.get("host", ""),
                    username=data.get("username", ""),
                    password=data.get("password", ""),
                    group=data.get("group", "")
                )
                
                # Remove existing session if we're overwriting
                if name in self.session_manager.sessions and overwrite_existing:
                    self.session_manager.delete_session(name)
                
                # Add to session manager (without using overwrite parameter)
                self.session_manager.add_session(session)
                imported += 1
            
            # Save changes
            self.session_manager.save_sessions()
            
            # Refresh tree
            self._populate_session_tree()
            
            QMessageBox.information(
                self,
                "Import Complete",
                f"Successfully imported {imported} sessions.\n"
                f"Skipped {skipped} sessions."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import sessions: {str(e)}"
            )
    
    def _on_export(self):
        """Export sessions to a JSON file with password masking option."""
        if not self.session_manager or not self.session_manager.sessions:
            QMessageBox.information(self, "Export Sessions", "No sessions to export.")
            return
        
        # Ask about password security
        reply = QMessageBox.question(
            self,
            "Export Security",
            "Do you want to mask passwords in the export file for security?\n\n"
            "Note: Masked passwords will need to be re-entered when imported.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        mask_passwords = reply == QMessageBox.StandardButton.Yes
        
        # Get file path from user
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Sessions",
            str(Path.home() / "asshm_sessions.json"),
            "JSON Files (*.json)"
        )
        
        if not file_path:
            return  # User canceled
        
        # Ensure the file has .json extension
        if not file_path.lower().endswith('.json'):
            file_path += '.json'
        
        try:
            # Get all sessions as dictionaries
            session_data = []
            for session in self.session_manager.sessions.values():
                session_dict = session.to_dict()
                
                # Mask password if requested
                if mask_passwords and session_dict.get("password"):
                    session_dict["password"] = "********"  # Masked password
                
                session_data.append(session_dict)
            
            # Write to file
            with open(file_path, 'w') as f:
                json.dump(session_data, f, indent=4)
            
            security_note = " (with masked passwords)" if mask_passwords else ""
            QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported {len(session_data)} sessions{security_note} to {file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export sessions: {str(e)}"
            )
    
    def _on_edit_session(self):
        """Edit the selected session."""
        selected_items = self.session_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Edit Session", "No session selected.")
            return
        
        item = selected_items[0]
        if item.parent() is None and item.childCount() > 0:
            # This is a group, not a session
            QMessageBox.information(self, "Edit Session", "Please select a session to edit.")
            return
        
        # Get session
        session_name = item.text(0)
        session = self.session_manager.get_session(session_name)
        
        if not session:
            QMessageBox.critical(self, "Error", "Session not found.")
            return
        
        # Remember the original host
        old_host = session.host
        
        # Show edit dialog
        dialog = SessionDialog(parent=self, session=session)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get updated data
            session_data = dialog.get_session_data()
            
            try:
                # Create a new Session object with the updated data
                updated_session = Session(
                    name=session_data["name"],
                    host=session_data["host"],
                    username=session_data["username"],
                    password=session_data["password"],
                    group=session_data["group"],
                    tags=session_data["tags"],
                    description=session_data["description"],
                    key_file=session_data["key_file"],
                    params=session_data["params"]
                )
                
                # Copy over connection statistics from the old session
                if hasattr(session, 'last_connection'):
                    updated_session.last_connection = session.last_connection
                if hasattr(session, 'connection_count'):
                    updated_session.connection_count = session.connection_count
                
                # Delete the old session first
                self.session_manager.delete_session(session_name)
                
                # Now add the updated session
                self.session_manager.add_session(updated_session)
                
                # CRITICAL: Explicitly save sessions to disk
                self.session_manager.save_sessions()
                
                # Update the host in IPAM if needed
                if hasattr(self, 'ipam_tab'):
                    self.ipam_tab.update_session_in_ipam(updated_session, old_host)
                
                # Repopulate the tree
                self._populate_session_tree()
                
                # Find and select the edited session (name may have changed)
                self._select_session_by_name(updated_session.name)
                
                # Update status bar - Fix: use showMessage method on statusBar object
                self.statusBar.showMessage(f"Updated session: {updated_session.name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update session: {str(e)}")
    
    def _on_delete_session(self):
        """Delete the selected session."""
        selected_items = self.session_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Delete Session", "Please select a session to delete")
            return
        
        # Ensure it's a session, not a group
        selected_item = selected_items[0]
        if selected_item.parent() is None:
            QMessageBox.information(self, "Delete Session", "Please select a session, not a group")
            return
        
        session_name = selected_item.data(0, Qt.ItemDataRole.UserRole)
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the session '{session_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Use delete_session instead of any other method name
                self.session_manager.delete_session(session_name)
                self._populate_session_tree()
                # Use self.statusBar (the object) instead of self.statusBar() (trying to call it as a method)
                self.statusBar.showMessage(f"Session '{session_name}' deleted")
                
            except ValueError as e:
                QMessageBox.warning(self, "Error", f"Failed to delete session: {str(e)}")
    
    def _on_preferences(self):
        """Open preferences dialog."""
        dialog = PreferencesDialog(self.config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get the settings from dialog
            settings = dialog.get_settings()
            
            # Update config
            for section, values in settings.items():
                for key, value in values.items():
                    self.config.set(section, key, value)
            
            # Save config
            self.config.save()
            
            # Apply UI settings
            
            # Toolbar and statusbar visibility (already working)
            self.toolbar.setVisible(self.config.get("ui", "show_toolbar", True))
            self.statusBar.setVisible(self.config.get("ui", "show_statusbar", True))
            
            # Apply font size
            font_size = self.config.get("ui", "font_size", 10)
            self._apply_font_size(font_size)
            
            # Update launcher paths
            if self.launcher:
                self.launcher.putty_path = self.config.get("general", "putty_path", "")
                self.launcher.winscp_path = self.config.get("general", "winscp_path", "")
                
            self.statusBar.showMessage("Preferences updated")
    
    def _apply_font_size(self, size):
        """Apply font size to the application."""
        font = self.font()
        font.setPointSize(size)
        QApplication.setFont(font)
        
        # Update the tree widget font
        tree_font = self.session_tree.font()
        tree_font.setPointSize(size)
        self.session_tree.setFont(tree_font)
        
        # Update the info label font
        info_font = self.session_info_label.font()
        info_font.setPointSize(size)
        self.session_info_label.setFont(info_font)
    
    def _on_launch_putty(self):
        """Connect to the selected session via SSH."""
        # Get the selected session
        selected_items = self.session_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Connect", "Please select a session to connect to")
            return
            
        # Ensure it's a session, not a group
        selected_item = selected_items[0]
        if selected_item.parent() is None:
            QMessageBox.information(self, "Connect", "Please select a session, not a group")
            return
            
        session_name = selected_item.data(0, Qt.ItemDataRole.UserRole)
        session = self.session_manager.get_session(session_name)
        
        if not session:
            QMessageBox.warning(self, "Error", f"Session '{session_name}' not found")
            return
            
        try:
            # Update connection statistics
            self.session_manager.update_connection_stats(session_name)
            
            # Launch PuTTY with this session
            self.launcher.launch_putty(session)
            
            self.statusBar.showMessage(f"Connected to '{session.name}'")
        except Exception as e:
            QMessageBox.warning(self, "Connection Error", f"Failed to connect: {str(e)}")
    
    def _on_launch_winscp(self):
        """Launch WinSCP directly without connection parameters."""
        from PyQt6.QtWidgets import QMessageBox
        import subprocess
        import os
        
        # List of possible WinSCP locations in order of preference
        winscp_locations = [
            "C:\\Program Files\\WinSCP\\WinSCP.exe",
            "C:\\Program Files (x86)\\WinSCP\\WinSCP.exe"
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
            # Launch WinSCP without parameters
            print(f"Launching standalone WinSCP: {winscp_path}")
            subprocess.Popen([winscp_path])
            
        except Exception as e:
            QMessageBox.warning(self, "Launch Error", f"Failed to launch WinSCP: {str(e)}")
    
    def _on_about_asshm(self):
        """Show about ASSHM dialog."""
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About ASSHM")
        about_dialog.setMinimumWidth(500)
        about_dialog.setMinimumHeight(300)
        
        layout = QVBoxLayout(about_dialog)
        
        # Get the actual AppData path
        app_data_path = Path.home() / 'AppData' / 'Local' / 'ASSHM'
        
        about_text = QLabel(
            "<div align='center'>"
            "<h2>ASSHM</h2>"
            "<p>Advanced SSH Manager</p>"
            "<p>A tool for managing SSH/SFTP/RDP connections.</p>"
            "<p><a href='https://github.com/McDevStudios/asshm'>https://github.com/McDevStudios/asshm</a></p>"
            "<p>Version 1.0.0</p>"
            "</div>"
        )
        about_text.setOpenExternalLinks(True)
        about_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_text.setTextFormat(Qt.TextFormat.RichText)
        about_text.setWordWrap(True)
        layout.addWidget(about_text)
        
        # Add OK button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(about_dialog.accept)
        layout.addWidget(button_box)
        
        about_dialog.exec()
    
    def _on_show_license(self):
        """Show license dialog."""
        license_dialog = QDialog(self)
        license_dialog.setWindowTitle("License")
        license_dialog.setMinimumWidth(500)
        license_dialog.setMinimumHeight(400)
        
        layout = QVBoxLayout(license_dialog)
        
        license_text = QLabel(
            "<div align='center'><h3>MIT License</h3></div>"
            "<p>Copyright (c) 2025 McDevStudios</p>"
            "<p>Permission is hereby granted, free of charge, to any person obtaining a copy "
            "of this software and associated documentation files (the \"Software\"), to deal "
            "in the Software without restriction, including without limitation the rights "
            "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell "
            "copies of the Software, and to permit persons to whom the Software is "
            "furnished to do so, subject to the following conditions:</p>"
            "<p>The above copyright notice and this permission notice shall be included in all "
            "copies or substantial portions of the Software.</p>"
            "<p>THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR "
            "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, "
            "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE "
            "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER "
            "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, "
            "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE "
            "SOFTWARE.</p>"
        )
        license_text.setWordWrap(True)
        license_text.setAlignment(Qt.AlignmentFlag.AlignJustify)
        
        # Add text to scrollable area
        scroll = QScrollArea()
        scroll.setWidget(license_text)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Add OK button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(license_dialog.accept)
        layout.addWidget(button_box)
        
        license_dialog.exec()
    
    def _on_connect_ssh(self):
        """Connect to the selected session via SSH (port 22)."""
        from PyQt6.QtWidgets import QMessageBox
        
        # Get the selected session
        selected_items = self.session_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Connect SSH", "Please select a session to connect to")
            return
        
        # Ensure it's a session, not a group
        selected_item = selected_items[0]
        if selected_item.parent() is None:
            QMessageBox.information(self, "Connect SSH", "Please select a session, not a group")
            return
        
        session_name = selected_item.data(0, Qt.ItemDataRole.UserRole)
        session = self.session_manager.get_session(session_name)
        
        if not session:
            QMessageBox.warning(self, "Error", f"Session '{session_name}' not found")
            return
        
        try:
            # Use the launcher to connect (which now handles SSH key conversion with user feedback)
            self.statusBar.showMessage(f"Connecting to '{session.name}' via SSH...")
            
            # Launch PuTTY with this session
            process = self.launcher.launch_putty(session)
            
            # If process is None, it means the user canceled
            if process is None:
                self.statusBar.showMessage("Connection canceled")
                return
                
            # Update connection statistics
            self.session_manager.update_connection_stats(session_name)
            
            # Update status message
            self.statusBar.showMessage(f"Connected to '{session.name}' via SSH")
            
        except Exception as e:
            QMessageBox.warning(self, "Connection Error", f"Failed to connect: {str(e)}")
            self.statusBar.showMessage(f"Connection failed: {str(e)}")
    
    def _on_connect_rdp(self):
        """Connect to the selected session via RDP (port 3389)."""
        from PyQt6.QtWidgets import QMessageBox
        import subprocess
        import os
        
        # Get the selected session
        selected_items = self.session_tree.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Connect RDP", "Please select a session to connect to")
            return
        
        # Ensure it's a session, not a group
        selected_item = selected_items[0]
        if selected_item.parent() is None:
            QMessageBox.information(self, "Connect RDP", "Please select a session, not a group")
            return
        
        session_name = selected_item.data(0, Qt.ItemDataRole.UserRole)
        session = self.session_manager.get_session(session_name)
        
        if not session:
            QMessageBox.warning(self, "Error", f"Session '{session_name}' not found")
            return
        
        try:
            # Hard-code RDP port
            rdp_port = 3389
            
            # Use Windows' built-in Remote Desktop client (mstsc.exe)
            rdp_client = "mstsc.exe"
            
            # Create temporary .rdp file with connection settings
            import tempfile
            
            # Create a temporary file with .rdp extension
            fd, rdp_file_path = tempfile.mkstemp(suffix='.rdp')
            os.close(fd)
            
            # Write RDP configuration
            with open(rdp_file_path, 'w') as rdp_file:
                rdp_file.write(f"full address:s:{session.host}:{rdp_port}\n")
                
                # Add username if provided
                if session.username:
                    rdp_file.write(f"username:s:{session.username}\n")
                
                # Optional settings for better experience
                rdp_file.write("screen mode id:i:1\n")  # 1 = windowed, 2 = full screen
                rdp_file.write("desktopwidth:i:1366\n")
                rdp_file.write("desktopheight:i:768\n")
                rdp_file.write("session bpp:i:32\n")  # color depth
                rdp_file.write("use multimon:i:0\n")
                rdp_file.write("audiomode:i:0\n")  # 0 = play locally
                rdp_file.write("connection type:i:7\n")  # 7 = auto detect connection
                rdp_file.write("networkautodetect:i:1\n")
                rdp_file.write("bandwidthautodetect:i:1\n")
                
                # Handle credentials
                if session.password:
                    # If password is saved, we can configure auto-login
                    rdp_file.write("prompt for credentials:i:0\n")
                    # Note: We can't directly store the password in the RDP file for security reasons
                    # Instead, we use Windows credential manager
                else:
                    rdp_file.write("prompt for credentials:i:1\n")
                
                # Add extra RDP settings for better experience
                rdp_file.write("alternate shell:s:\n")
                rdp_file.write("shell working directory:s:\n")
                rdp_file.write("disable wallpaper:i:1\n")
                rdp_file.write("disable full window drag:i:1\n")
                rdp_file.write("disable menu anims:i:1\n")
                rdp_file.write("disable themes:i:0\n")
                rdp_file.write("disable cursor setting:i:0\n")
                rdp_file.write("authentication level:i:2\n")
            
            # Launch RDP client with the configuration file
            subprocess.Popen([rdp_client, rdp_file_path])
            
            # Schedule the temp file for deletion when Windows closes
            # Note: we can't delete immediately as mstsc.exe needs to read it
            subprocess.Popen(f'ping 127.0.0.1 -n 5 > nul && del "{rdp_file_path}"', shell=True)
            
            # Update connection statistics
            self.session_manager.update_connection_stats(session_name)
            self.statusBar.showMessage(f"Launched RDP connection to '{session.name}'")
            
        except Exception as e:
            QMessageBox.warning(self, "Connection Error", f"Failed to launch RDP connection: {str(e)}")
    
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
            "C:\\Program Files (x86)\\WinSCP\\WinSCP.exe"
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
            # Build the SFTP URL
            sftp_url = "sftp://"
            
            # Add username if available
            if session.username:
                sftp_url += session.username
                # Only add password if no key file is configured
                if session.password and not (hasattr(session, 'key_file') and session.key_file):
                    sftp_url += ":" + session.password
                sftp_url += "@"
            
            # Add hostname
            sftp_url += session.host
            
            # Build command
            cmd = [winscp_path, sftp_url]
            
            # Add SSH key if specified
            if hasattr(session, 'key_file') and session.key_file:
                key_file_path = session.key_file
                if os.path.exists(key_file_path):
                    # WinSCP can use OpenSSH keys directly, no conversion needed
                    cmd.append(f"/privatekey={key_file_path}")
                else:
                    QMessageBox.warning(
                        self,
                        "Key File Warning",
                        f"The SSH key file '{key_file_path}' does not exist. Continuing without it."
                    )
            
            # Add any additional parameters from session
            if hasattr(session, 'params') and session.params:
                for param in session.params.split():
                    cmd.append(param)
            
            # Mask password for display
            masked_url = sftp_url
            if session.password:
                masked_url = sftp_url.replace(session.password, '********')
            print(f"Launching WinSCP with URL: {masked_url}")
            
            # Launch WinSCP
            subprocess.Popen(cmd)
            
            # Update statistics
            self.session_manager.update_connection_stats(session_name)
            self.statusBar.showMessage(f"Launched WinSCP for session '{session.name}'")
            
        except Exception as e:
            QMessageBox.warning(self, "Connection Error", f"Failed to launch WinSCP: {str(e)}")

    def _on_session_selected(self, current, previous):
        """Update the info panel when a session is selected."""
        if current and current.parent():  # Check if it's a session (has a parent)
            session_name = current.data(0, Qt.ItemDataRole.UserRole)
            session = self.session_manager.get_session(session_name)
            
            if session:
                # Create an info text with session details - without port & protocol references
                info_text = (
                    f"<b>Name:</b> {session.name}<br>"
                    f"<b>Host:</b> {session.host}<br>"
                    f"<b>Username:</b> {session.username}<br>"
                )
                
                # Add password status - NEW!
                if session.password:
                    info_text += "<b>Password:</b> [Saved]<br>"
                
                # Show key file if available
                if hasattr(session, 'key_file') and session.key_file:
                    info_text += f"<b>SSH Key:</b> {session.key_file}<br>"
                
                # Show additional parameters if available
                if hasattr(session, 'params') and session.params:
                    info_text += f"<b>Additional Parameters:</b> {session.params}<br>"
                
                if session.group:
                    info_text += f"<b>Group:</b> {session.group}<br>"
                    
                if session.tags:
                    info_text += f"<b>Tags:</b> {', '.join(session.tags)}<br>"
                    
                if session.description:
                    info_text += f"<b>Description:</b> {session.description}<br>"
                    
                if session.last_connection:
                    info_text += f"<b>Last connected:</b> {session.last_connection}<br>"
                    info_text += f"<b>Connection count:</b> {session.connection_count}<br>"
                
                self.session_info_label.setText(info_text)
                
                # Enable connection buttons
                self.connect_ssh_btn.setEnabled(True)
                self.connect_rdp_btn.setEnabled(True)
                self.connect_sftp_btn.setEnabled(True)
            else:
                self.session_info_label.setText("Session not found in manager")
                # Disable connection buttons
                self.connect_ssh_btn.setEnabled(False)
                self.connect_rdp_btn.setEnabled(False)
                self.connect_sftp_btn.setEnabled(False)
        else:
            self.session_info_label.setText("No session selected")
            # Disable connection buttons
            self.connect_ssh_btn.setEnabled(False)
            self.connect_rdp_btn.setEnabled(False)
            self.connect_sftp_btn.setEnabled(False)

    def _on_open_ipam(self):
        """Open the standalone IPAM window."""
        self.ipam_window = IPAMWindow(self.ipam_manager, self)
        self.ipam_window.show()

    def _create_session_tree(self):
        """Create the session tree widget."""
        # Create widget
        session_widget = QWidget()
        session_layout = QVBoxLayout(session_widget)
        session_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create session tree
        self.session_tree = QTreeWidget()
        self.session_tree.setHeaderLabel("Sessions")
        self.session_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.session_tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        self.session_tree.itemClicked.connect(self._on_session_selected)
        session_layout.addWidget(self.session_tree)
        
        # Add to splitter
        self.main_splitter.addWidget(session_widget)
    
    def _create_tab_widget(self):
        """Create the tab widget for different views."""
        # Create tab container
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        tab_layout.addWidget(self.tab_widget)
        
        # Create Session Details tab
        self.session_tab = self._create_session_tab()
        self.tab_widget.addTab(self.session_tab, "Session Details")
        
        # Create IPAM tab using the reusable widget
        self.ipam_tab = IPAMWidget(self.ipam_manager, self)
        self.ipam_tab.session_selected.connect(self._select_session_by_name)
        self.tab_widget.addTab(self.ipam_tab, "IP Management")
        
        # Add to splitter
        self.main_splitter.addWidget(tab_container)
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
    
    def _create_session_tab(self):
        """Create the session details tab content."""
        session_tab = QWidget()
        layout = QVBoxLayout(session_tab)
        
        # Session info
        self.session_info_label = QLabel("No session selected")
        self.session_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.session_info_label.setWordWrap(True)
        self.session_info_label.setStyleSheet("padding: 20px;")
        layout.addWidget(self.session_info_label)
        
        # Connection buttons
        buttons_layout = QHBoxLayout()
        
        self.connect_ssh_btn = QPushButton("Connect SSH")
        self.connect_ssh_btn.clicked.connect(self._on_connect_ssh)
        self.connect_ssh_btn.setEnabled(False)
        buttons_layout.addWidget(self.connect_ssh_btn)
        
        self.connect_rdp_btn = QPushButton("Connect RDP")
        self.connect_rdp_btn.clicked.connect(self._on_connect_rdp)
        self.connect_rdp_btn.setEnabled(False)
        buttons_layout.addWidget(self.connect_rdp_btn)
        
        self.connect_sftp_btn = QPushButton("Connect SFTP")
        self.connect_sftp_btn.clicked.connect(self._on_connect_sftp)
        self.connect_sftp_btn.setEnabled(False)
        buttons_layout.addWidget(self.connect_sftp_btn)
        
        layout.addLayout(buttons_layout)
        
        # Add stretcher to push everything to the top
        layout.addStretch()
        
        return session_tab
    
    def _on_tab_changed(self, index):
        """Handle tab selection changes."""
        if index == 1:  # IPAM tab
            # Get currently selected session
            selected_items = self.session_tree.selectedItems()
            if selected_items:
                item = selected_items[0]
                if item.parent() is not None:  # It's a session, not a group
                    session_name = item.text(0)
                    self.ipam_tab.select_session(session_name)
    
    def _select_session_by_name(self, session_name):
        """Find and select a session by name in the tree."""
        if not session_name:
            return
            
        # Switch to the Session Details tab
        self.tab_widget.setCurrentIndex(0)
        
        # Find and select the session
        self._find_and_select_session(session_name)
    
    def _find_and_select_session(self, session_name):
        """Find and select a session item in the tree."""
        # Iterate through all items to find the session
        for i in range(self.session_tree.topLevelItemCount()):
            top_item = self.session_tree.topLevelItem(i)
            
            # Check if this is a group with children
            if top_item.childCount() > 0:
                # Check all children
                for j in range(top_item.childCount()):
                    child = top_item.child(j)
                    if child.text(0) == session_name:
                        # Found it
                        self.session_tree.setCurrentItem(child)
                        return True
            elif top_item.text(0) == session_name:
                # Found it at top level
                self.session_tree.setCurrentItem(top_item)
                return True
        
        return False
    
    def _on_tree_context_menu(self, position):
        """Handle context menu for session tree."""
        # Get the item at the position
        item = self.session_tree.itemAt(position)
        if not item:
            return
        
        # Select the item that was right-clicked
        self.session_tree.setCurrentItem(item)
        
        # Create the context menu
        menu = QMenu(self)
        
        if item.parent() is None:
            # This is a group
            group_name = item.text(0)
            
            # Add actions for groups
            rename_action = menu.addAction("Rename Group")
            delete_group_action = menu.addAction("Delete Group and Sessions")
            menu.addSeparator()
            expand_action = menu.addAction("Expand All")
            collapse_action = menu.addAction("Collapse All")
            
            # Group-level actions
            action = menu.exec(self.session_tree.viewport().mapToGlobal(position))
            
            if action == rename_action:
                self._rename_group(item)
            elif action == delete_group_action:
                self._delete_group(item)
            elif action == expand_action:
                item.setExpanded(True)
                for i in range(item.childCount()):
                    item.child(i).setExpanded(True)
            elif action == collapse_action:
                item.setExpanded(False)
        else:
            # This is a session
            session_name = item.text(0)
            session = self.session_manager.get_session(session_name)
            
            if session:
                # Add actions for sessions
                edit_action = menu.addAction("Edit Session")
                delete_action = menu.addAction("Delete Session")
                menu.addSeparator()
                
                # Add connection options submenu
                connect_menu = menu.addMenu("Connect via")
                connect_ssh_action = connect_menu.addAction("SSH")
                connect_rdp_action = connect_menu.addAction("RDP")
                connect_sftp_action = connect_menu.addAction("SFTP")
                
                # Execute the menu and handle action
                action = menu.exec(self.session_tree.viewport().mapToGlobal(position))
                
                if action == edit_action:
                    self._on_edit_session()
                elif action == delete_action:
                    self._on_delete_session()
                elif action == connect_ssh_action:
                    self._on_connect_ssh()
                elif action == connect_rdp_action:
                    self._on_connect_rdp()
                elif action == connect_sftp_action:
                    self._on_connect_sftp()

    def _rename_group(self, group_item):
        """Rename a session group."""
        from PyQt6.QtWidgets import QInputDialog
        
        # Get the current group name
        old_name = group_item.text(0)
        
        # Show input dialog to get new name
        new_name, ok = QInputDialog.getText(
            self, 
            "Rename Group", 
            "Enter new group name:", 
            text=old_name
        )
        
        if ok and new_name.strip() and new_name != old_name:
            # Update the group name in the tree
            group_item.setText(0, new_name)
            
            # Update all sessions in this group
            for i in range(group_item.childCount()):
                child = group_item.child(i)
                session_name = child.text(0)
                session = self.session_manager.get_session(session_name)
                
                if session:
                    # Remember the original host (for IPAM)
                    old_host = session.host
                    
                    # Update session's group name
                    session.group = new_name
                    
                    # Update in session manager
                    try:
                        self.session_manager.update_session(session)
                    except:
                        # If update_session isn't working correctly, use delete/add approach
                        try:
                            self.session_manager.delete_session(session_name)
                            self.session_manager.add_session(session)
                        except Exception as e:
                            from PyQt6.QtWidgets import QMessageBox
                            QMessageBox.warning(self, "Error", f"Failed to update session: {str(e)}")
                            continue
                    
                    # Update IPAM if needed
                    if hasattr(self, 'ipam_tab'):
                        self.ipam_tab.update_session_in_ipam(session, old_host)
            
            # Save changes
            self.session_manager.save_sessions()
            
            # Show confirmation
            self.statusBar.showMessage(f"Group renamed to '{new_name}'")

    def _delete_group(self, group_item):
        """Delete a group and all its sessions."""
        group_name = group_item.text(0)
        
        # Count sessions in group
        session_count = group_item.childCount()
        
        # Confirm deletion
        reply = QMessageBox.warning(
            self,
            "Delete Group",
            f"Are you sure you want to delete the group '{group_name}' and all its {session_count} sessions?\n\n"
            "This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Delete all sessions in the group
                sessions_to_delete = []
                for i in range(group_item.childCount()):
                    session_item = group_item.child(i)
                    session_name = session_item.text(0)
                    sessions_to_delete.append(session_name)
                
                # Delete sessions from manager
                for session_name in sessions_to_delete:
                    self.session_manager.delete_session(session_name)
                
                # Remove group item from tree
                index = self.session_tree.indexOfTopLevelItem(group_item)
                self.session_tree.takeTopLevelItem(index)
                
                # Save changes
                self.session_manager.save_sessions()
                
                # Update status
                self.statusBar.showMessage(
                    f"Deleted group '{group_name}' and {session_count} sessions"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete group: {str(e)}"
                )

    def _on_show_help_info(self):
        """Show help and information dialog."""
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("Help & Information")
        help_dialog.setMinimumWidth(600)
        help_dialog.setMinimumHeight(400)
        
        layout = QVBoxLayout(help_dialog)
        
        # Get the actual AppData path using the current user's home directory
        app_data_path = str(Path.home() / 'AppData' / 'Local' / 'ASSHM')
        
        help_text = QLabel(
            "<div>"
            "<h2>Help & Information</h2>"
            
            "<h3>Data Storage</h3>"
            "<p>ASSHM stores your data in your personal AppData folder:</p>"
            f"<p><code>{app_data_path}</code></p>"
            "<ul>"
            "<li><b>sessions.json</b> - Your session configurations are stored in this file</li>"
            "<li><b>backups/</b> - Automatic backups of your sessions are stored in this folder</li>"
            "</ul>"
            
            "<h3>Connection Types</h3>"
            "<ul>"
            "<li><b>SSH</b> - Secure Shell connection using PuTTY</li>"
            "<li><b>SFTP</b> - Secure File Transfer using WinSCP</li>"
            "<li><b>RDP</b> - Remote Desktop Connection</li>"
            "</ul>"
            
            "<h3>Security Tips</h3>"
            "<ul>"
            "<li>Use SSH keys instead of passwords when possible</li>"
            "<li>Regular backups are automatically created in your AppData folder</li>"
            "<li>Session data is stored locally on your computer</li>"
            "</ul>"
            
            "<h3>Getting Started</h3>"
            "<ol>"
            "<li>Click 'New Session' to create your first connection</li>"
            "<li>Fill in the required connection details</li>"
            "<li>Use the connection buttons to connect via SSH, SFTP, or RDP</li>"
            "</ol>"
            "</div>"
        )
        
        help_text.setOpenExternalLinks(True)
        help_text.setTextFormat(Qt.TextFormat.RichText)
        help_text.setWordWrap(True)
        
        # Add scrollbar for content
        scroll = QScrollArea()
        scroll.setWidget(help_text)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Add OK button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(help_dialog.accept)
        layout.addWidget(button_box)
        
        help_dialog.exec()
