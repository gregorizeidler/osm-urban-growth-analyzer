"""Interactive map visualization module for urban growth analysis."""

import folium
from folium import plugins
import geopandas as gpd
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from branca.colormap import LinearColormap
import json

from ..utils import ConfigManager, Logger, format_large_number


class MapVisualizer:
    """Creates interactive maps for urban growth visualization."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize map visualizer.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager or ConfigManager()
        self.logger = Logger("MapVisualizer")
        
        # Get visualization settings from config
        viz_config = self.config.get_visualization_config()
        self.map_style = viz_config.get('map_style', 'OpenStreetMap')
        self.color_schemes = viz_config.get('color_schemes', {})
    
    def create_temporal_comparison_map(self, 
                                     processed_data: Dict[str, Dict[int, gpd.GeoDataFrame]],
                                     bbox: Tuple[float, float, float, float],
                                     feature_type: str = 'buildings') -> folium.Map:
        """
        Create a temporal comparison map showing changes over time.
        
        Args:
            processed_data: Processed data by feature type and year
            bbox: Bounding box (south, west, north, east)
            feature_type: Type of features to visualize ('buildings', 'roads', 'landuse')
            
        Returns:
            Folium map with temporal layers
        """
        # Calculate map center
        center_lat = (bbox[0] + bbox[2]) / 2
        center_lon = (bbox[1] + bbox[3]) / 2
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles=self.map_style
        )
        
        # Add bounding box rectangle
        folium.Rectangle(
            bounds=[[bbox[0], bbox[1]], [bbox[2], bbox[3]]],
            color='red',
            weight=2,
            fill=False,
            popup='Analysis Area'
        ).add_to(m)
        
        # Get data for the specified feature type
        feature_data = processed_data.get(feature_type, {})
        years = sorted(feature_data.keys())
        
        if not years:
            self.logger.warning(f"No data found for feature type: {feature_type}")
            return m
        
        # Get color scheme for feature type
        colors = self.color_schemes.get(feature_type, ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'])
        
        # Create a feature group for each year
        feature_groups = {}
        
        for i, year in enumerate(years):
            gdf = feature_data[year]
            
            if gdf.empty:
                continue
            
            # Create feature group for this year
            fg = folium.FeatureGroup(name=f'{feature_type.title()} {year}')
            
            # Choose color for this year
            color = colors[i % len(colors)]
            
            # Add features to map based on geometry type
            if feature_type == 'buildings':
                self._add_buildings_to_map(gdf, fg, color, year)
            elif feature_type == 'roads':
                self._add_roads_to_map(gdf, fg, color, year)
            elif feature_type == 'landuse':
                self._add_landuse_to_map(gdf, fg, color, year)
            
            feature_groups[year] = fg
            fg.add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add a legend
        self._add_temporal_legend(m, years, colors, feature_type)
        
        return m
    
    def create_growth_hotspots_map(self, 
                                 hotspots_data: Dict[str, Any],
                                 bbox: Tuple[float, float, float, float]) -> folium.Map:
        """
        Create a map showing urban growth hotspots.
        
        Args:
            hotspots_data: Hotspots analysis results
            bbox: Bounding box (south, west, north, east)
            
        Returns:
            Folium map with growth hotspots
        """
        # Calculate map center
        center_lat = (bbox[0] + bbox[2]) / 2
        center_lon = (bbox[1] + bbox[3]) / 2
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles=self.map_style
        )
        
        # Add analysis grid
        if 'grid' in hotspots_data:
            grid = hotspots_data['grid']
            
            # Add grid as a base layer
            folium.GeoJson(
                grid.to_json(),
                style_function=lambda x: {
                    'fillColor': 'lightblue',
                    'color': 'blue',
                    'weight': 1,
                    'fillOpacity': 0.1
                },
                popup=folium.GeoJsonPopup(fields=['grid_id'])
            ).add_to(m)
        
        # Add hotspots for each time period
        if 'hotspots' in hotspots_data:
            hotspots = hotspots_data['hotspots']
            
            for period, hotspot_gdf in hotspots.items():
                if hotspot_gdf.empty:
                    continue
                
                # Create feature group for this period
                fg = folium.FeatureGroup(name=f'Hotspots {period}')
                
                # Create colormap based on growth values
                growth_values = hotspot_gdf['absolute_growth'].values
                if len(growth_values) > 0:
                    colormap = LinearColormap(
                        colors=['yellow', 'orange', 'red'],
                        vmin=growth_values.min(),
                        vmax=growth_values.max()
                    )
                    
                    # Add hotspots to map
                    for idx, row in hotspot_gdf.iterrows():
                        color = colormap(row['absolute_growth'])
                        
                        folium.GeoJson(
                            row['geometry'].__geo_interface__,
                            style_function=lambda x, color=color: {
                                'fillColor': color,
                                'color': 'black',
                                'weight': 1,
                                'fillOpacity': 0.7
                            },
                            popup=folium.Popup(
                                f"""
                                <b>Growth Hotspot</b><br>
                                Period: {period}<br>
                                Absolute Growth: {row['absolute_growth']:.2f}<br>
                                Relative Growth: {row['relative_growth']:.1f}%
                                """,
                                max_width=200
                            )
                        ).add_to(fg)
                    
                    # Add colormap to map
                    colormap.caption = f'Growth Intensity ({period})'
                    colormap.add_to(m)
                
                fg.add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        return m
    
    def create_density_heatmap(self, 
                             buildings_gdf: gpd.GeoDataFrame,
                             bbox: Tuple[float, float, float, float]) -> folium.Map:
        """
        Create a density heatmap of urban features.
        
        Args:
            buildings_gdf: GeoDataFrame with building data
            bbox: Bounding box (south, west, north, east)
            
        Returns:
            Folium map with density heatmap
        """
        # Calculate map center
        center_lat = (bbox[0] + bbox[2]) / 2
        center_lon = (bbox[1] + bbox[3]) / 2
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles=self.map_style
        )
        
        if buildings_gdf.empty:
            return m
        
        # Get building centroids for heatmap
        centroids = buildings_gdf.geometry.centroid
        heat_data = [[point.y, point.x] for point in centroids]
        
        # Add heatmap
        plugins.HeatMap(
            heat_data,
            min_opacity=0.2,
            max_zoom=18,
            radius=25,
            blur=15,
            gradient={
                0.0: 'blue',
                0.4: 'lime',
                0.6: 'orange',
                1.0: 'red'
            }
        ).add_to(m)
        
        # Add building count info
        building_count = len(buildings_gdf)
        folium.Marker(
            [center_lat, center_lon],
            popup=f'Total Buildings: {building_count:,}',
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(m)
        
        return m
    
    def create_before_after_map(self, 
                              before_data: gpd.GeoDataFrame,
                              after_data: gpd.GeoDataFrame,
                              before_year: int,
                              after_year: int,
                              bbox: Tuple[float, float, float, float],
                              feature_type: str = 'buildings') -> folium.Map:
        """
        Create a before/after comparison map.
        
        Args:
            before_data: GeoDataFrame for the earlier year
            after_data: GeoDataFrame for the later year
            before_year: Earlier year
            after_year: Later year
            bbox: Bounding box (south, west, north, east)
            feature_type: Type of features being compared
            
        Returns:
            Folium map with before/after comparison
        """
        # Calculate map center
        center_lat = (bbox[0] + bbox[2]) / 2
        center_lon = (bbox[1] + bbox[3]) / 2
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles=self.map_style
        )
        
        # Create feature groups
        before_fg = folium.FeatureGroup(name=f'{feature_type.title()} {before_year}')
        after_fg = folium.FeatureGroup(name=f'{feature_type.title()} {after_year}')
        new_features_fg = folium.FeatureGroup(name=f'New {feature_type.title()} ({after_year})')
        
        # Add before data
        if not before_data.empty:
            if feature_type == 'buildings':
                self._add_buildings_to_map(before_data, before_fg, '#2E86AB', before_year)
            elif feature_type == 'roads':
                self._add_roads_to_map(before_data, before_fg, '#2E86AB', before_year)
        
        # Add after data
        if not after_data.empty:
            if feature_type == 'buildings':
                self._add_buildings_to_map(after_data, after_fg, '#A23B72', after_year)
            elif feature_type == 'roads':
                self._add_roads_to_map(after_data, after_fg, '#A23B72', after_year)
        
        # Find new features (simplified approach)
        if not before_data.empty and not after_data.empty:
            # This is a simplified approach - in practice, you'd want more sophisticated
            # spatial matching to identify truly new vs. modified features
            new_features = after_data[~after_data.index.isin(before_data.index)]
            
            if not new_features.empty:
                if feature_type == 'buildings':
                    self._add_buildings_to_map(new_features, new_features_fg, '#F18F01', f'New {after_year}')
                elif feature_type == 'roads':
                    self._add_roads_to_map(new_features, new_features_fg, '#F18F01', f'New {after_year}')
        
        # Add feature groups to map
        before_fg.add_to(m)
        after_fg.add_to(m)
        new_features_fg.add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add statistics
        stats_html = f"""
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 200px; height: 120px; 
                    background-color: white; border: 2px solid grey; z-index: 9999; 
                    font-size: 14px; padding: 10px">
        <h4>Comparison Statistics</h4>
        <p>{before_year}: {len(before_data):,} {feature_type}</p>
        <p>{after_year}: {len(after_data):,} {feature_type}</p>
        <p>Change: {len(after_data) - len(before_data):+,} ({((len(after_data) - len(before_data)) / len(before_data) * 100):+.1f}%)</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(stats_html))
        
        return m
    
    def _add_buildings_to_map(self, buildings_gdf: gpd.GeoDataFrame, 
                            feature_group: folium.FeatureGroup,
                            color: str, year: int) -> None:
        """Add building polygons to a feature group."""
        for idx, building in buildings_gdf.iterrows():
            # Create popup with building information
            popup_text = f"""
            <b>Building ({year})</b><br>
            Type: {building.get('building_type', 'Unknown')}<br>
            """
            
            if 'area_m2' in building:
                popup_text += f"Area: {format_large_number(building['area_m2'])} m²<br>"
            
            if 'levels' in building:
                popup_text += f"Levels: {building['levels']}<br>"
            
            folium.GeoJson(
                building['geometry'].__geo_interface__,
                style_function=lambda x, color=color: {
                    'fillColor': color,
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.6
                },
                popup=folium.Popup(popup_text, max_width=200)
            ).add_to(feature_group)
    
    def _add_roads_to_map(self, roads_gdf: gpd.GeoDataFrame,
                        feature_group: folium.FeatureGroup,
                        color: str, year: int) -> None:
        """Add road linestrings to a feature group."""
        for idx, road in roads_gdf.iterrows():
            # Determine line weight based on road type
            highway_type = road.get('highway', 'unknown')
            weight = self._get_road_weight(highway_type)
            
            # Create popup with road information
            popup_text = f"""
            <b>Road ({year})</b><br>
            Type: {highway_type}<br>
            """
            
            if 'length_m' in road:
                popup_text += f"Length: {format_large_number(road['length_m'])} m<br>"
            
            folium.GeoJson(
                road['geometry'].__geo_interface__,
                style_function=lambda x, color=color, weight=weight: {
                    'color': color,
                    'weight': weight,
                    'opacity': 0.8
                },
                popup=folium.Popup(popup_text, max_width=200)
            ).add_to(feature_group)
    
    def _add_landuse_to_map(self, landuse_gdf: gpd.GeoDataFrame,
                          feature_group: folium.FeatureGroup,
                          color: str, year: int) -> None:
        """Add landuse polygons to a feature group."""
        for idx, landuse in landuse_gdf.iterrows():
            # Get landuse type for coloring
            landuse_type = landuse.get('landuse_category', landuse.get('landuse', 'unknown'))
            
            # Create popup with landuse information
            popup_text = f"""
            <b>Landuse ({year})</b><br>
            Type: {landuse_type}<br>
            """
            
            if 'area_m2' in landuse:
                popup_text += f"Area: {format_large_number(landuse['area_m2'])} m²<br>"
            
            folium.GeoJson(
                landuse['geometry'].__geo_interface__,
                style_function=lambda x, color=color: {
                    'fillColor': color,
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.4
                },
                popup=folium.Popup(popup_text, max_width=200)
            ).add_to(feature_group)
    
    def _get_road_weight(self, highway_type: str) -> int:
        """Get line weight based on highway type."""
        weight_map = {
            'motorway': 6,
            'trunk': 5,
            'primary': 4,
            'secondary': 3,
            'tertiary': 2,
            'residential': 2,
            'service': 1,
            'track': 1
        }
        return weight_map.get(highway_type, 2)
    
    def _add_temporal_legend(self, m: folium.Map, years: List[int], 
                           colors: List[str], feature_type: str) -> None:
        """Add a legend for temporal comparison."""
        legend_html = f"""
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: auto; 
                    background-color: white; border: 2px solid grey; z-index: 9999; 
                    font-size: 14px; padding: 10px">
        <h4>{feature_type.title()} by Year</h4>
        """
        
        for i, year in enumerate(years):
            color = colors[i % len(colors)]
            legend_html += f"""
            <p><span style="color: {color}; font-size: 20px;">●</span> {year}</p>
            """
        
        legend_html += "</div>"
        
        m.get_root().html.add_child(folium.Element(legend_html))
    
    def create_analysis_summary_map(self, 
                                  analysis_results: Dict[str, Any]) -> folium.Map:
        """
        Create a comprehensive map summarizing the analysis.
        
        Args:
            analysis_results: Complete analysis results
            
        Returns:
            Folium map with analysis summary
        """
        # Extract bbox from metadata
        bbox = analysis_results['metadata']['bbox']
        
        # Calculate map center
        center_lat = (bbox[0] + bbox[2]) / 2
        center_lon = (bbox[1] + bbox[3]) / 2
        
        # Create base map
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=11,
            tiles=self.map_style
        )
        
        # Add analysis area boundary
        folium.Rectangle(
            bounds=[[bbox[0], bbox[1]], [bbox[2], bbox[3]]],
            color='red',
            weight=3,
            fill=False,
            popup='Analysis Area'
        ).add_to(m)
        
        # Add summary statistics as a marker
        if 'quantitative_analysis' in analysis_results:
            quant_data = analysis_results['quantitative_analysis']
            
            # Get latest year data
            years = quant_data.get('years', [])
            if years:
                latest_year = max(years)
                
                # Building stats
                building_metrics = quant_data.get('building_metrics', {})
                building_counts = building_metrics.get('building_counts', {})
                latest_buildings = building_counts.get(latest_year, 0)
                
                # Road stats  
                road_metrics = quant_data.get('road_metrics', {})
                road_counts = road_metrics.get('road_counts', {})
                latest_roads = road_counts.get(latest_year, 0)
                
                # Create summary popup
                summary_html = f"""
                <h3>Analysis Summary</h3>
                <p><b>Analysis Period:</b> {min(years)} - {max(years)}</p>
                <p><b>Buildings ({latest_year}):</b> {latest_buildings:,}</p>
                <p><b>Roads ({latest_year}):</b> {latest_roads:,}</p>
                """
                
                # Add growth rates if available
                growth_rates = building_metrics.get('growth_rates', {})
                if growth_rates:
                    latest_period = list(growth_rates.keys())[-1]
                    latest_growth = growth_rates[latest_period]
                    summary_html += f"""
                    <p><b>Recent Growth ({latest_period}):</b></p>
                    <p>Buildings: {latest_growth.get('count_growth_percent', 0):+.1f}%</p>
                    """
                
                summary_html += "</div>"
                
                folium.Marker(
                    [center_lat, center_lon],
                    popup=folium.Popup(summary_html, max_width=300),
                    icon=folium.Icon(color='green', icon='stats', prefix='fa')
                ).add_to(m)
        
        return m
