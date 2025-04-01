from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                         QLineEdit, QSpinBox, QCheckBox, QTabWidget,
                         QPushButton, QLabel, QDialogButtonBox, QGroupBox,
                         QFileDialog, QWidget)
from PyQt6.QtCore import Qt

class PreferencesDialog(QDialog):
    """Dialog for editing application preferences."""
    
    def __init__(self, config, parent=None):
        """Initialize the dialog with configuration."""
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("ASSHM - Preferences")
        self.resize(500, 400)
        
        self._create_ui()
        self._load_current_settings()
    
    def _create_ui(self):
        """Create the dialog UI components."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # General tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Application paths group
        paths_group = QGroupBox("Application Paths")
        paths_layout = QFormLayout(paths_group)
        
        # PuTTY path
        putty_layout = QHBoxLayout()
        self.putty_path_edit = QLineEdit()
        putty_browse_button = QPushButton("Browse...")
        putty_browse_button.clicked.connect(self._browse_putty_path)
        putty_layout.addWidget(self.putty_path_edit)
        putty_layout.addWidget(putty_browse_button)
        paths_layout.addRow("PuTTY Path:", putty_layout)
        
        # WinSCP path
        winscp_layout = QHBoxLayout()
        self.winscp_path_edit = QLineEdit()
        winscp_browse_button = QPushButton("Browse...")
        winscp_browse_button.clicked.connect(self._browse_winscp_path)
        winscp_layout.addWidget(self.winscp_path_edit)
        winscp_layout.addWidget(winscp_browse_button)
        paths_layout.addRow("WinSCP Path:", winscp_layout)
        
        general_layout.addWidget(paths_group)
        
        # Backups group
        backups_group = QGroupBox("Backups")
        backups_layout = QFormLayout(backups_group)
        
        self.max_backups_spin = QSpinBox()
        self.max_backups_spin.setRange(1, 50)
        backups_layout.addRow("Maximum Backups:", self.max_backups_spin)
        
        general_layout.addWidget(backups_group)
        
        # Interface tab
        ui_tab = QWidget()
        ui_layout = QVBoxLayout(ui_tab)
        
        # UI Settings group
        ui_group = QGroupBox("Interface Settings")
        ui_settings_layout = QFormLayout(ui_group)
        
        self.show_toolbar_check = QCheckBox("Show Toolbar")
        ui_settings_layout.addRow("", self.show_toolbar_check)
        
        self.show_statusbar_check = QCheckBox("Show Status Bar")
        ui_settings_layout.addRow("", self.show_statusbar_check)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 20)
        ui_settings_layout.addRow("Font Size:", self.font_size_spin)
        
        ui_layout.addWidget(ui_group)
        
        # Add tabs to tab widget (removed security tab)
        self.tabs.addTab(general_tab, "General")
        self.tabs.addTab(ui_tab, "Interface")
        
        layout.addWidget(self.tabs)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _load_current_settings(self):
        """Load current settings from config."""
        # General settings
        self.putty_path_edit.setText(self.config.get("general", "putty_path", ""))
        self.winscp_path_edit.setText(self.config.get("general", "winscp_path", ""))
        self.max_backups_spin.setValue(self.config.get("general", "max_backups", 5))
        
        # UI settings
        self.show_toolbar_check.setChecked(self.config.get("ui", "show_toolbar", True))
        self.show_statusbar_check.setChecked(self.config.get("ui", "show_statusbar", True))
        self.font_size_spin.setValue(self.config.get("ui", "font_size", 10))
    
    def _browse_putty_path(self):
        """Browse for PuTTY executable."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select PuTTY Executable", "", "Executable Files (*.exe);;All Files (*.*)"
        )
        if file_path:
            self.putty_path_edit.setText(file_path)
    
    def _browse_winscp_path(self):
        """Browse for WinSCP executable."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select WinSCP Executable", "", "Executable Files (*.exe);;All Files (*.*)"
        )
        if file_path:
            self.winscp_path_edit.setText(file_path)
    
    def get_settings(self):
        """Get settings from dialog."""
        return {
            "general": {
                "putty_path": self.putty_path_edit.text(),
                "winscp_path": self.winscp_path_edit.text(),
                "max_backups": self.max_backups_spin.value()
            },
            "ui": {
                "show_toolbar": self.show_toolbar_check.isChecked(),
                "show_statusbar": self.show_statusbar_check.isChecked(),
                "font_size": self.font_size_spin.value()
            }
        } 