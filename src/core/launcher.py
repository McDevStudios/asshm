import subprocess
import os
import shlex
from pathlib import Path
import platform
import tempfile
from .ssh_key_converter import SSHKeyConverter
from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PyQt6.QtCore import Qt

class Launcher:
    """Utility for launching external applications like PuTTY and WinSCP."""
    
    def __init__(self, config):
        """Initialize launcher with configuration."""
        self.config = config
        self.putty_path = self._find_path("putty", config.get("general", "putty_path"))
        self.winscp_path = self._find_path("winscp", config.get("general", "winscp_path"))
        # Track temporary files to clean up later if needed
        self.temp_files = []
    
    def __del__(self):
        """Clean up any temporary files when the launcher is destroyed."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
    
    def _find_path(self, app_name, configured_path=None):
        """Find path to application executable."""
        if configured_path and Path(configured_path).is_file():
            return configured_path
            
        # Common installation locations
        common_locations = []
        
        if platform.system() == "Windows":
            program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
            program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
            
            if app_name.lower() == "putty":
                common_locations = [
                    Path(program_files) / "PuTTY" / "putty.exe",
                    Path(program_files_x86) / "PuTTY" / "putty.exe",
                    Path(program_files) / "PuTTY" / "plink.exe",  # Command-line version
                    Path(program_files_x86) / "PuTTY" / "plink.exe",
                ]
            elif app_name.lower() == "winscp":
                common_locations = [
                    Path(program_files) / "WinSCP" / "WinSCP.exe",
                    Path(program_files_x86) / "WinSCP" / "WinSCP.exe",
                ]
        else:
            # For Linux and macOS, check common paths
            if app_name.lower() == "putty":
                common_locations = [
                    Path("/usr/bin/putty"),
                    Path("/usr/local/bin/putty"),
                ]
            elif app_name.lower() == "winscp":
                # WinSCP is Windows-only, but could be run with Wine
                common_locations = []
        
        # Look for the executable in PATH
        for path_dir in os.environ.get("PATH", "").split(os.pathsep):
            if app_name.lower() == "putty":
                exe_name = "putty.exe" if platform.system() == "Windows" else "putty"
                possible_path = Path(path_dir) / exe_name
                if possible_path.is_file():
                    return str(possible_path)
            elif app_name.lower() == "winscp":
                exe_name = "WinSCP.exe" if platform.system() == "Windows" else "winscp"
                possible_path = Path(path_dir) / exe_name
                if possible_path.is_file():
                    return str(possible_path)
        
        # Check common locations
        for location in common_locations:
            if location.is_file():
                # Update config with found path
                if app_name.lower() == "putty":
                    self.config.set("general", "putty_path", str(location))
                elif app_name.lower() == "winscp":
                    self.config.set("general", "winscp_path", str(location))
                self.config.save()
                return str(location)
        
        return None
    
    def launch_putty(self, session=None, raw_args=None):
        """Launch PuTTY with a session or raw arguments."""
        import os
        import subprocess
        from PyQt6.QtWidgets import QMessageBox
        
        # ALWAYS look for putty.exe specifically, ignoring plink.exe
        putty_executable = None
        potential_paths = [
            "C:\\Program Files\\PuTTY\\putty.exe",
            "C:\\Program Files (x86)\\PuTTY\\putty.exe"
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                putty_executable = path
                break
        
        if not putty_executable:
            raise FileNotFoundError("PuTTY GUI executable (putty.exe) not found")
        
        # Build the command - only use putty.exe
        cmd = [putty_executable]
        
        if session:
            key_file_used = False
            
            # First check if we have a valid key file
            if hasattr(session, 'key_file') and session.key_file:
                key_file_path = session.key_file
                
                if os.path.exists(key_file_path):
                    # Check if it's a PPK file (only format PuTTY accepts)
                    if key_file_path.lower().endswith('.ppk'):
                        # Add host info - using just the hostname here since we'll use -i for auth
                        cmd.extend([
                            "-ssh",
                            session.host,
                            "-P", str(getattr(session, 'port', 22))
                        ])
                        
                        # Use the PPK key file
                        cmd.extend(["-i", key_file_path])
                        key_file_used = True
                        
                        # Add username if provided
                        if session.username:
                            cmd.extend(["-l", session.username])
                            
                        # Log safely (no password included in key file scenarios)
                        print(f"Launching PuTTY with SSH key authentication")
                    else:
                        # It's not a PPK file - we need to warn the user
                        result = QMessageBox.warning(
                            None,
                            "Incompatible SSH Key Format",
                            f"The key file '{key_file_path}' is not in PPK format required by PuTTY.\n\n"
                            f"Would you like to continue with password authentication instead?\n"
                            f"(Choose 'No' to cancel and convert your key first)",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.Yes
                        )
                        
                        if result == QMessageBox.StandardButton.No:
                            # User wants to fix the key first
                            convert_instructions = QMessageBox()
                            convert_instructions.setIcon(QMessageBox.Icon.Information)
                            convert_instructions.setWindowTitle("Convert SSH Key")
                            convert_instructions.setText("How to convert your SSH key:")
                            convert_instructions.setInformativeText(
                                "1. Open PuTTYgen from your PuTTY installation\n"
                                "2. Click 'Load' and select your existing key file\n"
                                "3. Click 'Save private key' to create a PPK file\n"
                                "4. Edit your session to use the new PPK file"
                            )
                            convert_instructions.exec()
                            return None  # Cancel the connection
                else:
                    print(f"Warning: SSH key file '{key_file_path}' does not exist.")
                    QMessageBox.warning(
                        None, 
                        "SSH Key Not Found",
                        f"The SSH key file '{key_file_path}' does not exist.\n\n"
                        f"Continuing with password authentication."
                    )
            
            # If no key file was used, use username/password authentication
            if not key_file_used:
                # Use the simple -ssh user@host approach
                target = f"{session.username}@{session.host}" if session.username else session.host
                
                cmd.extend([
                    "-ssh",
                    target,
                    "-P", str(getattr(session, 'port', 22))
                ])
                
                # Add password if available (but don't log it)
                if session.password:
                    cmd.extend(["-pw", session.password])
                    print("Using password authentication")
                
                # Create a safe_cmd to log (without password)
                safe_cmd = cmd.copy()
                if session.password:
                    pw_index = safe_cmd.index("-pw")
                    if pw_index >= 0 and pw_index + 1 < len(safe_cmd):
                        safe_cmd[pw_index + 1] = "********"
            else:
                # If key file was used, the cmd is already safe to log
                safe_cmd = cmd
            
            # Add any additional parameters if specified
            if hasattr(session, 'params') and session.params:
                # Split by spaces and add as separate arguments
                for param in session.params.split():
                    cmd.append(param)
                    safe_cmd.append(param)  # Also add to safe_cmd
        elif raw_args:
            # Use raw args directly
            if isinstance(raw_args, str):
                import shlex
                raw_args_list = shlex.split(raw_args)
                cmd.extend(raw_args_list)
                
                # Create safe version by masking any potential passwords
                safe_cmd = cmd.copy()
                if "-pw" in raw_args_list:
                    pw_index = safe_cmd.index("-pw")
                    if pw_index >= 0 and pw_index + 1 < len(safe_cmd):
                        safe_cmd[pw_index + 1] = "********"
            else:
                cmd.extend(raw_args)
                # Create a safe version
                safe_cmd = cmd.copy()
                if "-pw" in raw_args:
                    pw_index = safe_cmd.index("-pw")
                    if pw_index >= 0 and pw_index + 1 < len(safe_cmd):
                        safe_cmd[pw_index + 1] = "********"
        else:
            # No arguments - safe to log directly
            safe_cmd = cmd
        
        # Debug output with masked password
        print(f"Launching PuTTY GUI with command: {safe_cmd}")
        
        # Launch the process
        return subprocess.Popen(cmd)
    
    def launch_winscp(self, session=None, raw_args=None):
        """Launch WinSCP with a session or raw arguments."""
        import os
        import subprocess
        
        # Look for WinSCP executable
        winscp_path = None
        potential_paths = [
            "C:\\Program Files\\WinSCP\\WinSCP.exe",
            "C:\\Program Files (x86)\\WinSCP\\WinSCP.exe"
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                winscp_path = path
                break
        
        if not winscp_path:
            raise FileNotFoundError("WinSCP executable not found")
        
        cmd = [winscp_path]
        
        if session:
            # For WinSCP with SSH key authentication
            protocol = "sftp"
            url = f"{protocol}://"
            
            # Create a safe URL for logging (without password)
            safe_url = f"{protocol}://"
            
            # Add username 
            if session.username:
                url += session.username
                safe_url += session.username
                
                # Add password if no key file is specified
                if session.password and not (hasattr(session, 'key_file') and session.key_file):
                    url += f":{session.password}"
                    safe_url += ":********"  # Mask password in safe URL
                url += "@"
                safe_url += "@"
            
            # Add host
            url += session.host
            safe_url += session.host
            
            # We'll use the raw command with rawsettings for SSH key support
            cmd.append(url)
            
            # If key file is specified, add it using rawsettings
            if hasattr(session, 'key_file') and session.key_file and os.path.exists(session.key_file):
                # No need to convert the key - WinSCP handles OpenSSH keys directly
                cmd.append(f"/privatekey={session.key_file}")
            
            # Add any additional parameters
            if hasattr(session, 'params') and session.params:
                for param in session.params.split():
                    cmd.append(param)
            
            # Debug output with masked password
            print(f"Launching WinSCP with URL: {safe_url}")
                
        elif raw_args:
            # Use raw args directly - just mask the URL if it contains a password
            if isinstance(raw_args, str):
                cmd_args = shlex.split(raw_args)
                cmd.extend(cmd_args)
                
                # For logging, mask any URL with passwords
                safe_args = []
                for arg in cmd_args:
                    if "://" in arg and ":" in arg and "@" in arg:
                        # This looks like a URL with a password
                        protocol, rest = arg.split("://", 1)
                        if "@" in rest:
                            creds, host = rest.split("@", 1)
                            if ":" in creds:
                                user, _ = creds.split(":", 1)
                                safe_args.append(f"{protocol}://{user}:********@{host}")
                            else:
                                safe_args.append(arg)  # No password to mask
                        else:
                            safe_args.append(arg)  # No credentials to mask
                    else:
                        safe_args.append(arg)
                
                print(f"Launching WinSCP with command: {[winscp_path] + safe_args}")
            else:
                cmd.extend(raw_args)
                # Can't easily mask passwords in a non-string arg list, so just provide minimal info
                print(f"Launching WinSCP (with raw arguments)")
        else:
            # Just launching WinSCP without args
            print(f"Launching WinSCP without arguments")
        
        # Launch the process
        return subprocess.Popen(cmd)
