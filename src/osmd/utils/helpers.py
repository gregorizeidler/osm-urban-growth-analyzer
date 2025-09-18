"""Helper functions for the OSM Urban Growth Analysis project."""

import re
import math
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timedelta
import geopandas as gpd
from shapely.geometry import Polygon
import numpy as np
import pyproj
from pyproj import CRS, Transformer


def validate_coordinates(south: float, west: float, north: float, east: float) -> bool:
    """
    Validate geographic coordinates for a bounding box.
    
    Args:
        south: Southern latitude
        west: Western longitude  
        north: Northern latitude
        east: Eastern longitude
        
    Returns:
        True if coordinates are valid
        
    Raises:
        ValueError: If coordinates are invalid
    """
    if not (-90 <= south <= 90) or not (-90 <= north <= 90):
        raise ValueError("Latitude values must be between -90 and 90 degrees")
    
    if not (-180 <= west <= 180) or not (-180 <= east <= 180):
        raise ValueError("Longitude values must be between -180 and 180 degrees")
    
    if south >= north:
        raise ValueError("Southern latitude must be less than northern latitude")
    
    if west >= east:
        raise ValueError("Western longitude must be less than eastern longitude")
    
    return True


def create_temporal_overpass_query(south: float, west: float, north: float, east: float,
                                  features: List[str], date_str: str) -> str:
    """
    Create Overpass query for historical data using temporal syntax.
    
    Args:
        south, west, north, east: Bounding box coordinates
        features: List of OSM features to query
        date_str: Date in ISO format (e.g., "2020-01-01T00:00:00Z")
        
    Returns:
        Overpass query string with temporal filter
    """
    bbox_str = f"({south},{west},{north},{east})"
    
    # Use adiff (augmented diff) for temporal queries
    query_parts = [
        "[out:json][timeout:600][adiff:\"2010-01-01T00:00:00Z\",\"" + date_str + "\"];",
        "("
    ]
    
    # Add feature queries with temporal context
    for feature in features:
        if "=" in feature:
            key, value = feature.split("=", 1)
            query_parts.append(f'  way["{key}"="{value}"]{bbox_str};')
            query_parts.append(f'  relation["{key}"="{value}"]{bbox_str};')
        else:
            query_parts.append(f'  way["{feature}"]{bbox_str};')
            query_parts.append(f'  relation["{feature}"]{bbox_str};')
    
    query_parts.extend([");", "out geom;"])
    
    return "\n".join(query_parts)


def bbox_to_overpass_query(south: float, west: float, north: float, east: float,
                          features: List[str], date_filter: Optional[str] = None) -> str:
    """
    Convert bounding box and features to Overpass API query.
    
    Args:
        south: Southern latitude
        west: Western longitude
        north: Northern latitude  
        east: Eastern longitude
        features: List of OSM features to query
        date_filter: Optional date filter (e.g., "2020-01-01T00:00:00Z")
        
    Returns:
        Overpass API query string
    """
    validate_coordinates(south, west, north, east)
    
    bbox_str = f"({south},{west},{north},{east})"
    
    # Build a simpler query that works without date filter for now
    # Historical queries are complex and require special syntax
    query_parts = ["[out:json][timeout:300];"]
    query_parts.append("(")
    
    # Add feature queries - simplified version
    for feature in features:
        if "=" in feature:
            key, value = feature.split("=", 1)
            query_parts.append(f'  way["{key}"="{value}"]{bbox_str};')
            query_parts.append(f'  relation["{key}"="{value}"]{bbox_str};')
        else:
            query_parts.append(f'  way["{feature}"]{bbox_str};')
            query_parts.append(f'  relation["{feature}"]{bbox_str};')
    
    query_parts.extend([");", "out geom;"])
    
    return "\n".join(query_parts)


def get_utm_crs(longitude: float, latitude: float) -> CRS:
    """
    Get the appropriate UTM CRS for given coordinates.
    
    Args:
        longitude: Longitude in decimal degrees
        latitude: Latitude in decimal degrees
        
    Returns:
        PyProj CRS object for the appropriate UTM zone
    """
    # Calculate UTM zone
    utm_zone = int((longitude + 180) / 6) + 1
    
    # Determine hemisphere
    if latitude >= 0:
        # Northern hemisphere
        epsg_code = 32600 + utm_zone
    else:
        # Southern hemisphere  
        epsg_code = 32700 + utm_zone
    
    return CRS.from_epsg(epsg_code)


