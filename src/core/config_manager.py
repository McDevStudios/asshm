import json
import os
from pathlib import Path

class ConfigManager:
    """
    Manages configuration settings for the application.
    Handles loading, saving, and accessing configuration values.
    """
    
    def __init__(self, config_file=None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file: Path to the configuration file. If None, uses default location.
        """
        if config_file:
            self.config_file = Path(config_file)
        else:
            # Use default location in user's home directory
            self.config_file = Path.home() / ".asshm" / "config.json"
        
        # Ensure directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Default configuration
        self.config = {
            "general": {
                "putty_path": "",
                "winscp_path": "",
                "default_protocol": "ssh",
                "save_passwords": True
            },
            "ui": {
                "show_toolbar": True,
                "show_statusbar": True,
                "font_size": 10,
                "theme": "system"
            },
            "ipam": {
                "enabled": True,
                "subnet_mask": "255.255.255.0"
            }
        }
        
        # Load existing configuration if available
        self.load()
    
    def load(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                
                # Update the default config with loaded values
                self._merge_configs(self.config, loaded_config)
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, section, key, default=None):
        """
        Get a configuration value.
        
        Args:
            section: Configuration section name
            key: Configuration key
            default: Default value if not found
            
        Returns:
            The configuration value or default if not found
        """
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        return default
    
    def set(self, section, key, value):
        """
        Set a configuration value.
        
        Args:
            section: Configuration section name
            key: Configuration key  
            value: Value to set
        """
        # Create section if it doesn't exist
        if section not in self.config:
            self.config[section] = {}
        
        # Set the value
        self.config[section][key] = value
    
    def _merge_configs(self, target, source):
        """
        Recursively merge source config into target config.
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursively update dictionaries
                self._merge_configs(target[key], value)
            else:
                # Replace or add values
                target[key] = value 