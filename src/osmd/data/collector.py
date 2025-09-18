"""OSM data collection module for historical urban growth analysis."""

import time
import requests
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString, Polygon
from shapely import wkt
import json

from ..utils import (
    ConfigManager, Logger, bbox_to_overpass_query, get_time_periods,
    split_large_bbox, optimize_overpass_query, estimate_query_complexity
)
from .cache import CacheManager


class OSMDataCollector:
    """Collects historical OSM data for urban growth analysis."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize OSM data collector.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager or ConfigManager()
        self.logger = Logger("OSMDataCollector")
        
        # Initialize cache manager if caching is enabled
        if self.config.is_cache_enabled():
            self.cache = CacheManager(self.config.get_cache_dir())
        else:
            self.cache = None
        
        # OSM API settings
        self.overpass_url = self.config.get_overpass_url()
        self.timeout = self.config.get_overpass_timeout()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # seconds between requests
    
    def _rate_limit(self) -> None:
        """Implement rate limiting for API requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_overpass_request(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Make request to Overpass API.
        
        Args:
            query: Overpass query string
            
        Returns:
            JSON response or None if failed
        """
        self._rate_limit()
        
        try:
            self.logger.debug(f"Making Overpass API request: {query[:100]}...")
            
            response = requests.post(
                self.overpass_url,
                data=query,
                timeout=self.timeout,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            self.logger.error("Overpass API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Overpass API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Overpass API response: {e}")
            return None
    
    def _parse_osm_elements(self, elements: List[Dict[str, Any]]) -> gpd.GeoDataFrame:
        """
        Parse OSM elements into GeoDataFrame.
        
        Args:
            elements: List of OSM elements from API response
            
        Returns:
            GeoDataFrame with parsed geometries and attributes
        """
        parsed_data = []
        
        for element in elements:
            try:
                # Extract basic information
                osm_id = element.get('id')
                osm_type = element.get('type')
                tags = element.get('tags', {})
                
                # Parse geometry based on element type
                geometry = None
                
                if osm_type == 'node':
                    lat = element.get('lat')
                    lon = element.get('lon')
                    if lat is not None and lon is not None:
                        geometry = Point(lon, lat)
                
                elif osm_type == 'way':
                    # Get coordinates from geometry
                    coords = []
                    if 'geometry' in element:
                        for node in element['geometry']:
                            coords.append((node['lon'], node['lat']))
                    
                    if len(coords) >= 2:
                        # Check if it's a closed polygon
                        if len(coords) >= 4 and coords[0] == coords[-1]:
                            # It's a polygon
                            geometry = Polygon(coords)
                        else:
                            # It's a linestring
                            geometry = LineString(coords)
                
                elif osm_type == 'relation':
                    # Relations are more complex - for now, skip or handle basic cases
                    continue
                
                if geometry is not None:
                    # Create record
                    record = {
                        'osm_id': osm_id,
                        'osm_type': osm_type,
                        'geometry': geometry
                    }
                    
                    # Add all tags as columns
                    record.update(tags)
                    parsed_data.append(record)
            
            except Exception as e:
                self.logger.warning(f"Failed to parse OSM element {element.get('id', 'unknown')}: {e}")
                continue
        
        if not parsed_data:
            return gpd.GeoDataFrame(columns=['osm_id', 'osm_type', 'geometry'])
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(parsed_data, crs='EPSG:4326')
        
        self.logger.info(f"Parsed {len(gdf)} OSM elements")
        return gdf
    
    def collect_historical_data(self, bbox: Tuple[float, float, float, float],
                               features: List[str], years: List[int]) -> Dict[int, gpd.GeoDataFrame]:
        """
        Collect historical OSM data for multiple years.
        Note: For demo purposes, this collects current data and simulates historical data.
        Real historical data would require OSM history planet files or Overpass temporal queries.
        
        Args:
            bbox: Bounding box (south, west, north, east)
            features: List of OSM features to collect
            years: List of years to collect data for
            
        Returns:
            Dictionary mapping years to GeoDataFrames
        """
        self.logger.log_analysis_start(bbox, years)
        
        historical_data = {}
        
        # For demo, collect current data first
        self.logger.info("Collecting current OSM data (simulating historical analysis)")
        
        # Check cache first
        cache_key = f"current_data_{hash(str(bbox))}"
        if self.cache:
            cached_data = self.cache.get_osm_data(bbox, features, None)
            if cached_data is not None:
                self.logger.info("Using cached current data")
                current_data = cached_data
            else:
                current_data = self.collect_data(bbox, features, None)
                if current_data is not None and not current_data.empty:
                    self.cache.save_osm_data(current_data, bbox, features, None)
        else:
            current_data = self.collect_data(bbox, features, None)
        
        if current_data is None or current_data.empty:
            self.logger.warning("No current data collected - creating empty datasets")
            for year in years:
                historical_data[year] = gpd.GeoDataFrame(columns=['osm_id', 'osm_type', 'geometry'])
            return historical_data
        
        # Simulate historical data by creating variations of current data
        # This is for demonstration - real implementation would use OSM history
        for i, year in enumerate(sorted(years)):
            self.logger.info(f"Creating simulated data for year {year}")
            
            if year == max(years):
                # Latest year gets full current data
                historical_data[year] = current_data.copy()
            else:
                # Earlier years get progressively smaller subsets
                sample_ratio = 0.3 + (i / len(years)) * 0.7  # 30% to 100%
                sample_size = max(1, int(len(current_data) * sample_ratio))
                
                if sample_size < len(current_data):
                    sampled_data = current_data.sample(n=sample_size, random_state=year).copy()
                else:
                    sampled_data = current_data.copy()
                
                historical_data[year] = sampled_data
            
            self.logger.log_data_collection(year, len(historical_data[year]))
        
        return historical_data
    
    def collect_data(self, bbox: Tuple[float, float, float, float],
                    features: List[str], date_filter: Optional[str] = None) -> Optional[gpd.GeoDataFrame]:
        """
        Collect OSM data for a specific time period with automatic area optimization.
        
        Args:
            bbox: Bounding box (south, west, north, east)
            features: List of OSM features to collect
            date_filter: Optional date filter for historical data
            
        Returns:
            GeoDataFrame with collected data or None if failed
        """
        start_time = time.time()
        
        # Check cache first
        if self.cache:
            cached_data = self.cache.get_osm_data(bbox, features, date_filter)
            if cached_data is not None:
                self.logger.info("Using cached OSM data")
                return cached_data
        
        # Estimate query complexity and split if needed
        complexity = estimate_query_complexity(bbox, features)
        self.logger.info(f"Query complexity score: {complexity}")
        
        if complexity > 1500:  # High complexity threshold
            self.logger.info("High complexity query detected, splitting area...")
            result = self._collect_data_chunked(bbox, features, date_filter)
        else:
            result = self._collect_data_single(bbox, features, date_filter)
        
        duration = time.time() - start_time
        self.logger.log_processing_step(f"data collection for {len(features)} features", duration)
        
        return result
    
    def _collect_data_single(self, bbox: Tuple[float, float, float, float], 
                           features: List[str], date_filter: Optional[str] = None) -> Optional[gpd.GeoDataFrame]:
        """Collect data for a single bounding box with optimized query."""
        # Generate optimized Overpass query
        query = optimize_overpass_query(bbox[0], bbox[1], bbox[2], bbox[3], features, date_filter)
        
        # Make API request
        response = self._make_overpass_request(query)
        
        if response is None:
            return None
        
        # Parse elements
        elements = response.get('elements', [])
        if not elements:
            self.logger.warning("No elements returned from Overpass API")
            return gpd.GeoDataFrame(columns=['osm_id', 'osm_type', 'geometry'])
        
        gdf = self._parse_osm_elements(elements)
        
        # Cache the result
        if self.cache and gdf is not None and not gdf.empty:
            self.cache.save_osm_data(gdf, bbox, features, date_filter)
        
        return gdf
    
    def _collect_data_chunked(self, bbox: Tuple[float, float, float, float], 
                            features: List[str], date_filter: Optional[str] = None) -> Optional[gpd.GeoDataFrame]:
        """Collect data by splitting large areas into smaller chunks."""
        # Split the bounding box into smaller areas
        sub_bboxes = split_large_bbox(bbox, max_area_km2=50.0)  # 50 km² chunks
        self.logger.info(f"Split area into {len(sub_bboxes)} chunks")
        
        all_data = []
        successful_chunks = 0
        
        for i, sub_bbox in enumerate(sub_bboxes):
            self.logger.info(f"Processing chunk {i+1}/{len(sub_bboxes)}")
            
            try:
                chunk_data = self._collect_data_single(sub_bbox, features, date_filter)
                if chunk_data is not None and not chunk_data.empty:
                    all_data.append(chunk_data)
                    successful_chunks += 1
                
                # Rate limiting between chunks
                time.sleep(1.5)  # Slightly longer delay for chunked requests
                
            except Exception as e:
                self.logger.warning(f"Failed to collect data for chunk {i+1}: {e}")
                continue
        
        if not all_data:
            self.logger.error("No data collected from any chunks")
            return None
        
        # Combine all chunks
        try:
            combined_gdf = gpd.pd.concat(all_data, ignore_index=True)
            
            # Remove duplicates based on OSM ID
            if 'osm_id' in combined_gdf.columns:
                combined_gdf = combined_gdf.drop_duplicates(subset=['osm_id'], keep='first')
            
            self.logger.info(f"Successfully combined data from {successful_chunks}/{len(sub_bboxes)} chunks")
            self.logger.info(f"Total features collected: {len(combined_gdf)}")
            
            # Cache the combined result
            if self.cache and not combined_gdf.empty:
                self.cache.save_osm_data(combined_gdf, bbox, features, date_filter)
            
            return combined_gdf
            
        except Exception as e:
            self.logger.error(f"Error combining chunked data: {e}")
            return None
    
    def collect_buildings(self, bbox: Tuple[float, float, float, float],
                         date_filter: Optional[str] = None) -> gpd.GeoDataFrame:
        """
        Collect building data specifically.
        
        Args:
            bbox: Bounding box (south, west, north, east)
            date_filter: Optional date filter for historical data
            
        Returns:
            GeoDataFrame with building polygons
        """
        building_features = [
            "building",
            "building=yes",
            "building=house",
            "building=apartments",
            "building=commercial",
            "building=industrial"
        ]
        
        data = self.collect_data(bbox, building_features, date_filter)
        
        if data is not None and not data.empty:
            # Filter to only polygon geometries (buildings should be polygons)
            buildings = data[data.geometry.type == 'Polygon'].copy()
            
            # Add building-specific processing
            if 'building' not in buildings.columns:
                buildings['building'] = 'yes'
            
            return buildings
        
        return gpd.GeoDataFrame(columns=['osm_id', 'osm_type', 'geometry', 'building'])
    
    def collect_roads(self, bbox: Tuple[float, float, float, float],
                     date_filter: Optional[str] = None) -> gpd.GeoDataFrame:
        """
        Collect road data specifically.
        
        Args:
            bbox: Bounding box (south, west, north, east)
            date_filter: Optional date filter for historical data
            
        Returns:
            GeoDataFrame with road linestrings
        """
        road_features = [
            "highway",
            "highway=primary",
            "highway=secondary", 
            "highway=tertiary",
            "highway=residential",
            "highway=service",
            "highway=track"
        ]
        
        data = self.collect_data(bbox, road_features, date_filter)
        
        if data is not None and not data.empty:
            # Filter to only linestring geometries (roads should be linestrings)
            roads = data[data.geometry.type == 'LineString'].copy()
            
            # Add road-specific processing
            if 'highway' not in roads.columns:
                roads['highway'] = 'unclassified'
            
            return roads
        
        return gpd.GeoDataFrame(columns=['osm_id', 'osm_type', 'geometry', 'highway'])
    
    def collect_landuse(self, bbox: Tuple[float, float, float, float],
                       date_filter: Optional[str] = None) -> gpd.GeoDataFrame:
        """
        Collect landuse data specifically.
        
        Args:
            bbox: Bounding box (south, west, north, east)
            date_filter: Optional date filter for historical data
            
        Returns:
            GeoDataFrame with landuse polygons
        """
        landuse_features = [
            "landuse",
            "landuse=residential",
            "landuse=commercial",
            "landuse=industrial", 
            "landuse=forest",
            "landuse=farmland",
            "amenity"
        ]
        
        data = self.collect_data(bbox, landuse_features, date_filter)
        
        if data is not None and not data.empty:
            # Filter to only polygon geometries
            landuse = data[data.geometry.type == 'Polygon'].copy()
            
            # Add landuse-specific processing
            if 'landuse' not in landuse.columns and 'amenity' not in landuse.columns:
                landuse['landuse'] = 'unknown'
            
            return landuse
        
        return gpd.GeoDataFrame(columns=['osm_id', 'osm_type', 'geometry', 'landuse'])
    
    def get_data_summary(self, data: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Get summary statistics for collected data.
        
        Args:
            data: GeoDataFrame with OSM data
            
        Returns:
            Dictionary with summary statistics
        """
        if data.empty:
            return {"total_features": 0}
        
        summary = {
            "total_features": len(data),
            "geometry_types": data.geometry.type.value_counts().to_dict(),
            "bbox": data.total_bounds.tolist(),
            "crs": str(data.crs)
        }
        
        # Add tag-specific summaries
        if 'building' in data.columns:
            summary['building_types'] = data['building'].value_counts().head(10).to_dict()
        
        if 'highway' in data.columns:
            summary['highway_types'] = data['highway'].value_counts().head(10).to_dict()
        
        if 'landuse' in data.columns:
            summary['landuse_types'] = data['landuse'].value_counts().head(10).to_dict()
        
        return summary