def calculate_area(geometry, source_crs: str = "EPSG:4326") -> float:
    """
    Calculate area of a geometry in square meters using appropriate UTM projection.
    
    Args:
        geometry: Shapely geometry object
        source_crs: Source coordinate reference system (default WGS84)
        
    Returns:
        Area in square meters
    """
    if geometry is None or geometry.is_empty:
        return 0.0
    
    if not hasattr(geometry, 'area'):
        return 0.0
    
    # If already in a projected CRS, return area directly
    if source_crs != "EPSG:4326":
        return geometry.area
    
    # Get centroid for UTM zone calculation
    centroid = geometry.centroid
    
    # Get appropriate UTM CRS
    utm_crs = get_utm_crs(centroid.x, centroid.y)
    
    # Create transformer
    transformer = Transformer.from_crs(CRS.from_string(source_crs), utm_crs, always_xy=True)
    
    # Transform geometry to UTM
    try:
        from shapely.ops import transform
        utm_geometry = transform(transformer.transform, geometry)
        return utm_geometry.area
    except Exception:
        # Fallback to approximation if transformation fails
        return geometry.area * 111319.9 ** 2


def calculate_distance(point1, point2, source_crs: str = "EPSG:4326") -> float:
    """
    Calculate distance between two points in meters using appropriate UTM projection.
    
    Args:
        point1: First point (Shapely Point or tuple of coordinates)
        point2: Second point (Shapely Point or tuple of coordinates)  
        source_crs: Source coordinate reference system (default WGS84)
        
    Returns:
        Distance in meters
    """
    from shapely.geometry import Point
    
    # Convert to Points if needed
    if not hasattr(point1, 'x'):
        point1 = Point(point1)
    if not hasattr(point2, 'x'):
        point2 = Point(point2)
    
    # If already in projected CRS, return distance directly
    if source_crs != "EPSG:4326":
        return point1.distance(point2)
    
    # Get centroid for UTM zone calculation
    center_x = (point1.x + point2.x) / 2
    center_y = (point1.y + point2.y) / 2
    
    # Get appropriate UTM CRS
    utm_crs = get_utm_crs(center_x, center_y)
    
    # Create transformer
    transformer = Transformer.from_crs(CRS.from_string(source_crs), utm_crs, always_xy=True)
    
    try:
        # Transform points to UTM
        utm_x1, utm_y1 = transformer.transform(point1.x, point1.y)
        utm_x2, utm_y2 = transformer.transform(point2.x, point2.y)
        
        # Calculate distance
        return math.sqrt((utm_x2 - utm_x1)**2 + (utm_y2 - utm_y1)**2)
    except Exception:
        # Fallback to haversine formula approximation
        return haversine_distance(point1.y, point1.x, point2.y, point2.x)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points using Haversine formula.
    
    Args:
        lat1, lon1: Latitude and longitude of first point in decimal degrees
        lat2, lon2: Latitude and longitude of second point in decimal degrees
        
    Returns:
        Distance in meters
    """
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth radius in meters
    r = 6371000
    
    return c * r


def get_time_periods(years: List[int]) -> List[Tuple[int, str]]:
    """
    Generate time periods for OSM historical queries.
    
    Args:
        years: List of years to analyze
        
    Returns:
        List of (year, date_string) tuples for Overpass queries
    """
    periods = []
    for year in sorted(years):
        # Use January 1st of each year
        date_str = f"{year}-01-01T00:00:00Z"
        periods.append((year, date_str))
    
    return periods


def normalize_osm_tags(tags: Dict[str, str]) -> Dict[str, str]:
    """
    Normalize OSM tags for consistent analysis.
    
    Args:
        tags: Dictionary of OSM tags
        
    Returns:
        Normalized tags dictionary
    """
    normalized = {}
    
    for key, value in tags.items():
        # Convert to lowercase and strip whitespace
        clean_key = key.lower().strip()
        clean_value = value.lower().strip() if isinstance(value, str) else str(value)
        
        # Handle common tag variations
        if clean_key == "building" and clean_value in ["yes", "true", "1"]:
            clean_value = "yes"
        elif clean_key == "highway" and clean_value in ["road", "street"]:
            clean_value = "unclassified"
        
        normalized[clean_key] = clean_value
    
    return normalized


def calculate_building_density(buildings_gdf: gpd.GeoDataFrame, 
                             area_km2: float) -> Dict[str, float]:
    """
    Calculate building density metrics.
    
    Args:
        buildings_gdf: GeoDataFrame with building polygons
        area_km2: Analysis area in square kilometers
        
    Returns:
        Dictionary with density metrics
    """
    if buildings_gdf.empty or area_km2 <= 0:
        return {
            "buildings_per_km2": 0.0,
            "building_coverage_ratio": 0.0,
            "avg_building_area_m2": 0.0
        }
    
    building_count = len(buildings_gdf)
    total_building_area_m2 = buildings_gdf.geometry.area.sum()
    
    return {
        "buildings_per_km2": building_count / area_km2,
        "building_coverage_ratio": total_building_area_m2 / (area_km2 * 1_000_000),
        "avg_building_area_m2": total_building_area_m2 / building_count if building_count > 0 else 0.0
    }


def calculate_road_density(roads_gdf: gpd.GeoDataFrame, 
                          area_km2: float) -> Dict[str, float]:
    """
    Calculate road density metrics.
    
    Args:
        roads_gdf: GeoDataFrame with road linestrings
        area_km2: Analysis area in square kilometers
        
    Returns:
        Dictionary with road density metrics
    """
    if roads_gdf.empty or area_km2 <= 0:
        return {
            "road_length_km_per_km2": 0.0,
            "total_road_length_km": 0.0
        }
    
    # Calculate total road length in kilometers
    total_length_km = roads_gdf.geometry.length.sum() / 1000  # Convert to km
    
    return {
        "road_length_km_per_km2": total_length_km / area_km2,
        "total_road_length_km": total_length_km
    }


def classify_building_types(buildings_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Classify buildings into categories based on OSM tags.
    
    Args:
        buildings_gdf: GeoDataFrame with building data
        
    Returns:
        GeoDataFrame with added 'building_type' column
    """
    def classify_building(row):
        tags = row.get('tags', {}) if 'tags' in row else {}
        building_tag = tags.get('building', 'unknown')
        
        # Residential buildings
        if building_tag in ['house', 'apartments', 'residential', 'detached', 'terrace']:
            return 'residential'
        
        # Commercial buildings
        elif building_tag in ['commercial', 'retail', 'office', 'shop']:
            return 'commercial'
        
        # Industrial buildings
        elif building_tag in ['industrial', 'warehouse', 'manufacture']:
            return 'industrial'
        
        # Public/institutional buildings
        elif building_tag in ['school', 'hospital', 'church', 'civic', 'public']:
            return 'public'
        
        # Generic building
        elif building_tag in ['yes', 'true']:
            return 'generic'
        
        else:
            return 'other'
    
    buildings_copy = buildings_gdf.copy()
    buildings_copy['building_type'] = buildings_copy.apply(classify_building, axis=1)
    
    return buildings_copy


