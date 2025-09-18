"""Growth metrics calculation module for urban development analysis."""

import numpy as np
import pandas as pd
import geopandas as gpd
from typing import Dict, List, Tuple, Any, Optional
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
import math

from ..utils import calculate_area, calculate_building_density, calculate_road_density


class GrowthMetrics:
    """Calculates various urban growth metrics and indicators."""
    
    def __init__(self):
        """Initialize growth metrics calculator."""
        pass
    
    def calculate_building_growth(self, 
                                buildings_by_year: Dict[int, gpd.GeoDataFrame]) -> Dict[str, Any]:
        """
        Calculate building growth metrics across years.
        
        Args:
            buildings_by_year: Dictionary mapping years to building GeoDataFrames
            
        Returns:
            Dictionary with building growth metrics
        """
        if not buildings_by_year or len(buildings_by_year) < 2:
            return {}
        
        years = sorted(buildings_by_year.keys())
        metrics = {
            'years': years,
            'building_counts': {},
            'total_area_m2': {},
            'average_building_size_m2': {},
            'building_types': {},
            'growth_rates': {}
        }
        
        # Calculate metrics for each year
        for year in years:
            buildings = buildings_by_year[year]
            
            if buildings.empty:
                metrics['building_counts'][year] = 0
                metrics['total_area_m2'][year] = 0.0
                metrics['average_building_size_m2'][year] = 0.0
                metrics['building_types'][year] = {}
            else:
                # Basic counts and areas
                metrics['building_counts'][year] = len(buildings)
                
                # Calculate areas if not present
                if 'area_m2' not in buildings.columns:
                    buildings = buildings.copy()
                    buildings['area_m2'] = buildings.geometry.apply(calculate_area)
                
                metrics['total_area_m2'][year] = buildings['area_m2'].sum()
                metrics['average_building_size_m2'][year] = buildings['area_m2'].mean()
                
                # Building type distribution
                if 'building_type' in buildings.columns:
                    type_counts = buildings['building_type'].value_counts().to_dict()
                    metrics['building_types'][year] = type_counts
                else:
                    metrics['building_types'][year] = {'unknown': len(buildings)}
        
        # Calculate growth rates between consecutive years
        for i in range(1, len(years)):
            prev_year = years[i-1]
            curr_year = years[i]
            
            prev_count = metrics['building_counts'][prev_year]
            curr_count = metrics['building_counts'][curr_year]
            
            prev_area = metrics['total_area_m2'][prev_year]
            curr_area = metrics['total_area_m2'][curr_year]
            
            period_key = f"{prev_year}-{curr_year}"
            
            # Count growth rate
            count_growth = ((curr_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
            
            # Area growth rate
            area_growth = ((curr_area - prev_area) / prev_area * 100) if prev_area > 0 else 0
            
            metrics['growth_rates'][period_key] = {
                'count_growth_percent': count_growth,
                'area_growth_percent': area_growth,
                'new_buildings': curr_count - prev_count,
                'new_area_m2': curr_area - prev_area,
                'years_elapsed': curr_year - prev_year,
                'annual_count_growth_percent': count_growth / (curr_year - prev_year),
                'annual_area_growth_percent': area_growth / (curr_year - prev_year)
            }
        
        return metrics
    
    def calculate_road_growth(self, 
                            roads_by_year: Dict[int, gpd.GeoDataFrame]) -> Dict[str, Any]:
        """
        Calculate road network growth metrics across years.
        
        Args:
            roads_by_year: Dictionary mapping years to road GeoDataFrames
            
        Returns:
            Dictionary with road growth metrics
        """
        if not roads_by_year or len(roads_by_year) < 2:
            return {}
        
        years = sorted(roads_by_year.keys())
        metrics = {
            'years': years,
            'road_counts': {},
            'total_length_km': {},
            'road_density_km_per_km2': {},
            'road_types': {},
            'growth_rates': {}
        }
        
        # Calculate metrics for each year
        for year in years:
            roads = roads_by_year[year]
            
            if roads.empty:
                metrics['road_counts'][year] = 0
                metrics['total_length_km'][year] = 0.0
                metrics['road_density_km_per_km2'][year] = 0.0
                metrics['road_types'][year] = {}
            else:
                # Basic counts
                metrics['road_counts'][year] = len(roads)
                
                # Calculate lengths if not present
                if 'length_m' not in roads.columns:
                    roads = roads.copy()
                    roads['length_m'] = roads.geometry.length * 111319.9  # rough conversion
                
                total_length_m = roads['length_m'].sum()
                metrics['total_length_km'][year] = total_length_m / 1000
                
                # Road type distribution
                if 'highway' in roads.columns:
                    type_counts = roads['highway'].value_counts().to_dict()
                    metrics['road_types'][year] = type_counts
                elif 'road_class' in roads.columns:
                    type_counts = roads['road_class'].value_counts().to_dict()
                    metrics['road_types'][year] = type_counts
                else:
                    metrics['road_types'][year] = {'unknown': len(roads)}
        
        # Calculate growth rates
        for i in range(1, len(years)):
            prev_year = years[i-1]
            curr_year = years[i]
            
            prev_count = metrics['road_counts'][prev_year]
            curr_count = metrics['road_counts'][curr_year]
            
            prev_length = metrics['total_length_km'][prev_year]
            curr_length = metrics['total_length_km'][curr_year]
            
            period_key = f"{prev_year}-{curr_year}"
            
            # Count growth rate
            count_growth = ((curr_count - prev_count) / prev_count * 100) if prev_count > 0 else 0
            
            # Length growth rate
            length_growth = ((curr_length - prev_length) / prev_length * 100) if prev_length > 0 else 0
            
            metrics['growth_rates'][period_key] = {
                'count_growth_percent': count_growth,
                'length_growth_percent': length_growth,
                'new_roads': curr_count - prev_count,
                'new_length_km': curr_length - prev_length,
                'years_elapsed': curr_year - prev_year,
                'annual_count_growth_percent': count_growth / (curr_year - prev_year),
                'annual_length_growth_percent': length_growth / (curr_year - prev_year)
            }
        
        return metrics
    
    def calculate_landuse_changes(self, 
                                landuse_by_year: Dict[int, gpd.GeoDataFrame]) -> Dict[str, Any]:
        """
        Calculate land use change metrics across years.
        
        Args:
            landuse_by_year: Dictionary mapping years to landuse GeoDataFrames
            
        Returns:
            Dictionary with landuse change metrics
        """
        if not landuse_by_year or len(landuse_by_year) < 2:
            return {}
        
        years = sorted(landuse_by_year.keys())
        metrics = {
            'years': years,
            'landuse_areas_m2': {},
            'landuse_percentages': {},
            'transitions': {}
        }
        
        # Calculate landuse areas for each year
        for year in years:
            landuse = landuse_by_year[year]
            
            if landuse.empty:
                metrics['landuse_areas_m2'][year] = {}
                metrics['landuse_percentages'][year] = {}
            else:
                # Calculate areas if not present
                if 'area_m2' not in landuse.columns:
                    landuse = landuse.copy()
                    landuse['area_m2'] = landuse.geometry.apply(calculate_area)
                
                # Group by landuse category
                landuse_col = 'landuse_category' if 'landuse_category' in landuse.columns else 'landuse'
                
                if landuse_col in landuse.columns:
                    area_by_type = landuse.groupby(landuse_col)['area_m2'].sum().to_dict()
                    total_area = sum(area_by_type.values())
                    
                    metrics['landuse_areas_m2'][year] = area_by_type
                    
                    # Calculate percentages
                    if total_area > 0:
                        percentages = {k: (v / total_area * 100) for k, v in area_by_type.items()}
                        metrics['landuse_percentages'][year] = percentages
                    else:
                        metrics['landuse_percentages'][year] = {}
                else:
                    metrics['landuse_areas_m2'][year] = {}
                    metrics['landuse_percentages'][year] = {}
        
        # Calculate transitions between consecutive years
        for i in range(1, len(years)):
            prev_year = years[i-1]
            curr_year = years[i]
            
            prev_areas = metrics['landuse_areas_m2'][prev_year]
            curr_areas = metrics['landuse_areas_m2'][curr_year]
            
            period_key = f"{prev_year}-{curr_year}"
            transitions = {}
            
            # Find all unique landuse types
            all_types = set(prev_areas.keys()) | set(curr_areas.keys())
            
            for landuse_type in all_types:
                prev_area = prev_areas.get(landuse_type, 0)
                curr_area = curr_areas.get(landuse_type, 0)
                
                change = curr_area - prev_area
                percent_change = (change / prev_area * 100) if prev_area > 0 else 0
                
                transitions[landuse_type] = {
                    'prev_area_m2': prev_area,
                    'curr_area_m2': curr_area,
                    'change_m2': change,
                    'percent_change': percent_change
                }
            
            metrics['transitions'][period_key] = transitions
        
        return metrics
    
    def calculate_density_metrics(self, 
                                buildings_gdf: gpd.GeoDataFrame,
                                roads_gdf: gpd.GeoDataFrame,
                                analysis_area_km2: float) -> Dict[str, Any]:
        """
        Calculate urban density metrics.
        
        Args:
            buildings_gdf: GeoDataFrame with buildings
            roads_gdf: GeoDataFrame with roads
            analysis_area_km2: Total analysis area in square kilometers
            
        Returns:
            Dictionary with density metrics
        """
        metrics = {}
        
        # Building density metrics
        if not buildings_gdf.empty and analysis_area_km2 > 0:
            building_density = calculate_building_density(buildings_gdf, analysis_area_km2)
            metrics.update(building_density)
        else:
            metrics.update({
                "buildings_per_km2": 0.0,
                "building_coverage_ratio": 0.0,
                "avg_building_area_m2": 0.0
            })
        
        # Road density metrics
        if not roads_gdf.empty and analysis_area_km2 > 0:
            road_density = calculate_road_density(roads_gdf, analysis_area_km2)
            metrics.update(road_density)
        else:
            metrics.update({
                "road_length_km_per_km2": 0.0,
                "total_road_length_km": 0.0
            })
        
        return metrics
    
    def calculate_compactness_metrics(self, buildings_gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Calculate urban compactness and form metrics.
        
        Args:
            buildings_gdf: GeoDataFrame with building polygons
            
        Returns:
            Dictionary with compactness metrics
        """
        if buildings_gdf.empty:
            return {
                'compactness_ratio': 0.0,
                'average_nearest_neighbor_distance': 0.0,
                'building_cluster_count': 0
            }
        
        metrics = {}
        
        try:
            # Calculate compactness ratio (area / perimeter^2)
            buildings_copy = buildings_gdf.copy()
            buildings_copy['area'] = buildings_copy.geometry.area
            buildings_copy['perimeter'] = buildings_copy.geometry.length
            
            # Avoid division by zero
            valid_buildings = buildings_copy[buildings_copy['perimeter'] > 0]
            
            if not valid_buildings.empty:
                compactness_values = valid_buildings['area'] / (valid_buildings['perimeter'] ** 2)
                metrics['compactness_ratio'] = compactness_values.mean()
            else:
                metrics['compactness_ratio'] = 0.0
            
            # Calculate average nearest neighbor distance
            if len(buildings_gdf) > 1:
                centroids = buildings_gdf.geometry.centroid
                distances = []
                
                for i, point in enumerate(centroids):
                    other_points = centroids.drop(centroids.index[i])
                    min_distance = min(point.distance(other) for other in other_points)
                    distances.append(min_distance * 111319.9)  # Convert to meters
                
                metrics['average_nearest_neighbor_distance'] = np.mean(distances)
            else:
                metrics['average_nearest_neighbor_distance'] = 0.0
            
            # Estimate building clusters (simplified)
            # Buildings within 100m of each other are considered in the same cluster
            cluster_distance = 100 / 111319.9  # Convert to degrees
            
            clustered_buildings = buildings_gdf.geometry.buffer(cluster_distance)
            merged_clusters = unary_union(clustered_buildings.tolist())
            
            if hasattr(merged_clusters, 'geoms'):
                metrics['building_cluster_count'] = len(list(merged_clusters.geoms))
            else:
                metrics['building_cluster_count'] = 1 if not merged_clusters.is_empty else 0
        
        except Exception as e:
            # Return default values if calculation fails
            metrics = {
                'compactness_ratio': 0.0,
                'average_nearest_neighbor_distance': 0.0,
                'building_cluster_count': 0
            }
        
        return metrics
    
    def calculate_growth_direction_metrics(self, 
                                         buildings_by_year: Dict[int, gpd.GeoDataFrame],
                                         center_point: Optional[Point] = None) -> Dict[str, Any]:
        """
        Calculate growth direction and sprawl metrics.
        
        Args:
            buildings_by_year: Dictionary mapping years to building GeoDataFrames
            center_point: Optional center point for analysis (if None, uses centroid)
            
        Returns:
            Dictionary with growth direction metrics
        """
        if not buildings_by_year or len(buildings_by_year) < 2:
            return {}
        
        years = sorted(buildings_by_year.keys())
        metrics = {
            'years': years,
            'center_of_mass': {},
            'mean_distance_from_center': {},
            'growth_vectors': {}
        }
        
        # Calculate center point if not provided
        if center_point is None:
            all_buildings = []
            for gdf in buildings_by_year.values():
                if not gdf.empty:
                    all_buildings.append(gdf)
            
            if all_buildings:
                combined = gpd.GeoDataFrame(pd.concat(all_buildings, ignore_index=True))
                center_point = combined.geometry.centroid.unary_union.centroid
        
        if center_point is None:
            return metrics
        
        # Calculate metrics for each year
        for year in years:
            buildings = buildings_by_year[year]
            
            if buildings.empty:
                metrics['center_of_mass'][year] = None
                metrics['mean_distance_from_center'][year] = 0.0
            else:
                # Center of mass (centroid of all buildings)
                center_of_mass = buildings.geometry.centroid.unary_union.centroid
                metrics['center_of_mass'][year] = {
                    'x': center_of_mass.x,
                    'y': center_of_mass.y
                }
                
                # Mean distance from center point
                centroids = buildings.geometry.centroid
                distances = [center_point.distance(centroid) * 111319.9 for centroid in centroids]
                metrics['mean_distance_from_center'][year] = np.mean(distances)
        
        # Calculate growth vectors between consecutive years
        for i in range(1, len(years)):
            prev_year = years[i-1]
            curr_year = years[i]
            
            prev_com = metrics['center_of_mass'][prev_year]
            curr_com = metrics['center_of_mass'][curr_year]
            
            if prev_com and curr_com:
                # Calculate growth vector
                dx = curr_com['x'] - prev_com['x']
                dy = curr_com['y'] - prev_com['y']
                
                distance = math.sqrt(dx**2 + dy**2) * 111319.9  # Convert to meters
                direction = math.degrees(math.atan2(dy, dx))
                
                # Normalize direction to 0-360 degrees
                if direction < 0:
                    direction += 360
                
                period_key = f"{prev_year}-{curr_year}"
                metrics['growth_vectors'][period_key] = {
                    'distance_m': distance,
                    'direction_degrees': direction,
                    'dx': dx,
                    'dy': dy
                }
        
        return metrics
    
    def calculate_summary_statistics(self, 
                                   buildings_by_year: Dict[int, gpd.GeoDataFrame],
                                   roads_by_year: Dict[int, gpd.GeoDataFrame],
                                   analysis_area_km2: float) -> Dict[str, Any]:
        """
        Calculate comprehensive summary statistics.
        
        Args:
            buildings_by_year: Dictionary mapping years to building GeoDataFrames
            roads_by_year: Dictionary mapping years to road GeoDataFrames
            analysis_area_km2: Analysis area in square kilometers
            
        Returns:
            Dictionary with comprehensive summary statistics
        """
        summary = {
            'analysis_area_km2': analysis_area_km2,
            'analysis_years': sorted(list(set(buildings_by_year.keys()) | set(roads_by_year.keys()))),
            'building_metrics': self.calculate_building_growth(buildings_by_year),
            'road_metrics': self.calculate_road_growth(roads_by_year)
        }
        
        # Calculate density metrics for each year
        summary['density_by_year'] = {}
        for year in summary['analysis_years']:
            buildings = buildings_by_year.get(year, gpd.GeoDataFrame())
            roads = roads_by_year.get(year, gpd.GeoDataFrame())
            
            density_metrics = self.calculate_density_metrics(buildings, roads, analysis_area_km2)
            summary['density_by_year'][year] = density_metrics
        
        # Calculate compactness metrics for each year
        summary['compactness_by_year'] = {}
        for year in summary['analysis_years']:
            buildings = buildings_by_year.get(year, gpd.GeoDataFrame())
            compactness_metrics = self.calculate_compactness_metrics(buildings)
            summary['compactness_by_year'][year] = compactness_metrics
        
        # Calculate growth direction metrics
        if buildings_by_year:
            summary['growth_direction'] = self.calculate_growth_direction_metrics(buildings_by_year)
        
        return summary
