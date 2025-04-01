from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QMenu, QMessageBox,
    QDialog, QLineEdit, QComboBox, QFormLayout, QDialogButtonBox,
    QHeaderView
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QBrush

from core.ipam import IPAMManager, IPAMEntry, Subnet
import ipaddress
from pathlib import Path

class SubnetDialog(QDialog):
    """Dialog for adding or editing a subnet."""
    def __init__(self, subnet=None, parent=None):
        super().__init__(parent)
        self.subnet = subnet
        self.setWindowTitle("Subnet Properties")
        self.setMinimumWidth(400)
        
        # Create form layout
        layout = QFormLayout(self)
        
        # CIDR input
        self.cidr_edit = QLineEdit()
        layout.addRow("CIDR Notation:", self.cidr_edit)
        
        # Name input
        self.name_edit = QLineEdit()
        layout.addRow("Name:", self.name_edit)
        
        # Description input
        self.description_edit = QLineEdit()
        layout.addRow("Description:", self.description_edit)
        
        # Button box
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                           QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)
        
        # Fill with existing data if editing
        if subnet:
            self.cidr_edit.setText(subnet.cidr)
            self.name_edit.setText(subnet.name)
            self.description_edit.setText(subnet.description)
    
    def get_subnet_data(self):
        """Get the subnet data from the dialog."""
        return {
            "cidr": self.cidr_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "description": self.description_edit.text().strip()
        }

class IPEntryDialog(QDialog):
    """Dialog for adding or editing an IP entry."""
    def __init__(self, ipam_manager, entry=None, parent=None):
        super().__init__(parent)
        self.ipam_manager = ipam_manager
        self.entry = entry
        self.setWindowTitle("IP Address Properties")
        self.setMinimumWidth(400)
        
        # Create form layout
        layout = QFormLayout(self)
        
        # IP input
        self.ip_edit = QLineEdit()
        layout.addRow("IP Address:", self.ip_edit)
        
        # Hostname input
        self.hostname_edit = QLineEdit()
        layout.addRow("Hostname:", self.hostname_edit)
        
        # Description input
        self.description_edit = QLineEdit()
        layout.addRow("Description:", self.description_edit)
        
        # Status selector
        self.status_combo = QComboBox()
        for status in ["Unknown", "Active", "Reserved", "Available"]:
            self.status_combo.addItem(status)
        layout.addRow("Status:", self.status_combo)
        
        # Session selector
        self.session_combo = QComboBox()
        self.session_combo.addItem("", "")  # Empty option
        if ipam_manager.session_manager:
            for name, _ in ipam_manager.session_manager.sessions.items():
                self.session_combo.addItem(name, name)
        layout.addRow("Associated Session:", self.session_combo)
        
        # Button box
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                           QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)
        
        # Fill with existing data if editing
        if entry:
            self.ip_edit.setText(entry.ip)
            self.hostname_edit.setText(entry.hostname)
            self.description_edit.setText(entry.description)
            
            # Find and select the status in the combo box
            index = self.status_combo.findText(entry.status)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
            
            # Find and select the session in the combo box
            if entry.session_name:
                index = self.session_combo.findData(entry.session_name)
                if index >= 0:
                    self.session_combo.setCurrentIndex(index)
    
    def get_entry_data(self):
        """Get the IP entry data from the dialog."""
        return {
            "ip": self.ip_edit.text().strip(),
            "hostname": self.hostname_edit.text().strip(),
            "description": self.description_edit.text().strip(),
            "status": self.status_combo.currentText(),
            "session_name": self.session_combo.currentData()
        }

