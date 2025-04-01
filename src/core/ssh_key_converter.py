import os
from pathlib import Path

class SSHKeyConverter:
    """
    Simple utility for checking SSH key formats and finding PuTTYgen.
    Instead of automated conversion, we now recommend manual conversion using PuTTYgen.
    """
    
    @staticmethod
    def is_ppk_file(key_path):
        """
        Check if the file is in PPK format based on extension.
        
        Args:
            key_path: Path to the key file
            
        Returns:
            True if the file has .ppk extension, False otherwise
        """
        return str(key_path).lower().endswith('.ppk')
    
    @staticmethod
    def is_openssh_format(key_path):
        """
        Check if a key file is in OpenSSH format by reading its first few lines.
        
        Args:
            key_path: Path to the key file
            
        Returns:
            True if the file is in OpenSSH format, False otherwise
        """
        try:
            with open(key_path, 'r') as f:
                first_line = f.readline().strip()
                return (
                    "BEGIN OPENSSH PRIVATE KEY" in first_line or 
                    "BEGIN RSA PRIVATE KEY" in first_line or
                    "BEGIN DSA PRIVATE KEY" in first_line or
                    "BEGIN EC PRIVATE KEY" in first_line
                )
        except Exception:
            return False
    
    @staticmethod
    def find_puttygen():
        """Find PuTTYgen executable on Windows."""
        puttygen_paths = [
            "C:\\Program Files\\PuTTY\\puttygen.exe",
            "C:\\Program Files (x86)\\PuTTY\\puttygen.exe"
        ]
        
        for path in puttygen_paths:
            if os.path.exists(path):
                return path
                
        return None
    
    @staticmethod
    def launch_puttygen_for_conversion(key_path):
        """
        Launch PuTTYgen with the specified key file for manual conversion.
        
        Args:
            key_path: Path to the OpenSSH key file to convert
            
        Returns:
            True if PuTTYgen was launched, False otherwise
        """
        import subprocess
        
        puttygen_path = SSHKeyConverter.find_puttygen()
        if not puttygen_path:
            return False
            
        try:
            subprocess.Popen([puttygen_path, str(key_path)])
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_suggested_ppk_path(openssh_key_path):
        """
        Get the suggested path for the PPK file based on the OpenSSH key path.
        
        Args:
            openssh_key_path: Path to the OpenSSH key file
            
        Returns:
            Path with .ppk extension
        """
        return Path(openssh_key_path).with_suffix('.ppk') 