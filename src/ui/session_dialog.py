from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                           QLineEdit, QComboBox, QSpinBox, QTextEdit,
                           QPushButton, QLabel, QDialogButtonBox, QCheckBox,
                           QGroupBox, QFileDialog, QMessageBox, QApplication)
from PyQt6.QtCore import Qt
from pathlib import Path

class SessionDialog(QDialog):
    """Dialog for creating or editing a session."""
    
    def __init__(self, parent=None, session=None):
        """Initialize dialog with optional existing session for editing."""
        super().__init__(parent)
        self.session = session
        self.parent_window = parent
        
        # Get config from parent if available
        self.config = None
        if hasattr(parent, 'config'):
            self.config = parent.config
        
        self.setWindowTitle("ASSHM - Session Properties")
        self.resize(500, 400)
        
        # Set dialog icon (inherit from application if possible)
        if QApplication.instance().windowIcon():
            self.setWindowIcon(QApplication.instance().windowIcon())
        
        self._create_ui()
        
        # Populate group dropdown with existing groups
        self._populate_group_dropdown()
        
        # If editing an existing session, populate fields
        if session:
            self._populate_form()
    
    def _create_ui(self):
        """Create the dialog UI components."""
        layout = QVBoxLayout(self)
        
        # Create form for session details
        form_group = QGroupBox("Session Details")
        form_layout = QFormLayout(form_group)
        
        # Session name
        self.name_edit = QLineEdit()
        form_layout.addRow("Session Name:", self.name_edit)
        
        # Host information
        self.host_edit = QLineEdit()
        form_layout.addRow("Host:", self.host_edit)
        
        # Username
        self.username_edit = QLineEdit()
        form_layout.addRow("Username:", self.username_edit)
        
        # Password
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_edit)
        
        # Group for categorization
        self.group_combo = QComboBox()
        self.group_combo.setEditable(True)
        form_layout.addRow("Group:", self.group_combo)
        
        # Tags (comma-separated)
        self.tags_edit = QLineEdit()
        form_layout.addRow("Tags (comma-separated):", self.tags_edit)
        
        # Description
        self.description_edit = QTextEdit()
        form_layout.addRow("Description:", self.description_edit)
        
        layout.addWidget(form_group)
        
        # Advanced options group
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QFormLayout(advanced_group)
        
        # SSH key file path
        self.key_file_edit = QLineEdit()
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self._browse_key_file)
        key_layout = QHBoxLayout()
        key_layout.addWidget(self.key_file_edit)
        key_layout.addWidget(browse_button)
        advanced_layout.addRow("SSH Key File:", key_layout)
        
        layout.addWidget(advanced_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(self._test_connection)
        button_box.addButton(test_button, QDialogButtonBox.ButtonRole.ActionRole)
        
        layout.addWidget(button_box)
    
    def _browse_key_file(self):
        """Open a file dialog to select an SSH key file."""
        from PyQt6.QtWidgets import QMessageBox
        import subprocess
        import os

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select SSH Key File",
            str(Path.home()),
            "All Files (*.*);;PEM Files (*.pem);;PPK Files (*.ppk)"
        )
        
        if file_path:
            # Check if the file is a PPK file
            if not file_path.lower().endswith('.ppk'):
                # It's not a PPK file, warn the user
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setWindowTitle("Non-PPK Key File")
                msg.setText("PuTTY requires keys in PPK format.")
                msg.setInformativeText(f"The selected file '{file_path}' is not a PPK file. "
                                      "You need to convert it first using PuTTYgen.")
                msg.setDetailedText("PuTTY can only use keys in its own PPK format. "
                                   "If you have an OpenSSH or other format key, you need to "
                                   "convert it using the PuTTYgen tool first.")
                
                # Add custom buttons - REMOVED "Use Anyway" option
                convert_button = msg.addButton("Launch PuTTYgen", QMessageBox.ButtonRole.ActionRole)
                cancel_button = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                
                msg.exec()
                
                clicked_button = msg.clickedButton()
                
                if clicked_button == convert_button:
                    # Find PuTTYgen and launch it
                    puttygen_paths = [
                        "C:\\Program Files\\PuTTY\\puttygen.exe",
                        "C:\\Program Files (x86)\\PuTTY\\puttygen.exe"
                    ]
                    
                    puttygen_path = None
                    for path in puttygen_paths:
                        if os.path.exists(path):
                            puttygen_path = path
                            break
                    
                    if puttygen_path:
                        # Launch PuTTYgen and load the key file
                        try:
                            subprocess.Popen([puttygen_path, file_path])
                            
                            # Show additional instructions
                            instructions = QMessageBox()
                            instructions.setIcon(QMessageBox.Icon.Information)
                            instructions.setWindowTitle("PuTTYgen Instructions")
                            instructions.setText("PuTTYgen has been launched with your key file.")
                            instructions.setInformativeText(
                                "1. Click 'Save private key' in PuTTYgen\n"
                                "2. Save the file with a .ppk extension\n"
                                "3. Then return here and browse for the new PPK file"
                            )
                            instructions.exec()
                            
                            # Don't set the non-PPK file in the dialog
                            return
                        except Exception as e:
                            QMessageBox.critical(
                                self, 
                                "Error", 
                                f"Failed to launch PuTTYgen: {str(e)}"
                            )
                    else:
                        QMessageBox.warning(
                            self,
                            "PuTTYgen Not Found",
                            "PuTTYgen was not found on your system. Please install PuTTY "
                            "or manually convert your key using PuTTYgen."
                        )
                else:  # cancel_button was clicked or dialog was dismissed
                    # User cancelled, don't set the file
                    return
            
            # Set the key file path in the dialog (only if it's a PPK or user chose to use it anyway)
            self.key_file_edit.setText(file_path)
    
    def _populate_form(self):
        """Populate form with session data when editing."""
        if not self.session:
            return
            
        # Basic session info
        self.name_edit.setText(self.session.name)
        self.host_edit.setText(self.session.host)
        self.username_edit.setText(self.session.username)
        self.password_edit.setText(self.session.password)  # Simply show the password if it exists
        
        # Group
        if self.session.group:
            group_index = self.group_combo.findText(self.session.group)
            if group_index >= 0:
                self.group_combo.setCurrentIndex(group_index)
            else:
                self.group_combo.setEditText(self.session.group)
        
        # Tags
        if self.session.tags:
            self.tags_edit.setText(", ".join(self.session.tags))
        
        # Description
        if self.session.description:
            self.description_edit.setText(self.session.description)
        
        # SSH Key
        if self.session.key_file:
            self.key_file_edit.setText(self.session.key_file)
    
    def get_session_data(self):
        """Get session data from form fields."""
        return {
            "name": self.name_edit.text().strip(),
            "host": self.host_edit.text().strip(),
            "username": self.username_edit.text().strip(),
            "password": self.password_edit.text(),  # Whatever is in the field is what gets saved
            "group": self.group_combo.currentText().strip(),
            "tags": [tag.strip() for tag in self.tags_edit.text().split(",")] if self.tags_edit.text().strip() else [],
            "description": self.description_edit.toPlainText().strip(),
            "key_file": self.key_file_edit.text().strip(),
            "params": ""  # Add this line to include empty params by default
        }
    
    def _test_connection(self):
        """Test connection to the server on common ports."""
        from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
        from PyQt6.QtCore import QTimer, Qt
        import socket
        import threading
        
        # Get the current data from form
        session_data = self.get_session_data()
        
        # Basic validation
        if not session_data["host"]:
            QMessageBox.warning(self, "Test Connection", "Host is required")
            return
        
        # Create a custom dialog to show test progress
        test_dialog = QDialog(self)
        test_dialog.setWindowTitle("Testing Connection")
        test_dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(test_dialog)
        
        # Add a label at the top
        header_label = QLabel(f"Testing connection to {session_data['host']}...")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header_label)
        
        # Add a text area to show progress
        log_area = QTextEdit()
        log_area.setReadOnly(True)
        layout.addWidget(log_area)
        
        # Add a close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(test_dialog.accept)
        layout.addWidget(close_button)
        
        # Add standard ports to test
        ports_to_test = [
            (22, "SSH/SFTP"),
            (3389, "RDP"),
        ]
        
        # Critical fix: Keep reference to dialog to prevent garbage collection
        self.test_dialog = test_dialog
        
        # Function to add a log entry - needs to be thread-safe
        def add_log(message):
            # Use invokeMethod or similar to safely update from non-GUI thread
            log_area.append(message)
            cursor = log_area.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            log_area.setTextCursor(cursor)
        
        # Function to test a specific port
        def test_port(host, port, service_name):
            try:
                add_log(f"Testing {service_name} on port {port}...")
                
                # Create a socket and set a timeout
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)  # 3 second timeout
                
                # Try to connect
                result = s.connect_ex((host, port))
                s.close()
                
                # Check result
                if result == 0:
                    add_log(f"✅ Success: {service_name} on port {port} is open and accepting connections.")
                else:
                    add_log(f"❌ Failed: {service_name} on port {port} is not reachable.")
                    
            except socket.gaierror:
                add_log(f"❌ Error: Hostname {host} could not be resolved.")
            except socket.error as e:
                add_log(f"❌ Error testing {service_name} on port {port}: {e}")
            except Exception as e:
                add_log(f"❌ Unexpected error testing {service_name} on port {port}: {e}")
        
        # Function to run all tests in sequence
        def run_tests():
            try:
                add_log(f"Starting connection tests to {session_data['host']}...\n")
                
                # Test each port in sequence
                for port, service_name in ports_to_test:
                    test_port(session_data['host'], port, service_name)
                    add_log("")  # Add a blank line between tests
                
                add_log("All tests completed.")
                
                # This needs to be thread-safe too, use a signal/slot approach
                # For now, we'll enable it directly, but a better approach would use QMetaObject.invokeMethod
                close_button.setEnabled(True)
                
            except Exception as e:
                add_log(f"Error running tests: {e}")
                close_button.setEnabled(True)
        
        # Make sure close button is enabled after tests or on exception
        close_button.setEnabled(True)
        
        # Show the dialog
        test_dialog.show()
        
        # Start tests in a separate thread so UI remains responsive
        # Create a proper daemon thread that won't cause issues when the app exits
        test_thread = threading.Thread(target=run_tests, daemon=True)
        test_thread.start()

    def _populate_group_dropdown(self):
        """Populate the group dropdown with existing groups from the session manager."""
        # Clear existing items
        self.group_combo.clear()
        
        # Add an empty option
        self.group_combo.addItem("")
        
        # Get existing groups from session manager if available
        if hasattr(self.parent_window, 'session_manager'):
            # Get all unique group names
            groups = self.parent_window.session_manager.get_groups()
            
            # Add groups to dropdown
            for group in groups:
                if group and group.strip():  # Only add non-empty groups
                    self.group_combo.addItem(group)

    def _on_protocol_changed(self, protocol):
        """Update port based on selected protocol."""
        if protocol == "ssh":
            self.port_spinbox.setValue(22)
        elif protocol == "rdp":
            self.port_spinbox.setValue(3389)
        elif protocol == "telnet":
            self.port_spinbox.setValue(23)

    def accept(self):
        """Override accept to add validation."""
        # Get the current data
        session_data = self.get_session_data()
        
        # Validate required fields
        if not session_data["name"].strip():
            QMessageBox.warning(self, "Validation Error", "Session name is required.")
            self.name_edit.setFocus()
            return
        
        if not session_data["host"].strip():
            QMessageBox.warning(self, "Validation Error", "Host is required.")
            self.host_edit.setFocus()
            return
        
        if not session_data["username"].strip():
            QMessageBox.warning(self, "Validation Error", "Username is required for all connections.")
            self.username_edit.setFocus()
            return
        
        # Add warning if saving password
        if session_data["password"]:
            reply = QMessageBox.warning(
                self,
                "Security Warning",
                "We recommend using SSH keys instead of passwords. Your passwords will be visible in session backups.\n\n"
                "Do you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # If all validation passes, accept the dialog
        super().accept()