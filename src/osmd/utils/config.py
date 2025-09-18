"""Configuration management for the OSM Urban Growth Analysis project."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class BoundingBox:
    """Represents a geographic bounding box."""
    south: float
    west: float
    north: float
    east: float
    
    def to_overpass_bbox(self) -> str:
        """Convert to Overpass API bbox format."""
        return f"{self.south},{self.west},{self.north},{self.east}"
    
    def to_tuple(self) -> tuple:
        """Convert to tuple format (south, west, north, east)."""
        return (self.south, self.west, self.north, self.east)


class ConfigManager:
    """Manages configuration settings for the OSM Urban Growth Analysis project."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, uses default config.yaml
        """
        self.config_path = config_path or self._get_default_config_path()
        self._config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        project_root = Path(__file__).parent.parent.parent.parent
        return str(project_root / "config.yaml")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing configuration file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key using dot notation.
        
        Args:
            key: Configuration key (e.g., 'database.host')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self.get('database', {})
    
    def get_osm_config(self) -> Dict[str, Any]:
        """Get OSM configuration."""
        return self.get('osm', {})
    
    def get_analysis_config(self) -> Dict[str, Any]:
        """Get analysis configuration."""
        return self.get('analysis', {})
    
    def get_visualization_config(self) -> Dict[str, Any]:
        """Get visualization configuration."""
        return self.get('visualization', {})
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration."""
        return self.get('processing', {})
    
    def get_default_bbox(self) -> BoundingBox:
        """Get default bounding box for analysis."""
        bbox_config = self.get('analysis.default_bbox', {})
        return BoundingBox(
            south=bbox_config.get('south', -23.6821),
            west=bbox_config.get('west', -46.9249),
            north=bbox_config.get('north', -23.4323),
            east=bbox_config.get('east', -46.3654)
        )
    
    def get_comparison_years(self) -> List[int]:
        """Get years for temporal comparison."""
        return self.get('analysis.comparison_years', [2010, 2015, 2020, 2024])
    
    def get_osm_features(self) -> Dict[str, List[str]]:
        """Get OSM features to track."""
        return self.get('analysis.features', {})
    
    def get_cache_dir(self) -> Path:
        """Get cache directory path."""
        cache_dir = self.get('osm.cache_dir', './data/cache')
        path = Path(cache_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def is_cache_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self.get('osm.cache_enabled', True)
    
    def get_overpass_url(self) -> str:
        """Get Overpass API URL."""
        return self.get('osm.overpass_url', 'https://overpass-api.de/api/interpreter')
    
    def get_overpass_timeout(self) -> int:
        """Get Overpass API timeout in seconds."""
        return self.get('osm.timeout', 300)
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._config = self._load_config()
    
    def update(self, key: str, value: Any) -> None:
        """
        Update configuration value.
        
        Args:
            key: Configuration key using dot notation
            value: New value
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, path: Optional[str] = None) -> None:
        """
        Save configuration to file.
        
        Args:
            path: Optional path to save to. If None, uses current config path.
        """
        save_path = path or self.config_path
        with open(save_path, 'w', encoding='utf-8') as file:
            yaml.dump(self._config, file, default_flow_style=False, indent=2)
