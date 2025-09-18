"""Chart generation module for urban growth analysis visualization."""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

from ..utils import ConfigManager, Logger, format_large_number


class ChartGenerator:
    """Generates various charts and plots for urban growth analysis."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize chart generator.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager or ConfigManager()
        self.logger = Logger("ChartGenerator")
        
        # Set plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def create_growth_timeline_chart(self, 
                                   building_metrics: Dict[str, Any],
                                   road_metrics: Dict[str, Any]) -> go.Figure:
        """
        Create a timeline chart showing growth over years.
        
        Args:
            building_metrics: Building growth metrics
            road_metrics: Road growth metrics
            
        Returns:
            Plotly figure with growth timeline
        """
        # Create subplot with secondary y-axis
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Building Growth Over Time', 'Road Network Growth Over Time'),
            vertical_spacing=0.1
        )
        
        # Building growth
        if 'years' in building_metrics and 'building_counts' in building_metrics:
            years = building_metrics['years']
            counts = [building_metrics['building_counts'].get(year, 0) for year in years]
            areas = [building_metrics['total_area_m2'].get(year, 0) / 1_000_000 for year in years]  # Convert to km²
            
            # Building count
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=counts,
                    mode='lines+markers',
                    name='Building Count',
                    line=dict(color='#2E86AB', width=3),
                    marker=dict(size=8)
                ),
                row=1, col=1
            )
            
            # Building area (secondary axis)
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=areas,
                    mode='lines+markers',
                    name='Total Area (km²)',
                    line=dict(color='#A23B72', width=3, dash='dash'),
                    marker=dict(size=8),
                    yaxis='y2'
                ),
                row=1, col=1
            )
        
        # Road growth
        if 'years' in road_metrics and 'road_counts' in road_metrics:
            years = road_metrics['years']
            counts = [road_metrics['road_counts'].get(year, 0) for year in years]
            lengths = [road_metrics['total_length_km'].get(year, 0) for year in years]
            
            # Road count
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=counts,
                    mode='lines+markers',
                    name='Road Count',
                    line=dict(color='#1B4332', width=3),
                    marker=dict(size=8)
                ),
                row=2, col=1
            )
            
            # Road length (secondary axis)
            fig.add_trace(
                go.Scatter(
                    x=years,
                    y=lengths,
                    mode='lines+markers',
                    name='Total Length (km)',
                    line=dict(color='#52B788', width=3, dash='dash'),
                    marker=dict(size=8),
                    yaxis='y4'
                ),
                row=2, col=1
            )
        
        # Update layout
        fig.update_layout(
            title='Urban Growth Timeline',
            height=700,
            showlegend=True,
            template='plotly_white'
        )
        
        # Update x-axes
        fig.update_xaxes(title_text="Year", row=2, col=1)
        
        # Update y-axes
        fig.update_yaxes(title_text="Building Count", row=1, col=1)
        fig.update_yaxes(title_text="Road Count", row=2, col=1)
        
        return fig
    
    def create_growth_rate_chart(self, growth_metrics: Dict[str, Any]) -> go.Figure:
        """
        Create a chart showing growth rates between periods.
        
        Args:
            growth_metrics: Growth rate metrics
            
        Returns:
            Plotly figure with growth rates
        """
        fig = go.Figure()
        
        if 'growth_rates' not in growth_metrics:
            return fig
        
        growth_rates = growth_metrics['growth_rates']
        periods = list(growth_rates.keys())
        
        # Extract growth rates
        count_growth = [growth_rates[period].get('count_growth_percent', 0) for period in periods]
        area_growth = [growth_rates[period].get('area_growth_percent', 0) for period in periods]
        
        # Add traces
        fig.add_trace(go.Bar(
            x=periods,
            y=count_growth,
            name='Count Growth (%)',
            marker_color='#2E86AB',
            text=[f'{rate:+.1f}%' for rate in count_growth],
            textposition='auto'
        ))
        
        fig.add_trace(go.Bar(
            x=periods,
            y=area_growth,
            name='Area Growth (%)',
            marker_color='#A23B72',
            text=[f'{rate:+.1f}%' for rate in area_growth],
            textposition='auto'
        ))
        
        # Update layout
        fig.update_layout(
            title='Growth Rates by Period',
            xaxis_title='Period',
            yaxis_title='Growth Rate (%)',
            barmode='group',
            template='plotly_white',
            height=500
        )
        
        return fig
    
    def create_building_type_distribution_chart(self, 
                                              building_metrics: Dict[str, Any]) -> go.Figure:
        """
        Create a chart showing building type distribution over time.
        
        Args:
            building_metrics: Building metrics data
            
        Returns:
            Plotly figure with building type distribution
        """
        if 'building_types' not in building_metrics or 'years' not in building_metrics:
            return go.Figure()
        
        building_types = building_metrics['building_types']
        years = building_metrics['years']
        
        # Get all unique building types
        all_types = set()
        for year_data in building_types.values():
            all_types.update(year_data.keys())
        
        all_types = sorted(list(all_types))
        
        # Create data for stacked bar chart
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set3
        
        for i, building_type in enumerate(all_types):
            counts = [building_types.get(year, {}).get(building_type, 0) for year in years]
            
            fig.add_trace(go.Bar(
                x=years,
                y=counts,
                name=building_type.title(),
                marker_color=colors[i % len(colors)]
            ))
        
        # Update layout
        fig.update_layout(
            title='Building Type Distribution Over Time',
            xaxis_title='Year',
            yaxis_title='Number of Buildings',
            barmode='stack',
            template='plotly_white',
            height=500
        )
        
        return fig
    
    def create_density_metrics_chart(self, density_by_year: Dict[int, Dict[str, Any]]) -> go.Figure:
        """
        Create a chart showing density metrics over time.
        
        Args:
            density_by_year: Density metrics by year
            
        Returns:
            Plotly figure with density metrics
        """
        if not density_by_year:
            return go.Figure()
        
        years = sorted(density_by_year.keys())
        
        # Extract metrics
        building_density = [density_by_year[year].get('buildings_per_km2', 0) for year in years]
        road_density = [density_by_year[year].get('road_length_km_per_km2', 0) for year in years]
        coverage_ratio = [density_by_year[year].get('building_coverage_ratio', 0) * 100 for year in years]  # Convert to percentage
        
        # Create subplot
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Building Density (buildings/km²)',
                'Road Density (km/km²)',
                'Building Coverage Ratio (%)',
                'Average Building Size (m²)'
            ),
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )
        
        # Building density
        fig.add_trace(
            go.Scatter(
                x=years,
                y=building_density,
                mode='lines+markers',
                name='Building Density',
                line=dict(color='#2E86AB', width=3),
                marker=dict(size=8)
            ),
            row=1, col=1
        )
        
        # Road density
        fig.add_trace(
            go.Scatter(
                x=years,
                y=road_density,
                mode='lines+markers',
                name='Road Density',
                line=dict(color='#1B4332', width=3),
                marker=dict(size=8)
            ),
            row=1, col=2
        )
        
        # Coverage ratio
        fig.add_trace(
            go.Scatter(
                x=years,
                y=coverage_ratio,
                mode='lines+markers',
                name='Coverage Ratio',
                line=dict(color='#A23B72', width=3),
                marker=dict(size=8)
            ),
            row=2, col=1
        )
        
        # Average building size
        avg_building_size = [density_by_year[year].get('avg_building_area_m2', 0) for year in years]
        fig.add_trace(
            go.Scatter(
                x=years,
                y=avg_building_size,
                mode='lines+markers',
                name='Avg Building Size',
                line=dict(color='#F18F01', width=3),
                marker=dict(size=8)
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title='Urban Density Metrics Over Time',
            height=600,
            showlegend=False,
            template='plotly_white'
        )
        
        # Update all x-axes
        for row in range(1, 3):
            for col in range(1, 3):
                fig.update_xaxes(title_text="Year", row=row, col=col)
        
        return fig
    
    def create_sprawl_analysis_chart(self, sprawl_data: Dict[str, Any]) -> go.Figure:
        """
        Create charts analyzing urban sprawl patterns.
        
        Args:
            sprawl_data: Urban sprawl analysis data
            
        Returns:
            Plotly figure with sprawl analysis
        """
        if 'sprawl_indices' not in sprawl_data or 'years' not in sprawl_data:
            return go.Figure()
        
        years = sprawl_data['years']
        sprawl_indices = sprawl_data['sprawl_indices']
        
        # Extract sprawl metrics
        mean_distances = [sprawl_indices.get(year, {}).get('mean_distance_from_center', 0) / 1000 
                         for year in years]  # Convert to km
        max_distances = [sprawl_indices.get(year, {}).get('max_distance_from_center', 0) / 1000 
                        for year in years]  # Convert to km
        urban_extents = [sprawl_data['urban_extent'].get(year, 0) / 1_000_000 
                        for year in years]  # Convert to km²
        
        # Create subplot
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Mean Distance from Center (km)',
                'Maximum Distance from Center (km)',
                'Urban Extent (km²)',
                'Distance Band Distribution (Latest Year)'
            ),
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # Mean distance from center
        fig.add_trace(
            go.Scatter(
                x=years,
                y=mean_distances,
                mode='lines+markers',
                name='Mean Distance',
                line=dict(color='#2E86AB', width=3),
                marker=dict(size=8)
            ),
            row=1, col=1
        )
        
        # Maximum distance from center
        fig.add_trace(
            go.Scatter(
                x=years,
                y=max_distances,
                mode='lines+markers',
                name='Max Distance',
                line=dict(color='#A23B72', width=3),
                marker=dict(size=8)
            ),
            row=1, col=2
        )
        
        # Urban extent
        fig.add_trace(
            go.Scatter(
                x=years,
                y=urban_extents,
                mode='lines+markers',
                name='Urban Extent',
                line=dict(color='#F18F01', width=3),
                marker=dict(size=8)
            ),
            row=2, col=1
        )
        
        # Distance band distribution for latest year
        if 'distance_bands' in sprawl_data and years:
            latest_year = max(years)
            distance_bands = sprawl_data['distance_bands'].get(latest_year, {})
            
            if distance_bands:
                bands = list(distance_bands.keys())
                counts = list(distance_bands.values())
                
                fig.add_trace(
                    go.Bar(
                        x=bands,
                        y=counts,
                        name='Building Count',
                        marker_color='#1B4332'
                    ),
                    row=2, col=2
                )
        
        # Update layout
        fig.update_layout(
            title='Urban Sprawl Analysis',
            height=600,
            showlegend=False,
            template='plotly_white'
        )
        
        # Update axes
        for row in range(1, 3):
            for col in range(1, 3):
                if not (row == 2 and col == 2):  # Skip the bar chart
                    fig.update_xaxes(title_text="Year", row=row, col=col)
        
        fig.update_xaxes(title_text="Distance Band", row=2, col=2)
        fig.update_yaxes(title_text="Building Count", row=2, col=2)
        
        return fig
    
    def create_comparison_dashboard(self, analysis_results: Dict[str, Any]) -> go.Figure:
        """
        Create a comprehensive comparison dashboard.
        
        Args:
            analysis_results: Complete analysis results
            
        Returns:
            Plotly figure with comparison dashboard
        """
        # Extract data
        quant_data = analysis_results.get('quantitative_analysis', {})
        building_metrics = quant_data.get('building_metrics', {})
        road_metrics = quant_data.get('road_metrics', {})
        
        if 'years' not in building_metrics:
            return go.Figure()
        
        years = building_metrics['years']
        
        # Create subplot with 2x2 layout
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Buildings vs Roads Count',
                'Total Area vs Road Length',
                'Growth Rates Comparison',
                'Key Performance Indicators'
            ),
            specs=[[{"secondary_y": True}, {"secondary_y": True}],
                   [{"type": "bar"}, {"type": "table"}]],
            vertical_spacing=0.15
        )
        
        # Buildings vs Roads count
        building_counts = [building_metrics['building_counts'].get(year, 0) for year in years]
        road_counts = [road_metrics['road_counts'].get(year, 0) for year in years]
        
        fig.add_trace(
            go.Scatter(x=years, y=building_counts, name='Buildings', 
                      line=dict(color='#2E86AB', width=3), marker=dict(size=8)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=years, y=road_counts, name='Roads',
                      line=dict(color='#1B4332', width=3), marker=dict(size=8)),
            row=1, col=1, secondary_y=True
        )
        
        # Total area vs road length
        building_areas = [building_metrics['total_area_m2'].get(year, 0) / 1_000_000 for year in years]
        road_lengths = [road_metrics['total_length_km'].get(year, 0) for year in years]
        
        fig.add_trace(
            go.Scatter(x=years, y=building_areas, name='Building Area (km²)',
                      line=dict(color='#A23B72', width=3), marker=dict(size=8)),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=years, y=road_lengths, name='Road Length (km)',
                      line=dict(color='#52B788', width=3), marker=dict(size=8)),
            row=1, col=2, secondary_y=True
        )
        
        # Growth rates comparison
        if 'growth_rates' in building_metrics:
            growth_rates = building_metrics['growth_rates']
            periods = list(growth_rates.keys())
            building_growth = [growth_rates[period].get('count_growth_percent', 0) for period in periods]
            
            fig.add_trace(
                go.Bar(x=periods, y=building_growth, name='Building Growth (%)',
                      marker_color='#2E86AB'),
                row=2, col=1
            )
        
        if 'growth_rates' in road_metrics:
            road_growth_rates = road_metrics['growth_rates']
            road_growth = [road_growth_rates[period].get('count_growth_percent', 0) for period in periods]
            
            fig.add_trace(
                go.Bar(x=periods, y=road_growth, name='Road Growth (%)',
                      marker_color='#1B4332'),
                row=2, col=1
            )
        
        # KPI Table
        if years:
            latest_year = max(years)
            earliest_year = min(years)
            
            # Calculate KPIs
            total_buildings = building_metrics['building_counts'].get(latest_year, 0)
            total_roads = road_metrics['road_counts'].get(latest_year, 0)
            
            building_change = (building_metrics['building_counts'].get(latest_year, 0) - 
                             building_metrics['building_counts'].get(earliest_year, 0))
            road_change = (road_metrics['road_counts'].get(latest_year, 0) - 
                          road_metrics['road_counts'].get(earliest_year, 0))
            
            # Create table
            fig.add_trace(
                go.Table(
                    header=dict(values=['Metric', 'Value'],
                               fill_color='lightblue',
                               align='left'),
                    cells=dict(values=[
                        ['Total Buildings', 'Total Roads', 'Building Growth', 'Road Growth', 'Analysis Period'],
                        [f'{total_buildings:,}', f'{total_roads:,}', 
                         f'+{building_change:,}', f'+{road_change:,}',
                         f'{earliest_year}-{latest_year}']
                    ],
                    fill_color='white',
                    align='left')
                ),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            title='Urban Growth Comparison Dashboard',
            height=700,
            showlegend=True,
            template='plotly_white'
        )
        
        return fig
    
    def create_summary_statistics_table(self, analysis_results: Dict[str, Any]) -> pd.DataFrame:
        """
        Create a summary statistics table.
        
        Args:
            analysis_results: Complete analysis results
            
        Returns:
            DataFrame with summary statistics
        """
        summary_data = []
        
        # Extract quantitative data
        quant_data = analysis_results.get('quantitative_analysis', {})
        
        if 'building_metrics' in quant_data:
            building_metrics = quant_data['building_metrics']
            years = building_metrics.get('years', [])
            
            for year in years:
                building_count = building_metrics.get('building_counts', {}).get(year, 0)
                building_area = building_metrics.get('total_area_m2', {}).get(year, 0)
                avg_building_size = building_metrics.get('average_building_size_m2', {}).get(year, 0)
                
                summary_data.append({
                    'Year': year,
                    'Metric': 'Buildings',
                    'Count': building_count,
                    'Total Area (km²)': building_area / 1_000_000,
                    'Average Size (m²)': avg_building_size
                })
        
        if 'road_metrics' in quant_data:
            road_metrics = quant_data['road_metrics']
            years = road_metrics.get('years', [])
            
            for year in years:
                road_count = road_metrics.get('road_counts', {}).get(year, 0)
                road_length = road_metrics.get('total_length_km', {}).get(year, 0)
                
                summary_data.append({
                    'Year': year,
                    'Metric': 'Roads',
                    'Count': road_count,
                    'Total Length (km)': road_length,
                    'Average Length (m)': (road_length * 1000 / road_count) if road_count > 0 else 0
                })
        
        return pd.DataFrame(summary_data)
