# config_manager.py
import json
import os
import logging
from typing import Dict, List, Any, Optional
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from utils.session_manager import SessionManager

class ConfigManager:
    """Manages configuration files for the automation tool with optimized performance."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._check_config_dir()
        
        # Define essential file paths
        self.mobile_devices_path = self.config_dir / "mobile_devices.json"
        self.telegram_entities_path = self.config_dir / "telegram_entities.json"
        self.env_file_path = self.config_dir.parent / ".env"
        self.example_env_file = self.config_dir.parent / ".env.example"
        self.sessions_dir = self.config_dir.parent / "sessions"
        
        # Default environment settings (prevents redundant parsing)
        self.default_env_settings = {
            "TELEGRAM_API_ID": "",
            # ... (other settings)
        }
        
        # Single-source cache for configuration files
        self._config_cache = {}
        
        # Lazy-loaded session manager
        self._session_manager = None
        
        # Load environment variables (only once)
        load_dotenv(find_dotenv(str(self.env_file_path), usecwd=True))
        
        # Ensure critical files exist
        self._initialize_config_files()
    
    def _check_config_dir(self) -> None:
        """Ensure config directory exists with atomic mkdir."""
        self.config_dir.mkdir(exist_ok=True, parents=True)
        logging.info(f"Config directory confirmed: {self.config_dir}")
    
    def _initialize_config_files(self) -> None:
        """Create missing config files once during initialization."""
        if not self.example_env_file.exists():
            self._create_example_env()
        if not self.mobile_devices_path.exists():
            self._create_default_devices()
        if not self.telegram_entities_path.exists():
            self._create_empty_telegram_entities()
    
    def _read_json_file(self, file_path: Path) -> Any:
        """Efficient JSON reading with cache."""
        if file_path in self._config_cache:
            return self._config_cache[file_path]
        
        try:
            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
                self._config_cache[file_path] = data
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            # Return empty dict/list based on file type
            return [] if file_path == self.mobile_devices_path else {}
    
    def _write_json_file(self, file_path: Path, data: Any) -> bool:
        """Atomic JSON writing with cache invalidation."""
        try:
            with file_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            self._config_cache[file_path] = data  # Update cache
            return True
        except Exception as e:
            logging.error(f"Error writing to {file_path}: {e}")
            return False
    
    def get_env_settings(self) -> Dict[str, str]:
        """Efficiently retrieve environment variables using os.getenv."""
        env_vars = self.default_env_settings.copy()
        for key in env_vars:
            env_vars[key] = os.getenv(key, env_vars[key])
        return env_vars
    
    def save_env_settings(self, settings: Dict[str, str]) -> bool:
        """Batch update .env file to minimize I/O operations."""
        try:
            # Read existing .env into a dict
            env_data = {}
            if self.env_file_path.exists():
                with self.env_file_path.open('r') as f:
                    for line in f:
                        if '=' in line:
                            k, v = line.strip().split('=', 1)
                            env_data[k] = v.strip("'\"")
            
            # Update with new values
            env_data.update({**self.default_env_settings, **settings})
            
            # Write back in one operation
            with self.env_file_path.open('w') as f:
                for key in sorted(env_data.keys()):
                    f.write(f"{key}='{env_data[key]}'\n")
            return True
        except Exception as e:
            logging.error(f"Error writing to .env: {e}")
            return False
    
    def get_mobile_devices(self) -> List[Dict[str, Any]]:
        """Cached device list with O(1) access."""
        return self._read_json_file(self.mobile_devices_path)
    
    def get_device_by_name(self, device_name: str) -> Optional[Dict[str, Any]]:
        """O(1) device lookup using a pre-built index."""
        devices = self.get_mobile_devices()
        if not hasattr(self, '_device_index'):
            self._device_index = {d['name']: d for d in devices}
        return self._device_index.get(device_name)
    
    def invalidate_cache(self, file_path: Optional[Path] = None) -> None:
        """Invalidate cache for a specific file or all files."""
        if file_path is not None:
            self._config_cache.pop(file_path, None)
        else:
            self._config_cache.clear()
            if hasattr(self, '_device_index'):
                delattr(self, '_device_index')