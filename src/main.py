import sys
import os
import traceback  # Added for better error reporting
from PyQt6.QtWidgets import QApplication, QMessageBox
from ui.main_window import MainWindow
from ui.session_dialog import SessionDialog
from core.session_manager import SessionManager, Session
from core.launcher import Launcher
from core.config_manager import ConfigManager  # Use your ConfigManager
from PyQt6.QtGui import QIcon
from pathlib import Path

# Global exception handler
def exception_hook(exctype, value, tb):
    """Handle uncaught exceptions and show details to the user."""
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    
    error_dialog = QMessageBox()
    error_dialog.setIcon(QMessageBox.Icon.Critical)
    error_dialog.setWindowTitle("Unhandled Exception")
    error_dialog.setText("An unexpected error occurred:")
    error_dialog.setDetailedText(error_msg)
    error_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
    error_dialog.exec()

def main():
    """Entry point for the application."""
    # Install global exception handler
    sys.excepthook = exception_hook
    
    # Create application instance
    app = QApplication(sys.argv)
    app.setApplicationName("ASSHM")
    app.setApplicationDisplayName("ASSHM - Advanced SSH Manager")
    app.setOrganizationName("ASSHM")
    
    # Set application icon
    from PyQt6.QtGui import QIcon
    from pathlib import Path
    
    # Get the directory where main.py is located and construct path to assets
    current_dir = Path(__file__).parent
    icon_path = current_dir / "assets" / "ASSHM.ico"
    if not icon_path.exists():
        # Try PNG as fallback
        icon_path = current_dir / "assets" / "ASSHM.png"
    
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    try:
        # Load configuration using ConfigManager
        config = ConfigManager()
        
        # Initialize session manager (removed encryption_service)
        session_manager = SessionManager(config)
        
        # Initialize launcher
        launcher = Launcher(config)
        
        # Create and show the main window with all necessary services
        main_window = MainWindow(config, session_manager, launcher)
        main_window.show()
        
        # Execute the application
        sys.exit(app.exec())
        
    except Exception as e:
        QMessageBox.critical(None, "Error", f"An error occurred while starting the application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()