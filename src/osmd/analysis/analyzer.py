"""Main urban growth analyzer that orchestrates the analysis workflow."""

import time
import math
from typing import Dict, List, Tuple, Any, Optional
import geopandas as gpd
import pandas as pd
from pathlib import Path

from ..utils import ConfigManager, Logger, BoundingBox
from ..data import OSMDataCollector, DataProcessor, CacheManager
from .metrics import GrowthMetrics
from .spatial import SpatialAnalyzer


class UrbanGrowthAnalyzer:
    """Main analyzer class that orchestrates urban growth analysis."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize urban growth analyzer.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager or ConfigManager()
        self.logger = Logger("UrbanGrowthAnalyzer")
        
        # Initialize components
        self.data_collector = OSMDataCollector(self.config)
        self.data_processor = DataProcessor()
        self.growth_metrics = GrowthMetrics()
        self.spatial_analyzer = SpatialAnalyzer()
        
        # Initialize cache if enabled
        if self.config.is_cache_enabled():
            self.cache = CacheManager(self.config.get_cache_dir())
        else:
            self.cache = None
    
    def analyze_urban_growth(self, 
                           bbox: Optional[BoundingBox] = None,
                           years: Optional[List[int]] = None,
                           features: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive urban growth analysis.
        
        Args:
            bbox: Bounding box for analysis (uses default if None)
            years: Years to analyze (uses config default if None)
            features: OSM features to collect (uses config default if None)
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        # Use defaults from config if not provided
        if bbox is None:
            bbox = self.config.get_default_bbox()
        
        if years is None:
            years = self.config.get_comparison_years()
        
        if features is None:
            osm_features = self.config.get_osm_features()
            features = []
            for feature_list in osm_features.values():
                features.extend(feature_list)
        
        self.logger.log_analysis_start(bbox.to_tuple(), years)
        start_time = time.time()
        
        # Step 1: Collect historical data
        self.logger.info("Step 1: Collecting historical OSM data")
        historical_data = self.data_collector.collect_historical_data(
            bbox.to_tuple(), features, years
        )
        
        # Step 2: Process and clean data
        self.logger.info("Step 2: Processing and cleaning data")
        processed_data = self._process_historical_data(historical_data)
        
        # Step 3: Perform quantitative analysis
        self.logger.info("Step 3: Calculating growth metrics")
        analysis_results = self._perform_quantitative_analysis(processed_data, bbox)
        
        # Step 4: Perform spatial analysis
        self.logger.info("Step 4: Performing spatial analysis")
        spatial_results = self._perform_spatial_analysis(processed_data, bbox)
        
        # Step 5: Generate summary
        total_time = time.time() - start_time
        self.logger.log_processing_step("complete urban growth analysis", total_time)
        
        # Combine all results
        comprehensive_results = {
            'metadata': {
                'bbox': bbox.to_tuple(),
                'years': years,
                'features': features,
                'analysis_date': pd.Timestamp.now().isoformat(),
                'processing_time_seconds': total_time
            },
            'data_summary': self._generate_data_summary(historical_data),
            'quantitative_analysis': analysis_results,
            'spatial_analysis': spatial_results,
            'processed_data': processed_data  # Include for visualization
        }
        
        # Cache results if caching is enabled
        if self.cache:
            analysis_id = f"analysis_{int(time.time())}"
            # Don't cache the processed_data (too large), just the results
            cacheable_results = {k: v for k, v in comprehensive_results.items() 
                               if k != 'processed_data'}
            self.cache.save_analysis_results(cacheable_results, analysis_id)
        
        return comprehensive_results
    
    def _process_historical_data(self, 
                               historical_data: Dict[int, gpd.GeoDataFrame]) -> Dict[str, Dict[int, gpd.GeoDataFrame]]:
        """
        Process historical data by feature type.
        
        Args:
            historical_data: Raw historical data by year
            
        Returns:
            Processed data organized by feature type and year
        """
        processed_data = {
            'buildings': {},
            'roads': {},
            'landuse': {}
        }
        
        for year, data in historical_data.items():
            if data.empty:
                processed_data['buildings'][year] = gpd.GeoDataFrame()
                processed_data['roads'][year] = gpd.GeoDataFrame()
                processed_data['landuse'][year] = gpd.GeoDataFrame()
                continue
            
            # Separate data by feature type
            buildings = self._extract_buildings(data)
            roads = self._extract_roads(data)
            landuse = self._extract_landuse(data)
            
            # Process each feature type
            processed_data['buildings'][year] = self.data_processor.process_buildings(buildings)
            processed_data['roads'][year] = self.data_processor.process_roads(roads)
            processed_data['landuse'][year] = self.data_processor.process_landuse(landuse)
            
            self.logger.info(f"Processed data for {year}: "
                           f"{len(processed_data['buildings'][year])} buildings, "
                           f"{len(processed_data['roads'][year])} roads, "
                           f"{len(processed_data['landuse'][year])} landuse")
        
        return processed_data
    
    def _extract_buildings(self, data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Extract building features from OSM data."""
        if data.empty:
            return gpd.GeoDataFrame()
        
        # Look for building tag
        building_mask = data.get('building', pd.Series()).notna()
        buildings = data[building_mask & (data.geometry.type == 'Polygon')].copy()
        
        return buildings
    
    def _extract_roads(self, data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Extract road features from OSM data."""
        if data.empty:
            return gpd.GeoDataFrame()
        
        # Look for highway tag
        highway_mask = data.get('highway', pd.Series()).notna()
        roads = data[highway_mask & (data.geometry.type == 'LineString')].copy()
        
        return roads
    
    def _extract_landuse(self, data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Extract landuse features from OSM data."""
        if data.empty:
            return gpd.GeoDataFrame()
        
        # Look for landuse or amenity tags
        landuse_mask = (data.get('landuse', pd.Series()).notna() | 
                       data.get('amenity', pd.Series()).notna())
        landuse = data[landuse_mask & (data.geometry.type == 'Polygon')].copy()
        
        return landuse
    
    def _perform_quantitative_analysis(self, 
                                     processed_data: Dict[str, Dict[int, gpd.GeoDataFrame]],
                                     bbox: BoundingBox) -> Dict[str, Any]:
        """
        Perform quantitative growth analysis.
        
        Args:
            processed_data: Processed data by feature type and year
            bbox: Analysis bounding box
            
        Returns:
            Dictionary with quantitative analysis results
        """
        # Calculate analysis area
        analysis_area_km2 = self._calculate_analysis_area(bbox)
        
        # Calculate comprehensive metrics
        summary_stats = self.growth_metrics.calculate_summary_statistics(
            processed_data['buildings'],
            processed_data['roads'],
            analysis_area_km2
        )
        
        # Calculate landuse changes if available
        if any(not gdf.empty for gdf in processed_data['landuse'].values()):
            landuse_changes = self.growth_metrics.calculate_landuse_changes(
                processed_data['landuse']
            )
            summary_stats['landuse_changes'] = landuse_changes
        
        return summary_stats
    
    def _perform_spatial_analysis(self, 
                                processed_data: Dict[str, Dict[int, gpd.GeoDataFrame]],
                                bbox: BoundingBox) -> Dict[str, Any]:
        """
        Perform spatial growth analysis.
        
        Args:
            processed_data: Processed data by feature type and year
            bbox: Analysis bounding box
            
        Returns:
            Dictionary with spatial analysis results
        """
        spatial_results = {}
        
        # Detect growth hotspots
        if processed_data['buildings']:
            hotspots = self.spatial_analyzer.detect_growth_hotspots(
                processed_data['buildings'],
                grid_size_km=1.0,
                bbox=bbox.to_tuple()
            )
            spatial_results['growth_hotspots'] = hotspots
        
        # Analyze urban sprawl
        if processed_data['buildings']:
            sprawl_analysis = self.spatial_analyzer.analyze_urban_sprawl(
                processed_data['buildings']
            )
            spatial_results['urban_sprawl'] = sprawl_analysis
        
        # Analyze connectivity
        years = sorted(processed_data['buildings'].keys())
        if years:
            latest_year = years[-1]
            buildings = processed_data['buildings'][latest_year]
            roads = processed_data['roads'][latest_year]
            
            if not buildings.empty or not roads.empty:
                connectivity = self.spatial_analyzer.analyze_connectivity(buildings, roads)
                spatial_results['connectivity'] = connectivity
        
        # Analyze fragmentation for landuse
        if processed_data['landuse'] and years:
            latest_landuse = processed_data['landuse'][years[-1]]
            if not latest_landuse.empty:
                fragmentation = self.spatial_analyzer.calculate_fragmentation_metrics(latest_landuse)
                spatial_results['fragmentation'] = fragmentation
        
        return spatial_results
    
    def _calculate_analysis_area(self, bbox: BoundingBox) -> float:
        """
        Calculate analysis area in square kilometers.
        
        Args:
            bbox: Bounding box
            
        Returns:
            Area in square kilometers
        """
        # Rough calculation using bounding box
        lat_diff = bbox.north - bbox.south
        lon_diff = bbox.east - bbox.west
        
        # Convert to approximate kilometers
        lat_km = lat_diff * 111.32  # 1 degree lat ≈ 111.32 km
        lon_km = lon_diff * 111.32 * abs(math.cos(math.radians((bbox.north + bbox.south) / 2)))
        
        return lat_km * lon_km
    
    def _generate_data_summary(self, 
                             historical_data: Dict[int, gpd.GeoDataFrame]) -> Dict[str, Any]:
        """
        Generate summary of collected data.
        
        Args:
            historical_data: Historical data by year
            
        Returns:
            Dictionary with data summary
        """
        summary = {
            'years_analyzed': sorted(historical_data.keys()),
            'data_by_year': {}
        }
        
        for year, data in historical_data.items():
            year_summary = {
                'total_features': len(data) if not data.empty else 0,
                'geometry_types': data.geometry.type.value_counts().to_dict() if not data.empty else {},
                'feature_tags': {}
            }
            
            # Count common tags
            if not data.empty:
                for tag in ['building', 'highway', 'landuse', 'amenity']:
                    if tag in data.columns:
                        tag_counts = data[tag].value_counts().head(5).to_dict()
                        year_summary['feature_tags'][tag] = tag_counts
            
            summary['data_by_year'][year] = year_summary
        
        return summary
    
    def analyze_specific_area(self, 
                            bbox: BoundingBox,
                            years: List[int],
                            feature_types: List[str] = None) -> Dict[str, Any]:
        """
        Analyze a specific area with custom parameters.
        
        Args:
            bbox: Custom bounding box
            years: Custom year list
            feature_types: Specific feature types to analyze
            
        Returns:
            Analysis results for the specific area
        """
        if feature_types is None:
            feature_types = ['buildings', 'roads', 'landuse']
        
        # Build feature list based on types
        features = []
        osm_features = self.config.get_osm_features()
        
        for feature_type in feature_types:
            if feature_type == 'buildings':
                features.extend(osm_features.get('buildings', ['building']))
            elif feature_type == 'roads':
                features.extend(osm_features.get('roads', ['highway']))
            elif feature_type == 'landuse':
                features.extend(osm_features.get('landuse', ['landuse']))
        
        return self.analyze_urban_growth(bbox, years, features)
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache usage statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if self.cache:
            return self.cache.get_cache_stats()
        else:
            return {"cache_enabled": False}
    
    def clear_cache(self, cache_type: Optional[str] = None) -> int:
        """
        Clear analysis cache.
        
        Args:
            cache_type: Specific cache type to clear
            
        Returns:
            Number of files deleted
        """
        if self.cache:
            return self.cache.clear_cache(cache_type)
        else:
            return 0
