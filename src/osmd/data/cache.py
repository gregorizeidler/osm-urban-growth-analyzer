"""Cache management for OSM data to improve performance and reduce API calls."""

import os
import json
import pickle
import hashlib
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import geopandas as gpd


class CacheManager:
    """Manages caching of OSM data and analysis results."""
    
    def __init__(self, cache_dir: Path, cache_ttl_hours: int = 24):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
            cache_ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        
        # Create subdirectories for different data types
        (self.cache_dir / "osm_data").mkdir(exist_ok=True)
        (self.cache_dir / "processed_data").mkdir(exist_ok=True)
        (self.cache_dir / "analysis_results").mkdir(exist_ok=True)
        (self.cache_dir / "metadata").mkdir(exist_ok=True)
    
    def _generate_cache_key(self, data: Dict[str, Any]) -> str:
        """
        Generate a unique cache key from data parameters.
        
        Args:
            data: Dictionary of parameters
            
        Returns:
            MD5 hash as cache key
        """
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(sorted_data.encode()).hexdigest()
    
    def _get_cache_path(self, cache_type: str, cache_key: str, 
                       file_format: str = "pkl") -> Path:
        """
        Get full path for cache file.
        
        Args:
            cache_type: Type of cache (osm_data, processed_data, etc.)
            cache_key: Unique cache key
            file_format: File format (pkl, json, geojson)
            
        Returns:
            Path to cache file
        """
        return self.cache_dir / cache_type / f"{cache_key}.{file_format}"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """
        Check if cache file is valid and not expired.
        
        Args:
            cache_path: Path to cache file
            
        Returns:
            True if cache is valid
        """
        if not cache_path.exists():
            return False
        
        # Check if cache has expired
        file_modified = datetime.fromtimestamp(cache_path.stat().st_mtime)
        return datetime.now() - file_modified < self.cache_ttl
    
    def get_osm_data(self, bbox: tuple, features: list, 
                     date_filter: Optional[str] = None) -> Optional[gpd.GeoDataFrame]:
        """
        Get cached OSM data.
        
        Args:
            bbox: Bounding box (south, west, north, east)
            features: List of OSM features
            date_filter: Optional date filter
            
        Returns:
            Cached GeoDataFrame or None if not found/expired
        """
        cache_key = self._generate_cache_key({
            "bbox": bbox,
            "features": sorted(features),
            "date_filter": date_filter,
            "type": "osm_data"
        })
        
        cache_path = self._get_cache_path("osm_data", cache_key, "pkl")
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Error loading cache: {e}")
                # Remove corrupted cache file
                cache_path.unlink(missing_ok=True)
        
        return None
    
    def save_osm_data(self, data: gpd.GeoDataFrame, bbox: tuple, 
                      features: list, date_filter: Optional[str] = None) -> None:
        """
        Save OSM data to cache.
        
        Args:
            data: GeoDataFrame to cache
            bbox: Bounding box used for query
            features: List of OSM features
            date_filter: Optional date filter used
        """
        cache_key = self._generate_cache_key({
            "bbox": bbox,
            "features": sorted(features),
            "date_filter": date_filter,
            "type": "osm_data"
        })
        
        cache_path = self._get_cache_path("osm_data", cache_key, "pkl")
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            
            # Save metadata
            metadata = {
                "bbox": bbox,
                "features": features,
                "date_filter": date_filter,
                "cached_at": datetime.now().isoformat(),
                "record_count": len(data),
                "cache_key": cache_key
            }
            
            metadata_path = self._get_cache_path("metadata", cache_key, "json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            print(f"Error saving to cache: {e}")
    
    def get_processed_data(self, data_id: str) -> Optional[gpd.GeoDataFrame]:
        """
        Get cached processed data.
        
        Args:
            data_id: Unique identifier for processed data
            
        Returns:
            Cached GeoDataFrame or None if not found/expired
        """
        cache_path = self._get_cache_path("processed_data", data_id, "pkl")
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Error loading processed data cache: {e}")
                cache_path.unlink(missing_ok=True)
        
        return None
    
    def save_processed_data(self, data: gpd.GeoDataFrame, data_id: str) -> None:
        """
        Save processed data to cache.
        
        Args:
            data: Processed GeoDataFrame
            data_id: Unique identifier
        """
        cache_path = self._get_cache_path("processed_data", data_id, "pkl")
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Error saving processed data to cache: {e}")
    
    def get_analysis_results(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached analysis results.
        
        Args:
            analysis_id: Unique identifier for analysis
            
        Returns:
            Cached results dictionary or None if not found/expired
        """
        cache_path = self._get_cache_path("analysis_results", analysis_id, "json")
        
        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading analysis results cache: {e}")
                cache_path.unlink(missing_ok=True)
        
        return None
    
    def save_analysis_results(self, results: Dict[str, Any], analysis_id: str) -> None:
        """
        Save analysis results to cache.
        
        Args:
            results: Analysis results dictionary
            analysis_id: Unique identifier
        """
        cache_path = self._get_cache_path("analysis_results", analysis_id, "json")
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving analysis results to cache: {e}")
    
    def clear_cache(self, cache_type: Optional[str] = None) -> int:
        """
        Clear cache files.
        
        Args:
            cache_type: Specific cache type to clear, or None for all
            
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        
        if cache_type:
            cache_subdir = self.cache_dir / cache_type
            if cache_subdir.exists():
                for file_path in cache_subdir.iterdir():
                    if file_path.is_file():
                        file_path.unlink()
                        deleted_count += 1
        else:
            # Clear all cache types
            for subdir in ["osm_data", "processed_data", "analysis_results", "metadata"]:
                cache_subdir = self.cache_dir / subdir
                if cache_subdir.exists():
                    for file_path in cache_subdir.iterdir():
                        if file_path.is_file():
                            file_path.unlink()
                            deleted_count += 1
        
        return deleted_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "cache_dir": str(self.cache_dir),
            "ttl_hours": self.cache_ttl.total_seconds() / 3600,
            "cache_types": {}
        }
        
        for cache_type in ["osm_data", "processed_data", "analysis_results", "metadata"]:
            cache_subdir = self.cache_dir / cache_type
            if cache_subdir.exists():
                files = list(cache_subdir.iterdir())
                total_size = sum(f.stat().st_size for f in files if f.is_file())
                
                stats["cache_types"][cache_type] = {
                    "file_count": len([f for f in files if f.is_file()]),
                    "total_size_mb": total_size / (1024 * 1024),
                    "valid_files": len([f for f in files if f.is_file() and self._is_cache_valid(f)])
                }
        
        return stats
    
    def cleanup_expired_cache(self) -> int:
        """
        Remove expired cache files.
        
        Returns:
            Number of expired files removed
        """
        deleted_count = 0
        
        for cache_type in ["osm_data", "processed_data", "analysis_results", "metadata"]:
            cache_subdir = self.cache_dir / cache_type
            if cache_subdir.exists():
                for file_path in cache_subdir.iterdir():
                    if file_path.is_file() and not self._is_cache_valid(file_path):
                        file_path.unlink()
                        deleted_count += 1
        
        return deleted_count