class IPAMWidget(QWidget):
    """Reusable IPAM widget that can be used as a tab or in a standalone window."""
    # Define signals
    session_selected = pyqtSignal(str)
    
    def __init__(self, ipam_manager, parent=None):
        super().__init__(parent)
        self.ipam_manager = ipam_manager
        
        self._create_ui()
        self._refresh_data()
    
    def _create_ui(self):
        """Create the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create Subnets tab
        self.subnets_tab = QWidget()
        subnets_layout = QVBoxLayout(self.subnets_tab)
        
        # Create subnet buttons layout
        subnet_buttons_layout = QHBoxLayout()
        self.add_subnet_btn = QPushButton("Add Subnet")
        self.add_subnet_btn.clicked.connect(self._on_add_subnet)
        subnet_buttons_layout.addWidget(self.add_subnet_btn)
        
        subnet_buttons_layout.addStretch()
        subnets_layout.addLayout(subnet_buttons_layout)
        
        # Create subnet table
        self.subnet_table = QTableWidget()
        self.subnet_table.setColumnCount(3)
        self.subnet_table.setHorizontalHeaderLabels(["CIDR", "Name", "Description"])
        self.subnet_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.subnet_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.subnet_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.subnet_table.customContextMenuRequested.connect(self._on_subnet_context_menu)
        subnets_layout.addWidget(self.subnet_table)
        
        # Create IP Addresses tab
        self.ips_tab = QWidget()
        ips_layout = QVBoxLayout(self.ips_tab)
        
        # Create IP buttons layout
        ip_buttons_layout = QHBoxLayout()
        self.add_ip_btn = QPushButton("Add IP Address")
        self.add_ip_btn.clicked.connect(self._on_add_ip)
        ip_buttons_layout.addWidget(self.add_ip_btn)
        
        ip_buttons_layout.addStretch()
        ips_layout.addLayout(ip_buttons_layout)
        
        # Create IP table
        self.ip_table = QTableWidget()
        self.ip_table.setColumnCount(4)
        self.ip_table.setHorizontalHeaderLabels(["IP Address", "Hostname", "Description", "Session"])
        self.ip_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.ip_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.ip_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ip_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ip_table.customContextMenuRequested.connect(self._on_ip_context_menu)
        self.ip_table.itemDoubleClicked.connect(self._on_ip_double_clicked)
        ips_layout.addWidget(self.ip_table)
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.subnets_tab, "Subnets")
        self.tab_widget.addTab(self.ips_tab, "IP Addresses")
    
    def _refresh_data(self):
        """Refresh the UI with current data."""
        self._populate_subnet_table()
        self._populate_ip_table()
    
    def _populate_subnet_table(self):
        """Populate the subnet table with data."""
        self.subnet_table.setRowCount(0)
        
        row = 0
        for cidr, subnet in sorted(self.ipam_manager.subnets.items()):
            self.subnet_table.insertRow(row)
            
            # CIDR
            self.subnet_table.setItem(row, 0, QTableWidgetItem(subnet.cidr))
            
            # Name
            self.subnet_table.setItem(row, 1, QTableWidgetItem(subnet.name))
            
            # Description
            self.subnet_table.setItem(row, 2, QTableWidgetItem(subnet.description))
            
            row += 1
    
    def _populate_ip_table(self):
        """Populate the IP address table with data."""
        self.ip_table.setRowCount(0)
        
        row = 0
        for ip, entry in sorted(self.ipam_manager.entries.items()):
            self.ip_table.insertRow(row)
            
            # IP Address
            self.ip_table.setItem(row, 0, QTableWidgetItem(entry.ip))
            
            # Hostname
            self.ip_table.setItem(row, 1, QTableWidgetItem(entry.hostname))
            
            # Description
            self.ip_table.setItem(row, 2, QTableWidgetItem(entry.description))
            
            # Session
            session_item = QTableWidgetItem(entry.session_name)
            if entry.session_name:
                # Highlight sessions that exist in the session manager
                if self.ipam_manager.session_manager and \
                   self.ipam_manager.session_manager.get_session(entry.session_name):
                    session_item.setForeground(QBrush(QColor("green")))
            self.ip_table.setItem(row, 3, session_item)
            
            row += 1
    
    def _on_add_subnet(self):
        """Handle add subnet button click."""
        dialog = SubnetDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            subnet_data = dialog.get_subnet_data()
            
            # Validate CIDR
            try:
                subnet = Subnet(
                    cidr=subnet_data["cidr"],
                    name=subnet_data["name"],
                    description=subnet_data["description"]
                )
                
                if self.ipam_manager.add_subnet(subnet):
                    self._refresh_data()
                else:
                    QMessageBox.warning(self, "Add Subnet", "Subnet already exists.")
            except ValueError as e:
                QMessageBox.critical(self, "Invalid CIDR", f"Invalid CIDR notation: {e}")
    
    def _on_add_ip(self):
        """Handle add IP button click."""
        dialog = IPEntryDialog(self.ipam_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            entry_data = dialog.get_entry_data()
            
            # Validate IP
            try:
                ipaddress.ip_address(entry_data["ip"])
                
                entry = IPAMEntry(
                    ip=entry_data["ip"],
                    hostname=entry_data["hostname"],
                    description=entry_data["description"],
                    status=entry_data["status"],
                    session_name=entry_data["session_name"]
                )
                
                self.ipam_manager.add_ip_entry(entry)
                self._refresh_data()
            except ValueError as e:
                QMessageBox.critical(self, "Invalid IP", f"Invalid IP address: {e}")
    
    def _on_subnet_context_menu(self, position):
        """Show context menu for subnet table."""
        row = self.subnet_table.rowAt(position.y())
        if row < 0:
            return
            
        cidr = self.subnet_table.item(row, 0).text()
        subnet = self.ipam_manager.get_subnet(cidr)
        if not subnet:
            return
            
        menu = QMenu(self)
        edit_action = menu.addAction("Edit Subnet")
        menu.addSeparator()
        remove_action = menu.addAction("Remove Subnet")
        
        action = menu.exec(self.subnet_table.mapToGlobal(position))
        
        if action == edit_action:
            self._edit_subnet(subnet)
        elif action == remove_action:
            self._remove_subnet(cidr)
    
    def _edit_subnet(self, subnet):
        """Open dialog to edit a subnet."""
        dialog = SubnetDialog(subnet, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            subnet_data = dialog.get_subnet_data()
            
            # Update the subnet
            subnet.name = subnet_data["name"]
            subnet.description = subnet_data["description"]
            self.ipam_manager.save_data()
            self._refresh_data()
    
    def _remove_subnet(self, cidr):
        """Remove a subnet and its associated IPs."""
        subnet = self.ipam_manager.get_subnet(cidr)
        if not subnet:
            return
            
        reply = QMessageBox.question(
            self,
            "Remove Subnet",
            f"Are you sure you want to remove subnet {cidr}?\n\n"
            f"This will also remove all associated IP entries.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.ipam_manager.remove_subnet(cidr):
                self._refresh_data()
    
    def _on_ip_context_menu(self, position):
        """Show context menu for IP table."""
        row = self.ip_table.rowAt(position.y())
        if row < 0:
            return
            
        ip = self.ip_table.item(row, 0).text()
        entry = self.ipam_manager.get_entry(ip)
        if not entry:
            return
            
        menu = QMenu(self)
        edit_action = menu.addAction("Edit IP Entry")
        
        # If associated with a session, add option to view session
        if entry.session_name and self.ipam_manager.session_manager and \
           self.ipam_manager.session_manager.get_session(entry.session_name):
            view_session_action = menu.addAction("Go to Session")
            menu.addSeparator()
        else:
            view_session_action = None
        
        remove_action = menu.addAction("Remove IP Entry")
        
        action = menu.exec(self.ip_table.mapToGlobal(position))
        
        if action == edit_action:
            self._edit_ip_entry(entry)
        elif action == remove_action:
            self._remove_ip_entry(ip)
        elif view_session_action and action == view_session_action:
            self.session_selected.emit(entry.session_name)
    
    def _on_ip_double_clicked(self, item):
        """Handle double-click on IP table item."""
        row = item.row()
        session_item = self.ip_table.item(row, 3)
        if session_item and session_item.text():
            session_name = session_item.text()
            if self.ipam_manager.session_manager and \
               self.ipam_manager.session_manager.get_session(session_name):
                self.session_selected.emit(session_name)
    
    def _edit_ip_entry(self, entry):
        """Open dialog to edit an IP entry."""
        dialog = IPEntryDialog(self.ipam_manager, entry, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            entry_data = dialog.get_entry_data()
            
            # Update existing entry
            entry.hostname = entry_data["hostname"]
            entry.description = entry_data["description"]
            entry.status = entry_data["status"]
            entry.session_name = entry_data["session_name"]
            self.ipam_manager.save_data()
            
            self._refresh_data()
    
    def _remove_ip_entry(self, ip):
        """Remove an IP entry."""
        reply = QMessageBox.question(
            self,
            "Remove IP Entry",
            f"Are you sure you want to remove IP entry {ip}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.ipam_manager.remove_ip_entry(ip):
                self._refresh_data()
    
    def select_session(self, session_name):
        """Select an IP entry associated with a session."""
        if not session_name:
            return
            
        # Switch to IP Addresses tab
        self.tab_widget.setCurrentIndex(1)
        
        # Find and select row with matching session name
        for row in range(self.ip_table.rowCount()):
            if self.ip_table.item(row, 3).text() == session_name:
                self.ip_table.selectRow(row)
                break
    
    def add_session_to_ipam(self, session):
        """Add a session's host to IPAM if it's a valid IP."""
        if not session or not session.host:
            return
            
        # Check if host is a valid IP address
        try:
            ipaddress.ip_address(session.host)
            
            # Check if it already exists
            if session.host in self.ipam_manager.entries:
                # Update the existing entry
                entry = self.ipam_manager.entries[session.host]
                entry.session_name = session.name
                if not entry.hostname and session.name:
                    entry.hostname = session.name
                self.ipam_manager.save_data()
            else:
                # Create a new entry
                entry = IPAMEntry(
                    ip=session.host,
                    hostname=session.name,
                    description=f"Added from session: {session.name}",
                    status="Active",
                    session_name=session.name
                )
                self.ipam_manager.add_ip_entry(entry)
            
            self._refresh_data()
        except ValueError:
            # Not a valid IP address, might be a hostname
            pass
    
    def update_session_in_ipam(self, session, old_host=None):
        """Update IP entries when a session is updated."""
        if old_host:
            # Update or remove the old entry
            if old_host in self.ipam_manager.entries:
                entry = self.ipam_manager.entries[old_host]
                if entry.session_name == session.name:
                    # This entry was linked to our session
                    if session.host and session.host != old_host:
                        # Host changed, remove old entry
                        self.ipam_manager.remove_ip_entry(old_host)
                    elif not session.host:
                        # No new host, just clear the session link
                        entry.session_name = ""
                        self.ipam_manager.save_data()
        
        # Add the new host if it exists and is different
        if session.host and (not old_host or session.host != old_host):
            self.add_session_to_ipam(session)
        
        self._refresh_data()


class IPAMWindow(QMainWindow):
    """Standalone window for IP Address Management."""
    def __init__(self, ipam_manager, parent=None):
        super().__init__(parent)
        self.ipam_manager = ipam_manager
        
        self.setWindowTitle("ASSHM - IP Address Management")
        self.resize(800, 600)
        
        # Create central widget
        self.ipam_widget = IPAMWidget(ipam_manager, self)
        self.setCentralWidget(self.ipam_widget)
        
        # Connect signals
        self.ipam_widget.session_selected.connect(self._on_session_selected)
        
        # Create menus
        self._create_menus()
        
        # Status bar for messages
        self.statusBar().showMessage("Ready")
    
    def _create_menus(self):
        """Create application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        close_action = QAction("&Close", self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        refresh_action = QAction("&Refresh Data", self)
        refresh_action.triggered.connect(self.ipam_widget._refresh_data)
        edit_menu.addAction(refresh_action)
    
    def _on_session_selected(self, session_name):
        """Handle session selection in standalone window."""
        if self.parent() and hasattr(self.parent(), "select_session_by_name"):
            # If we have a parent that knows how to select sessions, use it
            self.parent().select_session_by_name(session_name)
            self.close()  # Close this window as we're switching to main window
        else:
            # Just show a message
            QMessageBox.information(
                self,
                "Session Selected",
                f"Selected session: {session_name}\n\n"
                "To connect to this session, please use the main application window."
            ) 