def create_analysis_grid(bbox: Tuple[float, float, float, float], 
                        grid_size_km: float = 1.0) -> gpd.GeoDataFrame:
    """
    Create a grid for spatial analysis.
    
    Args:
        bbox: Bounding box (south, west, north, east)
        grid_size_km: Grid cell size in kilometers
        
    Returns:
        GeoDataFrame with grid polygons
    """
    south, west, north, east = bbox
    
    # Convert grid size to degrees (rough approximation)
    grid_size_deg = grid_size_km / 111.32  # 1 degree ≈ 111.32 km
    
    # Create grid coordinates
    x_coords = np.arange(west, east + grid_size_deg, grid_size_deg)
    y_coords = np.arange(south, north + grid_size_deg, grid_size_deg)
    
    # Create grid polygons
    polygons = []
    grid_ids = []
    
    for i, x in enumerate(x_coords[:-1]):
        for j, y in enumerate(y_coords[:-1]):
            polygon = Polygon([
                (x, y),
                (x + grid_size_deg, y),
                (x + grid_size_deg, y + grid_size_deg),
                (x, y + grid_size_deg),
                (x, y)
            ])
            polygons.append(polygon)
            grid_ids.append(f"grid_{i}_{j}")
    
    return gpd.GeoDataFrame({
        'grid_id': grid_ids,
        'geometry': polygons
    }, crs='EPSG:4326')


