"""Spatial analysis module for urban growth pattern detection."""

import numpy as np
import pandas as pd
import geopandas as gpd
from typing import Dict, List, Tuple, Any, Optional
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import unary_union, voronoi_diagram
from scipy.spatial.distance import cdist
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.cluster import DBSCAN
import math

from ..utils import create_analysis_grid, calculate_area


class SpatialAnalyzer:
    """Performs spatial analysis for urban growth patterns."""
    
    def __init__(self):
        """Initialize spatial analyzer."""
        pass
    
    def detect_growth_hotspots(self, 
                             buildings_by_year: Dict[int, gpd.GeoDataFrame],
                             grid_size_km: float = 1.0,
                             bbox: Optional[Tuple[float, float, float, float]] = None) -> Dict[str, Any]:
        """
        Detect urban growth hotspots using spatial grid analysis.
        
        Args:
            buildings_by_year: Dictionary mapping years to building GeoDataFrames
            grid_size_km: Grid cell size in kilometers
            bbox: Optional bounding box for analysis
            
        Returns:
            Dictionary with hotspot analysis results
        """
        if not buildings_by_year or len(buildings_by_year) < 2:
            return {}
        
        years = sorted(buildings_by_year.keys())
        
        # Determine bounding box if not provided
        if bbox is None:
            all_bounds = []
            for gdf in buildings_by_year.values():
                if not gdf.empty:
                    all_bounds.append(gdf.total_bounds)
            
            if all_bounds:
                all_bounds = np.array(all_bounds)
                bbox = (
                    all_bounds[:, 1].min(),  # west (min x)
                    all_bounds[:, 0].min(),  # south (min y)
                    all_bounds[:, 3].max(),  # east (max x)
                    all_bounds[:, 2].max()   # north (max y)
                )
            else:
                return {}
        
        # Create analysis grid
        grid = create_analysis_grid(bbox, grid_size_km)
        
        # Calculate building density for each year and grid cell
        grid_densities = {}
        
        for year in years:
            buildings = buildings_by_year[year]
            
            if buildings.empty:
                # All grid cells have zero density
                year_densities = pd.Series(0.0, index=grid['grid_id'])
            else:
                # Spatial join buildings with grid
                joined = gpd.sjoin(buildings, grid, how='inner', predicate='intersects')
                
                # Count buildings per grid cell
                building_counts = joined.groupby('grid_id').size()
                
                # Calculate density (buildings per km²)
                grid_area_km2 = grid_size_km ** 2
                year_densities = building_counts / grid_area_km2
                
                # Fill missing grid cells with zero
                year_densities = year_densities.reindex(grid['grid_id'], fill_value=0.0)
            
            grid_densities[year] = year_densities
        
        # Calculate growth rates between consecutive years
        growth_rates = {}
        hotspots = {}
        
        for i in range(1, len(years)):
            prev_year = years[i-1]
            curr_year = years[i]
            
            prev_density = grid_densities[prev_year]
            curr_density = grid_densities[curr_year]
            
            # Calculate absolute and relative growth
            absolute_growth = curr_density - prev_density
            relative_growth = ((curr_density - prev_density) / prev_density * 100).fillna(0)
            relative_growth = relative_growth.replace([np.inf, -np.inf], 0)
            
            period_key = f"{prev_year}-{curr_year}"
            growth_rates[period_key] = {
                'absolute_growth': absolute_growth,
                'relative_growth': relative_growth
            }
            
            # Identify hotspots (top 20% by absolute growth)
            growth_threshold = absolute_growth.quantile(0.8)
            hotspot_cells = absolute_growth[absolute_growth >= growth_threshold].index
            
            # Create hotspot GeoDataFrame
            hotspot_grid = grid[grid['grid_id'].isin(hotspot_cells)].copy()
            hotspot_grid['absolute_growth'] = hotspot_grid['grid_id'].map(absolute_growth)
            hotspot_grid['relative_growth'] = hotspot_grid['grid_id'].map(relative_growth)
            
            hotspots[period_key] = hotspot_grid
        
        return {
            'grid': grid,
            'grid_densities': grid_densities,
            'growth_rates': growth_rates,
            'hotspots': hotspots,
            'grid_size_km': grid_size_km,
            'bbox': bbox
        }
    
    def analyze_urban_sprawl(self, 
                           buildings_by_year: Dict[int, gpd.GeoDataFrame],
                           center_point: Optional[Point] = None) -> Dict[str, Any]:
        """
        Analyze urban sprawl patterns and characteristics.
        
        Args:
            buildings_by_year: Dictionary mapping years to building GeoDataFrames
            center_point: Optional urban center point
            
        Returns:
            Dictionary with sprawl analysis results
        """
        if not buildings_by_year or len(buildings_by_year) < 2:
            return {}
        
        years = sorted(buildings_by_year.keys())
        sprawl_metrics = {
            'years': years,
            'urban_extent': {},
            'sprawl_indices': {},
            'distance_bands': {}
        }
        
        # Determine center point if not provided
        if center_point is None:
            all_buildings = []
            for gdf in buildings_by_year.values():
                if not gdf.empty:
                    all_buildings.append(gdf)
            
            if all_buildings:
                combined = gpd.GeoDataFrame(pd.concat(all_buildings, ignore_index=True))
                center_point = combined.geometry.centroid.unary_union.centroid
        
        if center_point is None:
            return sprawl_metrics
        
        # Analyze for each year
        for year in years:
            buildings = buildings_by_year[year]
            
            if buildings.empty:
                sprawl_metrics['urban_extent'][year] = 0.0
                sprawl_metrics['sprawl_indices'][year] = {}
                sprawl_metrics['distance_bands'][year] = {}
                continue
            
            # Calculate urban extent (area of convex hull)
            try:
                urban_boundary = buildings.geometry.unary_union.convex_hull
                urban_extent = calculate_area(urban_boundary)
                sprawl_metrics['urban_extent'][year] = urban_extent
            except:
                sprawl_metrics['urban_extent'][year] = 0.0
            
            # Calculate sprawl indices
            building_centroids = buildings.geometry.centroid
            
            # Distance from center
            distances = [center_point.distance(centroid) * 111319.9 for centroid in building_centroids]
            
            # Sprawl metrics
            sprawl_indices = {
                'mean_distance_from_center': np.mean(distances),
                'max_distance_from_center': np.max(distances),
                'std_distance_from_center': np.std(distances),
                'buildings_count': len(buildings)
            }
            
            # Calculate density gradient (buildings per distance band)
            distance_bands = self._calculate_distance_bands(distances, band_width_km=2.0)
            sprawl_indices['density_gradient'] = distance_bands
            
            sprawl_metrics['sprawl_indices'][year] = sprawl_indices
            sprawl_metrics['distance_bands'][year] = distance_bands
        
        return sprawl_metrics
    
    def _calculate_distance_bands(self, distances: List[float], 
                                band_width_km: float = 2.0) -> Dict[str, int]:
        """
        Calculate building counts by distance bands from center.
        
        Args:
            distances: List of distances from center (in meters)
            band_width_km: Width of each distance band in kilometers
            
        Returns:
            Dictionary with distance bands and building counts
        """
        if not distances:
            return {}
        
        max_distance_km = max(distances) / 1000
        num_bands = int(np.ceil(max_distance_km / band_width_km))
        
        bands = {}
        for i in range(num_bands):
            band_start = i * band_width_km
            band_end = (i + 1) * band_width_km
            
            count = sum(1 for d in distances 
                       if band_start * 1000 <= d < band_end * 1000)
            
            band_key = f"{band_start:.1f}-{band_end:.1f}km"
            bands[band_key] = count
        
        return bands
    
    def detect_building_clusters(self, buildings_gdf: gpd.GeoDataFrame,
                               eps_meters: float = 100.0,
                               min_samples: int = 5) -> gpd.GeoDataFrame:
        """
        Detect building clusters using DBSCAN algorithm.
        
        Args:
            buildings_gdf: GeoDataFrame with building polygons
            eps_meters: Maximum distance between buildings in a cluster (meters)
            min_samples: Minimum number of buildings to form a cluster
            
        Returns:
            GeoDataFrame with cluster labels added
        """
        if buildings_gdf.empty:
            return buildings_gdf
        
        # Get building centroids
        centroids = buildings_gdf.geometry.centroid
        
        # Convert to coordinate arrays
        coords = np.array([[point.x, point.y] for point in centroids])
        
        # Convert eps from meters to degrees (rough approximation)
        eps_degrees = eps_meters / 111319.9
        
        # Apply DBSCAN clustering
        clustering = DBSCAN(eps=eps_degrees, min_samples=min_samples)
        cluster_labels = clustering.fit_predict(coords)
        
        # Add cluster labels to GeoDataFrame
        result = buildings_gdf.copy()
        result['cluster_id'] = cluster_labels
        
        # Mark noise points (cluster_id = -1) as individual clusters
        result['is_clustered'] = result['cluster_id'] != -1
        
        return result
    
    def analyze_accessibility(self, buildings_gdf: gpd.GeoDataFrame,
                            roads_gdf: gpd.GeoDataFrame,
                            max_distance_m: float = 500.0) -> gpd.GeoDataFrame:
        """
        Analyze building accessibility to road network.
        
        Args:
            buildings_gdf: GeoDataFrame with building polygons
            roads_gdf: GeoDataFrame with road linestrings
            max_distance_m: Maximum distance to consider for accessibility (meters)
            
        Returns:
            GeoDataFrame with accessibility metrics added
        """
        if buildings_gdf.empty or roads_gdf.empty:
            result = buildings_gdf.copy() if not buildings_gdf.empty else gpd.GeoDataFrame()
            if not result.empty:
                result['distance_to_road_m'] = np.inf
                result['accessible'] = False
            return result
        
        # Convert distance to degrees
        max_distance_deg = max_distance_m / 111319.9
        
        # Create a unified road network
        road_network = roads_gdf.geometry.unary_union
        
        # Calculate distance from each building to nearest road
        building_centroids = buildings_gdf.geometry.centroid
        
        distances = []
        for centroid in building_centroids:
            distance_deg = centroid.distance(road_network)
            distance_m = distance_deg * 111319.9
            distances.append(distance_m)
        
        # Add accessibility metrics to buildings
        result = buildings_gdf.copy()
        result['distance_to_road_m'] = distances
        result['accessible'] = result['distance_to_road_m'] <= max_distance_m
        
        return result
    
    def calculate_fragmentation_metrics(self, 
                                      landuse_gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Calculate landscape fragmentation metrics.
        
        Args:
            landuse_gdf: GeoDataFrame with landuse polygons
            
        Returns:
            Dictionary with fragmentation metrics
        """
        if landuse_gdf.empty:
            return {}
        
        metrics = {}
        
        # Group by landuse type
        if 'landuse_category' in landuse_gdf.columns:
            landuse_col = 'landuse_category'
        elif 'landuse' in landuse_gdf.columns:
            landuse_col = 'landuse'
        else:
            return {}
        
        for landuse_type in landuse_gdf[landuse_col].unique():
            if pd.isna(landuse_type):
                continue
            
            type_polygons = landuse_gdf[landuse_gdf[landuse_col] == landuse_type]
            
            if type_polygons.empty:
                continue
            
            # Calculate fragmentation metrics for this landuse type
            type_metrics = {
                'patch_count': len(type_polygons),
                'total_area_m2': type_polygons.geometry.apply(calculate_area).sum(),
                'mean_patch_area_m2': type_polygons.geometry.apply(calculate_area).mean(),
                'largest_patch_area_m2': type_polygons.geometry.apply(calculate_area).max()
            }
            
            # Calculate patch density (patches per km²)
            if 'total_area_m2' in type_metrics and type_metrics['total_area_m2'] > 0:
                total_area_km2 = type_metrics['total_area_m2'] / 1_000_000
                type_metrics['patch_density_per_km2'] = type_metrics['patch_count'] / total_area_km2
            else:
                type_metrics['patch_density_per_km2'] = 0.0
            
            # Calculate edge density (perimeter to area ratio)
            perimeters = type_polygons.geometry.length * 111319.9  # Convert to meters
            type_metrics['total_edge_length_m'] = perimeters.sum()
            
            if type_metrics['total_area_m2'] > 0:
                type_metrics['edge_density'] = type_metrics['total_edge_length_m'] / type_metrics['total_area_m2']
            else:
                type_metrics['edge_density'] = 0.0
            
            metrics[landuse_type] = type_metrics
        
        return metrics
    
    def analyze_connectivity(self, buildings_gdf: gpd.GeoDataFrame,
                           roads_gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Analyze urban connectivity patterns.
        
        Args:
            buildings_gdf: GeoDataFrame with building polygons
            roads_gdf: GeoDataFrame with road linestrings
            
        Returns:
            Dictionary with connectivity metrics
        """
        if buildings_gdf.empty and roads_gdf.empty:
            return {}
        
        connectivity_metrics = {}
        
        # Road network connectivity
        if not roads_gdf.empty:
            # Calculate total road length
            total_road_length = roads_gdf.geometry.length.sum() * 111319.9  # Convert to meters
            
            # Calculate road density (simplified)
            if not buildings_gdf.empty:
                # Use building area as proxy for urban area
                urban_area_m2 = buildings_gdf.geometry.apply(calculate_area).sum()
                urban_area_km2 = urban_area_m2 / 1_000_000
                
                if urban_area_km2 > 0:
                    road_density = (total_road_length / 1000) / urban_area_km2  # km of road per km²
                else:
                    road_density = 0.0
            else:
                road_density = 0.0
            
            connectivity_metrics['road_network'] = {
                'total_length_km': total_road_length / 1000,
                'segment_count': len(roads_gdf),
                'road_density_km_per_km2': road_density,
                'average_segment_length_m': total_road_length / len(roads_gdf) if len(roads_gdf) > 0 else 0
            }
        
        # Building connectivity (simplified)
        if not buildings_gdf.empty:
            # Calculate building clusters
            clustered_buildings = self.detect_building_clusters(buildings_gdf)
            
            cluster_counts = clustered_buildings['cluster_id'].value_counts()
            # Remove noise (-1 cluster)
            valid_clusters = cluster_counts[cluster_counts.index != -1]
            
            connectivity_metrics['building_clusters'] = {
                'cluster_count': len(valid_clusters),
                'clustered_buildings': clustered_buildings['is_clustered'].sum(),
                'isolated_buildings': (~clustered_buildings['is_clustered']).sum(),
                'largest_cluster_size': valid_clusters.max() if not valid_clusters.empty else 0,
                'average_cluster_size': valid_clusters.mean() if not valid_clusters.empty else 0
            }
        
        return connectivity_metrics
