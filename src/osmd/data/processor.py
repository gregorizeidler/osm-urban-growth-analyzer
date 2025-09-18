"""Data processing module for cleaning and preparing OSM data for analysis."""

import pandas as pd
import geopandas as gpd
from typing import Dict, List, Optional, Tuple, Any
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
import numpy as np

from ..utils import (
    Logger, normalize_osm_tags, calculate_area, 
    classify_building_types, create_analysis_grid
)


class DataProcessor:
    """Processes and cleans OSM data for urban growth analysis."""
    
    def __init__(self):
        """Initialize data processor."""
        self.logger = Logger("DataProcessor")
    
    def clean_geometries(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Clean and validate geometries in GeoDataFrame.
        
        Args:
            gdf: Input GeoDataFrame
            
        Returns:
            Cleaned GeoDataFrame
        """
        if gdf.empty:
            return gdf
        
        original_count = len(gdf)
        
        # Remove invalid geometries
        gdf = gdf[gdf.geometry.is_valid].copy()
        
        # Remove empty geometries
        gdf = gdf[~gdf.geometry.is_empty].copy()
        
        # Remove null geometries
        gdf = gdf[gdf.geometry.notna()].copy()
        
        # Fix any remaining geometry issues
        try:
            gdf['geometry'] = gdf.geometry.buffer(0)  # Fix self-intersections
        except Exception as e:
            self.logger.warning(f"Error fixing geometries: {e}")
        
        cleaned_count = len(gdf)
        removed_count = original_count - cleaned_count
        
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} invalid geometries ({removed_count/original_count*100:.1f}%)")
        
        return gdf
    
    def normalize_tags(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Normalize OSM tags for consistent analysis.
        
        Args:
            gdf: Input GeoDataFrame with OSM tags
            
        Returns:
            GeoDataFrame with normalized tags
        """
        if gdf.empty:
            return gdf
        
        normalized_gdf = gdf.copy()
        
        # Get all tag columns (exclude geometry and metadata columns)
        metadata_cols = {'osm_id', 'osm_type', 'geometry'}
        tag_columns = [col for col in gdf.columns if col not in metadata_cols]
        
        # Normalize each tag column
        for col in tag_columns:
            if col in normalized_gdf.columns:
                normalized_gdf[col] = normalized_gdf[col].astype(str).str.lower().str.strip()
                
                # Handle common variations
                if col == 'building':
                    normalized_gdf[col] = normalized_gdf[col].replace({
                        'true': 'yes',
                        '1': 'yes',
                        'nan': None
                    })
                elif col == 'highway':
                    normalized_gdf[col] = normalized_gdf[col].replace({
                        'road': 'unclassified',
                        'street': 'unclassified',
                        'nan': None
                    })
        
        return normalized_gdf
    
    def filter_by_area(self, gdf: gpd.GeoDataFrame, 
                      min_area_m2: float = 10.0,
                      max_area_m2: Optional[float] = None) -> gpd.GeoDataFrame:
        """
        Filter features by area (for polygon geometries).
        
        Args:
            gdf: Input GeoDataFrame
            min_area_m2: Minimum area in square meters
            max_area_m2: Optional maximum area in square meters
            
        Returns:
            Filtered GeoDataFrame
        """
        if gdf.empty:
            return gdf
        
        # Only apply to polygon geometries
        polygon_mask = gdf.geometry.type == 'Polygon'
        if not polygon_mask.any():
            return gdf
        
        # Calculate areas
        areas = gdf.loc[polygon_mask, 'geometry'].apply(calculate_area)
        
        # Apply filters
        area_filter = areas >= min_area_m2
        if max_area_m2:
            area_filter &= (areas <= max_area_m2)
        
        # Create filtered dataframe
        filtered_gdf = gdf.copy()
        filtered_gdf.loc[polygon_mask & ~area_filter, 'geometry'] = None
        filtered_gdf = filtered_gdf.dropna(subset=['geometry'])
        
        removed_count = polygon_mask.sum() - len(filtered_gdf[filtered_gdf.geometry.type == 'Polygon'])
        if removed_count > 0:
            self.logger.info(f"Filtered out {removed_count} features by area")
        
        return filtered_gdf
    
    def remove_duplicates(self, gdf: gpd.GeoDataFrame, 
                         tolerance: float = 0.001) -> gpd.GeoDataFrame:
        """
        Remove duplicate geometries based on spatial proximity.
        
        Args:
            gdf: Input GeoDataFrame
            tolerance: Spatial tolerance for duplicate detection (degrees)
            
        Returns:
            GeoDataFrame with duplicates removed
        """
        if gdf.empty or len(gdf) <= 1:
            return gdf
        
        original_count = len(gdf)
        
        # Create spatial index for efficient querying
        try:
            # Simple approach: buffer geometries and check for overlaps
            buffered = gdf.geometry.buffer(tolerance)
            
            # Find overlapping geometries
            duplicates = set()
            
            for i in range(len(gdf)):
                if i in duplicates:
                    continue
                    
                for j in range(i + 1, len(gdf)):
                    if j in duplicates:
                        continue
                    
                    if buffered.iloc[i].intersects(buffered.iloc[j]):
                        # Keep the one with more attributes or the first one
                        if gdf.iloc[i].count() >= gdf.iloc[j].count():
                            duplicates.add(j)
                        else:
                            duplicates.add(i)
                            break
            
            # Remove duplicates
            keep_indices = [i for i in range(len(gdf)) if i not in duplicates]
            deduplicated_gdf = gdf.iloc[keep_indices].copy()
            
            removed_count = original_count - len(deduplicated_gdf)
            if removed_count > 0:
                self.logger.info(f"Removed {removed_count} duplicate features")
            
            return deduplicated_gdf
            
        except Exception as e:
            self.logger.warning(f"Error removing duplicates: {e}")
            return gdf
    
    def process_buildings(self, buildings_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Process building data specifically.
        
        Args:
            buildings_gdf: GeoDataFrame with building polygons
            
        Returns:
            Processed buildings GeoDataFrame
        """
        if buildings_gdf.empty:
            return buildings_gdf
        
        self.logger.info(f"Processing {len(buildings_gdf)} buildings")
        
        # Clean geometries
        processed = self.clean_geometries(buildings_gdf)
        
        # Normalize tags
        processed = self.normalize_tags(processed)
        
        # Filter by minimum area (remove very small buildings, likely errors)
        processed = self.filter_by_area(processed, min_area_m2=10.0, max_area_m2=1_000_000.0)
        
        # Remove duplicates
        processed = self.remove_duplicates(processed)
        
        # Classify building types
        processed = classify_building_types(processed)
        
        # Calculate building areas
        processed['area_m2'] = processed.geometry.apply(calculate_area)
        
        # Estimate building levels if not present
        if 'building:levels' not in processed.columns:
            processed['building:levels'] = None
        
        # Convert levels to numeric, estimate if missing
        processed['levels'] = pd.to_numeric(processed['building:levels'], errors='coerce')
        processed['levels'] = processed['levels'].fillna(1)  # Default to 1 level
        
        # Calculate estimated floor area
        processed['floor_area_m2'] = processed['area_m2'] * processed['levels']
        
        self.logger.info(f"Processed buildings: {len(processed)} remaining")
        
        return processed
    
    def process_roads(self, roads_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Process road data specifically.
        
        Args:
            roads_gdf: GeoDataFrame with road linestrings
            
        Returns:
            Processed roads GeoDataFrame
        """
        if roads_gdf.empty:
            return roads_gdf
        
        self.logger.info(f"Processing {len(roads_gdf)} roads")
        
        # Clean geometries
        processed = self.clean_geometries(roads_gdf)
        
        # Normalize tags
        processed = self.normalize_tags(processed)
        
        # Filter by minimum length (remove very short segments, likely errors)
        if not processed.empty:
            processed['length_m'] = processed.geometry.length * 111319.9  # rough conversion to meters
            processed = processed[processed['length_m'] >= 10.0].copy()
        
        # Remove duplicates
        processed = self.remove_duplicates(processed, tolerance=0.0001)
        
        # Classify road types
        if 'highway' in processed.columns:
            processed['road_class'] = processed['highway'].map({
                'motorway': 'major',
                'trunk': 'major', 
                'primary': 'major',
                'secondary': 'arterial',
                'tertiary': 'arterial',
                'residential': 'local',
                'service': 'service',
                'track': 'track',
                'footway': 'pedestrian',
                'cycleway': 'bicycle'
            }).fillna('other')
        else:
            processed['road_class'] = 'other'
        
        self.logger.info(f"Processed roads: {len(processed)} remaining")
        
        return processed
    
    def process_landuse(self, landuse_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Process landuse data specifically.
        
        Args:
            landuse_gdf: GeoDataFrame with landuse polygons
            
        Returns:
            Processed landuse GeoDataFrame
        """
        if landuse_gdf.empty:
            return landuse_gdf
        
        self.logger.info(f"Processing {len(landuse_gdf)} landuse features")
        
        # Clean geometries
        processed = self.clean_geometries(landuse_gdf)
        
        # Normalize tags
        processed = self.normalize_tags(processed)
        
        # Filter by minimum area
        processed = self.filter_by_area(processed, min_area_m2=100.0)
        
        # Remove duplicates
        processed = self.remove_duplicates(processed)
        
        # Classify landuse types
        landuse_categories = {
            'residential': 'residential',
            'commercial': 'commercial', 
            'industrial': 'industrial',
            'retail': 'commercial',
            'forest': 'natural',
            'farmland': 'agricultural',
            'grass': 'natural',
            'meadow': 'natural',
            'park': 'recreational',
            'playground': 'recreational',
            'cemetery': 'other',
            'construction': 'construction'
        }
        
        if 'landuse' in processed.columns:
            processed['landuse_category'] = processed['landuse'].map(landuse_categories).fillna('other')
        else:
            processed['landuse_category'] = 'other'
        
        # Calculate areas
        processed['area_m2'] = processed.geometry.apply(calculate_area)
        
        self.logger.info(f"Processed landuse: {len(processed)} remaining")
        
        return processed
    
    def create_temporal_comparison(self, 
                                  data_by_year: Dict[int, gpd.GeoDataFrame]) -> Dict[str, Any]:
        """
        Create temporal comparison analysis between years.
        
        Args:
            data_by_year: Dictionary mapping years to GeoDataFrames
            
        Returns:
            Dictionary with comparison results
        """
        if not data_by_year or len(data_by_year) < 2:
            return {}
        
        years = sorted(data_by_year.keys())
        comparison = {
            'years': years,
            'feature_counts': {},
            'area_changes': {},
            'new_features': {},
            'removed_features': {}
        }
        
        # Count features by year
        for year in years:
            gdf = data_by_year[year]
            comparison['feature_counts'][year] = len(gdf) if not gdf.empty else 0
        
        # Compare consecutive years
        for i in range(1, len(years)):
            prev_year = years[i-1]
            curr_year = years[i]
            
            prev_data = data_by_year[prev_year]
            curr_data = data_by_year[curr_year]
            
            if prev_data.empty and curr_data.empty:
                continue
            
            # Calculate feature count changes
            prev_count = len(prev_data) if not prev_data.empty else 0
            curr_count = len(curr_data) if not curr_data.empty else 0
            
            comparison['feature_counts'][f'{prev_year}_to_{curr_year}'] = {
                'change': curr_count - prev_count,
                'percent_change': ((curr_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
            }
            
            # Calculate area changes (for polygon features)
            if not prev_data.empty and not curr_data.empty:
                prev_polygons = prev_data[prev_data.geometry.type == 'Polygon']
                curr_polygons = curr_data[curr_data.geometry.type == 'Polygon']
                
                if not prev_polygons.empty and not curr_polygons.empty:
                    prev_area = prev_polygons.geometry.apply(calculate_area).sum()
                    curr_area = curr_polygons.geometry.apply(calculate_area).sum()
                    
                    comparison['area_changes'][f'{prev_year}_to_{curr_year}'] = {
                        'prev_area_m2': prev_area,
                        'curr_area_m2': curr_area,
                        'change_m2': curr_area - prev_area,
                        'percent_change': ((curr_area - prev_area) / prev_area * 100) if prev_area > 0 else 0
                    }
        
        return comparison
    
    def aggregate_by_grid(self, gdf: gpd.GeoDataFrame, 
                         bbox: Tuple[float, float, float, float],
                         grid_size_km: float = 1.0) -> gpd.GeoDataFrame:
        """
        Aggregate features by spatial grid.
        
        Args:
            gdf: Input GeoDataFrame
            bbox: Bounding box for grid creation
            grid_size_km: Grid cell size in kilometers
            
        Returns:
            GeoDataFrame with aggregated statistics by grid cell
        """
        if gdf.empty:
            return gpd.GeoDataFrame()
        
        # Create analysis grid
        grid = create_analysis_grid(bbox, grid_size_km)
        
        # Perform spatial join
        joined = gpd.sjoin(gdf, grid, how='inner', predicate='intersects')
        
        # Aggregate statistics by grid cell
        aggregated = []
        
        for grid_id in grid['grid_id'].unique():
            grid_features = joined[joined['grid_id'] == grid_id]
            grid_geom = grid[grid['grid_id'] == grid_id]['geometry'].iloc[0]
            
            if not grid_features.empty:
                stats = {
                    'grid_id': grid_id,
                    'geometry': grid_geom,
                    'feature_count': len(grid_features),
                    'feature_density': len(grid_features) / (grid_size_km ** 2)
                }
                
                # Add geometry-specific stats
                if 'area_m2' in grid_features.columns:
                    stats['total_area_m2'] = grid_features['area_m2'].sum()
                    stats['avg_area_m2'] = grid_features['area_m2'].mean()
                
                if 'length_m' in grid_features.columns:
                    stats['total_length_m'] = grid_features['length_m'].sum()
                
                aggregated.append(stats)
        
        return gpd.GeoDataFrame(aggregated, crs='EPSG:4326') if aggregated else gpd.GeoDataFrame()
    
    def get_processing_summary(self, 
                              original_data: gpd.GeoDataFrame,
                              processed_data: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Get summary of processing operations.
        
        Args:
            original_data: Original GeoDataFrame before processing
            processed_data: Processed GeoDataFrame
            
        Returns:
            Dictionary with processing summary
        """
        original_count = len(original_data) if not original_data.empty else 0
        processed_count = len(processed_data) if not processed_data.empty else 0
        
        summary = {
            'original_features': original_count,
            'processed_features': processed_count,
            'removed_features': original_count - processed_count,
            'removal_rate': ((original_count - processed_count) / original_count * 100) if original_count > 0 else 0
        }
        
        if not processed_data.empty:
            summary['geometry_types'] = processed_data.geometry.type.value_counts().to_dict()
            summary['bbox'] = processed_data.total_bounds.tolist()
        
        return summary