def split_large_bbox(bbox: Tuple[float, float, float, float], 
                     max_area_km2: float = 100.0) -> List[Tuple[float, float, float, float]]:
    """
    Split large bounding boxes into smaller chunks to avoid API timeouts.
    
    Args:
        bbox: Bounding box (south, west, north, east)
        max_area_km2: Maximum area per chunk in square kilometers
        
    Returns:
        List of smaller bounding boxes
    """
    south, west, north, east = bbox
    
    # Calculate approximate area in km²
    width_km = haversine_distance(south, west, south, east) / 1000
    height_km = haversine_distance(south, west, north, west) / 1000
    area_km2 = width_km * height_km
    
    # If area is within limits, return original bbox
    if area_km2 <= max_area_km2:
        return [bbox]
    
    # Calculate number of divisions needed
    divisions = math.ceil(math.sqrt(area_km2 / max_area_km2))
    
    # Split into grid
    lat_step = (north - south) / divisions
    lon_step = (east - west) / divisions
    
    bboxes = []
    for i in range(divisions):
        for j in range(divisions):
            sub_south = south + i * lat_step
            sub_north = south + (i + 1) * lat_step
            sub_west = west + j * lon_step
            sub_east = west + (j + 1) * lon_step
            
            bboxes.append((sub_south, sub_west, sub_north, sub_east))
    
    return bboxes


def estimate_query_complexity(bbox: Tuple[float, float, float, float], 
                            features: List[str]) -> int:
    """
    Estimate query complexity to predict potential timeouts.
    
    Args:
        bbox: Bounding box (south, west, north, east)
        features: List of OSM features
        
    Returns:
        Complexity score (higher = more complex)
    """
    south, west, north, east = bbox
    
    # Calculate area
    width_km = haversine_distance(south, west, south, east) / 1000
    height_km = haversine_distance(south, west, north, west) / 1000
    area_km2 = width_km * height_km
    
    # Base complexity from area
    complexity = int(area_km2)
    
    # Add complexity for each feature type
    complexity += len(features) * 10
    
    # Add complexity for broad features
    broad_features = ['building', 'highway', 'landuse', 'amenity']
    for feature in features:
        if any(broad in feature.lower() for broad in broad_features):
            complexity += 50
    
    return complexity


def optimize_overpass_query(south: float, west: float, north: float, east: float,
                          features: List[str], date_filter: Optional[str] = None) -> str:
    """
    Generate optimized Overpass query with complexity management.
    
    Args:
        south, west, north, east: Bounding box coordinates
        features: List of OSM features to query
        date_filter: Optional date filter
        
    Returns:
        Optimized Overpass query string
    """
    bbox = (south, west, north, east)
    complexity = estimate_query_complexity(bbox, features)
    
    # Use longer timeout for complex queries
    timeout = 300 if complexity < 1000 else 600
    
    bbox_str = f"({south},{west},{north},{east})"
    
    query_parts = [f"[out:json][timeout:{timeout}];"]
    query_parts.append("(")
    
    # Group similar features to reduce query parts
    building_features = [f for f in features if 'building' in f.lower()]
    highway_features = [f for f in features if 'highway' in f.lower()]
    other_features = [f for f in features if f not in building_features + highway_features]
    
    # Add building queries
    if building_features:
        if len(building_features) == 1 and building_features[0] == 'building':
            query_parts.append(f'  way["building"]{bbox_str};')
            query_parts.append(f'  relation["building"]{bbox_str};')
        else:
            for feature in building_features:
                if "=" in feature:
                    key, value = feature.split("=", 1)
                    query_parts.append(f'  way["{key}"="{value}"]{bbox_str};')
                    query_parts.append(f'  relation["{key}"="{value}"]{bbox_str};')
    
    # Add highway queries
    if highway_features:
        if len(highway_features) == 1 and highway_features[0] == 'highway':
            query_parts.append(f'  way["highway"]{bbox_str};')
            query_parts.append(f'  relation["highway"]{bbox_str};')
        else:
            for feature in highway_features:
                if "=" in feature:
                    key, value = feature.split("=", 1)
                    query_parts.append(f'  way["{key}"="{value}"]{bbox_str};')
                    query_parts.append(f'  relation["{key}"="{value}"]{bbox_str};')
    
    # Add other features
    for feature in other_features:
        if "=" in feature:
            key, value = feature.split("=", 1)
            query_parts.append(f'  way["{key}"="{value}"]{bbox_str};')
            query_parts.append(f'  relation["{key}"="{value}"]{bbox_str};')
        else:
            query_parts.append(f'  way["{feature}"]{bbox_str};')
            query_parts.append(f'  relation["{feature}"]{bbox_str};')
    
    query_parts.extend([");", "out geom;"])
    
    return "\n".join(query_parts)


def format_large_number(number: float, precision: int = 1) -> str:
    """
    Format large numbers with appropriate units.
    
    Args:
        number: Number to format
        precision: Decimal places
        
    Returns:
        Formatted string
    """
    if number >= 1_000_000:
        return f"{number / 1_000_000:.{precision}f}M"
    elif number >= 1_000:
        return f"{number / 1_000:.{precision}f}K"
    else:
        return f"{number:.{precision}f}"
