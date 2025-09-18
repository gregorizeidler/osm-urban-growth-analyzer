"""Streamlit dashboard for urban growth analysis visualization."""

import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import time
import sys
from pathlib import Path

# Add src to Python path for direct execution
current_file = Path(__file__).resolve()
src_path = current_file.parent.parent.parent
sys.path.insert(0, str(src_path))

from osmd.utils import ConfigManager, Logger, BoundingBox
from osmd.analysis import UrbanGrowthAnalyzer
from osmd.visualization.maps import MapVisualizer
from osmd.visualization.charts import ChartGenerator


class DashboardApp:
    """Streamlit dashboard application for urban growth analysis."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Initialize dashboard application.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager or ConfigManager()
        self.logger = Logger("DashboardApp")
        
        # Initialize components
        self.analyzer = UrbanGrowthAnalyzer(self.config)
        self.map_visualizer = MapVisualizer(self.config)
        self.chart_generator = ChartGenerator(self.config)
        
        # Dashboard configuration
        dashboard_config = self.config.get_visualization_config().get('dashboard', {})
        self.title = dashboard_config.get('title', 'Urban Growth Analysis Dashboard')
    
    def run(self):
        """Run the Streamlit dashboard application."""
        st.set_page_config(
            page_title=self.title,
            page_icon="🏙️",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Main title
        st.title(self.title)
        st.markdown("---")
        
        # Sidebar configuration
        self._setup_sidebar()
        
        # Main content based on selected page
        if st.session_state.get('page') == 'Analysis':
            self._show_analysis_page()
        elif st.session_state.get('page') == 'Maps':
            self._show_maps_page()
        elif st.session_state.get('page') == 'Charts':
            self._show_charts_page()
        elif st.session_state.get('page') == 'Data':
            self._show_data_page()
        else:
            self._show_home_page()
    
    def _setup_sidebar(self):
        """Setup sidebar with navigation and configuration options."""
        st.sidebar.title("Navigation")
        
        # Page selection
        pages = ['Home', 'Analysis', 'Maps', 'Charts', 'Data']
        selected_page = st.sidebar.selectbox("Select Page", pages)
        st.session_state['page'] = selected_page
        
        st.sidebar.markdown("---")
        
        # Analysis configuration
        st.sidebar.subheader("Analysis Configuration")
        
        # Bounding box configuration
        st.sidebar.markdown("**Geographic Area**")
        
        # Get default bbox from config
        default_bbox = self.config.get_default_bbox()
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            south = st.number_input("South", value=default_bbox.south, format="%.4f", key="south")
            west = st.number_input("West", value=default_bbox.west, format="%.4f", key="west")
        
        with col2:
            north = st.number_input("North", value=default_bbox.north, format="%.4f", key="north")
            east = st.number_input("East", value=default_bbox.east, format="%.4f", key="east")
        
        st.session_state['bbox'] = BoundingBox(south=south, west=west, north=north, east=east)
        
        # Years selection
        st.sidebar.markdown("**Analysis Years**")
        default_years = self.config.get_comparison_years()
        
        min_year = st.sidebar.number_input("Start Year", min_value=2000, max_value=2024, 
                                          value=min(default_years), key="min_year")
        max_year = st.sidebar.number_input("End Year", min_value=min_year, max_value=2024, 
                                          value=max(default_years), key="max_year")
        
        # Generate year list
        year_step = st.sidebar.selectbox("Year Step", [1, 2, 5], index=1)
        years = list(range(min_year, max_year + 1, year_step))
        st.session_state['years'] = years
        
        # Feature selection
        st.sidebar.markdown("**Features to Analyze**")
        feature_options = ['buildings', 'roads', 'landuse']
        selected_features = st.sidebar.multiselect(
            "Select Features", 
            feature_options, 
            default=['buildings', 'roads']
        )
        st.session_state['features'] = selected_features
        
        st.sidebar.markdown("---")
        
        # Cache management
        st.sidebar.subheader("Cache Management")
        
        if st.sidebar.button("Clear Cache"):
            deleted_count = self.analyzer.clear_cache()
            st.sidebar.success(f"Deleted {deleted_count} cache files")
        
        # Cache statistics
        cache_stats = self.analyzer.get_cache_statistics()
        if cache_stats.get('cache_enabled', False):
            st.sidebar.markdown("**Cache Statistics**")
            for cache_type, stats in cache_stats.get('cache_types', {}).items():
                st.sidebar.text(f"{cache_type}: {stats['file_count']} files")
    
    def _show_home_page(self):
        """Display the home page with project overview."""
        st.header("Welcome to Urban Growth Analysis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            ## About This Project
            
            This dashboard provides comprehensive analysis of urban growth patterns using 
            historical OpenStreetMap (OSM) data. The system analyzes changes in:
            
            - **Buildings**: New construction, demolition, and expansion patterns
            - **Road Networks**: Infrastructure development and connectivity changes  
            - **Land Use**: Changes in land utilization and urban sprawl patterns
            
            ## Key Features
            
            - **Temporal Analysis**: Compare urban features across multiple time periods
            - **Interactive Maps**: Visualize changes with before/after comparisons
            - **Growth Metrics**: Quantitative analysis of urban development
            - **Spatial Analytics**: Hotspot detection and sprawl analysis
            - **Export Capabilities**: Download analysis results and visualizations
            
            ## How to Use
            
            1. **Configure Analysis**: Use the sidebar to set geographic bounds and time periods
            2. **Run Analysis**: Navigate to the Analysis page to process OSM data
            3. **Explore Results**: View interactive maps and charts
            4. **Export Data**: Download results for further analysis
            """)
        
        with col2:
            st.markdown("""
            ## Quick Start
            
            **Current Configuration:**
            """)
            
            bbox = st.session_state.get('bbox')
            years = st.session_state.get('years', [])
            features = st.session_state.get('features', [])
            
            if bbox:
                st.text(f"Area: {bbox.south:.3f}, {bbox.west:.3f} to")
                st.text(f"      {bbox.north:.3f}, {bbox.east:.3f}")
            
            if years:
                st.text(f"Years: {min(years)} - {max(years)}")
                st.text(f"Periods: {len(years)} years")
            
            if features:
                st.text(f"Features: {', '.join(features)}")
            
            st.markdown("---")
            
            if st.button("🚀 Start Analysis", type="primary"):
                st.session_state['page'] = 'Analysis'
                st.rerun()
    
    def _show_analysis_page(self):
        """Display the analysis page with processing controls."""
        st.header("Urban Growth Analysis")
        
        # Analysis controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("**Analysis Configuration**")
            bbox = st.session_state.get('bbox')
            years = st.session_state.get('years', [])
            features = st.session_state.get('features', [])
            
            if bbox and years and features:
                st.success("✅ Configuration Complete")
                st.text(f"Area: {bbox.south:.3f}°, {bbox.west:.3f}° to {bbox.north:.3f}°, {bbox.east:.3f}°")
                st.text(f"Years: {years}")
                st.text(f"Features: {features}")
            else:
                st.error("❌ Please configure analysis parameters in the sidebar")
                return
        
        with col2:
            if st.button("🔍 Run Analysis", type="primary"):
                st.session_state['run_analysis'] = True
        
        with col3:
            if st.button("💾 Load Previous"):
                st.info("Feature coming soon!")
        
        # Run analysis if requested
        if st.session_state.get('run_analysis', False):
            self._run_analysis()
            st.session_state['run_analysis'] = False
    
    def _run_analysis(self):
        """Execute the urban growth analysis."""
        bbox = st.session_state.get('bbox')
        years = st.session_state.get('years')
        features = st.session_state.get('features')
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Start analysis
            status_text.text("🔄 Starting urban growth analysis...")
            progress_bar.progress(10)
            
            # Build feature list
            osm_features = self.config.get_osm_features()
            feature_list = []
            
            for feature_type in features:
                if feature_type == 'buildings':
                    feature_list.extend(osm_features.get('buildings', ['building']))
                elif feature_type == 'roads':
                    feature_list.extend(osm_features.get('roads', ['highway']))
                elif feature_type == 'landuse':
                    feature_list.extend(osm_features.get('landuse', ['landuse']))
            
            progress_bar.progress(20)
            status_text.text("📡 Collecting OSM data...")
            
            # Run analysis
            start_time = time.time()
            results = self.analyzer.analyze_urban_growth(bbox, years, feature_list)
            analysis_time = time.time() - start_time
            
            progress_bar.progress(100)
            status_text.text(f"✅ Analysis completed in {analysis_time:.1f} seconds")
            
            # Store results in session state
            st.session_state['analysis_results'] = results
            
            # Display results summary
            self._display_analysis_summary(results)
            
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            self.logger.error(f"Analysis failed: {e}")
            progress_bar.progress(0)
            status_text.text("❌ Analysis failed")
    
    def _display_analysis_summary(self, results: Dict[str, Any]):
        """Display summary of analysis results."""
        st.markdown("---")
        st.subheader("Analysis Results Summary")
        
        # Extract key metrics
        metadata = results.get('metadata', {})
        quant_data = results.get('quantitative_analysis', {})
        
        # Display metadata
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Analysis Years", 
                     f"{min(metadata.get('years', []))}-{max(metadata.get('years', []))}")
        
        with col2:
            st.metric("Processing Time", 
                     f"{metadata.get('processing_time_seconds', 0):.1f}s")
        
        with col3:
            features_analyzed = len(metadata.get('features', []))
            st.metric("Features Analyzed", features_analyzed)
        
        with col4:
            # Calculate total data points
            data_summary = results.get('data_summary', {})
            total_features = sum(
                year_data.get('total_features', 0) 
                for year_data in data_summary.get('data_by_year', {}).values()
            )
            st.metric("Total Data Points", f"{total_features:,}")
        
        # Display key findings
        if 'building_metrics' in quant_data:
            building_metrics = quant_data['building_metrics']
            
            if 'years' in building_metrics and building_metrics['years']:
                years = building_metrics['years']
                latest_year = max(years)
                earliest_year = min(years)
                
                latest_count = building_metrics.get('building_counts', {}).get(latest_year, 0)
                earliest_count = building_metrics.get('building_counts', {}).get(earliest_year, 0)
                
                st.markdown("### 🏢 Building Analysis")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(f"Buildings ({latest_year})", f"{latest_count:,}")
                
                with col2:
                    growth = latest_count - earliest_count
                    st.metric("Total Growth", f"{growth:+,}")
                
                with col3:
                    growth_rate = ((latest_count - earliest_count) / earliest_count * 100) if earliest_count > 0 else 0
                    st.metric("Growth Rate", f"{growth_rate:+.1f}%")
        
        # Success message with navigation
        st.success("🎉 Analysis completed successfully! Navigate to Maps or Charts to explore the results.")
    
    def _show_maps_page(self):
        """Display the interactive maps page."""
        st.header("Interactive Maps")
        
        # Check if analysis results are available
        if 'analysis_results' not in st.session_state:
            st.warning("⚠️ Please run an analysis first to view maps.")
            if st.button("Go to Analysis"):
                st.session_state['page'] = 'Analysis'
                st.rerun()
            return
        
        results = st.session_state['analysis_results']
        processed_data = results.get('processed_data', {})
        bbox = results['metadata']['bbox']
        
        # Map type selection
        map_types = [
            'Temporal Comparison',
            'Growth Hotspots', 
            'Density Heatmap',
            'Before/After Comparison'
        ]
        
        selected_map = st.selectbox("Select Map Type", map_types)
        
        if selected_map == 'Temporal Comparison':
            self._show_temporal_comparison_map(processed_data, bbox)
        
        elif selected_map == 'Growth Hotspots':
            self._show_growth_hotspots_map(results, bbox)
        
        elif selected_map == 'Density Heatmap':
            self._show_density_heatmap(processed_data, bbox)
        
        elif selected_map == 'Before/After Comparison':
            self._show_before_after_map(processed_data, bbox)
    
    def _show_temporal_comparison_map(self, processed_data: Dict[str, Any], 
                                    bbox: List[float]):
        """Display temporal comparison map."""
        st.subheader("Temporal Comparison Map")
        
        # Feature type selection
        available_features = [key for key in processed_data.keys() 
                            if any(not gdf.empty for gdf in processed_data[key].values())]
        
        if not available_features:
            st.error("No data available for mapping.")
            return
        
        feature_type = st.selectbox("Select Feature Type", available_features)
        
        # Create map
        with st.spinner("Creating temporal comparison map..."):
            map_obj = self.map_visualizer.create_temporal_comparison_map(
                processed_data, tuple(bbox), feature_type
            )
        
        # Display map
        st_folium(map_obj, width=1200, height=600)
    
    def _show_growth_hotspots_map(self, results: Dict[str, Any], bbox: List[float]):
        """Display growth hotspots map."""
        st.subheader("Growth Hotspots Map")
        
        spatial_analysis = results.get('spatial_analysis', {})
        hotspots_data = spatial_analysis.get('growth_hotspots', {})
        
        if not hotspots_data:
            st.error("No hotspots data available. This requires building data.")
            return
        
        # Create map
        with st.spinner("Creating growth hotspots map..."):
            map_obj = self.map_visualizer.create_growth_hotspots_map(
                hotspots_data, tuple(bbox)
            )
        
        # Display map
        st_folium(map_obj, width=1200, height=600)
        
        # Display hotspots statistics
        if 'hotspots' in hotspots_data:
            st.markdown("### Hotspots Statistics")
            
            for period, hotspot_gdf in hotspots_data['hotspots'].items():
                if not hotspot_gdf.empty:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(f"Hotspots ({period})", len(hotspot_gdf))
                    
                    with col2:
                        avg_growth = hotspot_gdf['absolute_growth'].mean()
                        st.metric("Average Growth", f"{avg_growth:.2f}")
                    
                    with col3:
                        max_growth = hotspot_gdf['absolute_growth'].max()
                        st.metric("Maximum Growth", f"{max_growth:.2f}")
    
    def _show_density_heatmap(self, processed_data: Dict[str, Any], bbox: List[float]):
        """Display density heatmap."""
        st.subheader("Density Heatmap")
        
        # Year selection for heatmap
        buildings_data = processed_data.get('buildings', {})
        available_years = [year for year, gdf in buildings_data.items() if not gdf.empty]
        
        if not available_years:
            st.error("No building data available for heatmap.")
            return
        
        selected_year = st.selectbox("Select Year", sorted(available_years))
        buildings_gdf = buildings_data[selected_year]
        
        # Create heatmap
        with st.spinner("Creating density heatmap..."):
            map_obj = self.map_visualizer.create_density_heatmap(
                buildings_gdf, tuple(bbox)
            )
        
        # Display map
        st_folium(map_obj, width=1200, height=600)
        
        # Display statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Buildings", f"{len(buildings_gdf):,}")
        
        with col2:
            if 'area_m2' in buildings_gdf.columns:
                total_area = buildings_gdf['area_m2'].sum() / 1_000_000  # Convert to km²
                st.metric("Total Area", f"{total_area:.2f} km²")
        
        with col3:
            # Calculate approximate area from bbox
            lat_diff = bbox[2] - bbox[0]  # north - south
            lon_diff = bbox[3] - bbox[1]  # east - west
            area_km2 = lat_diff * lon_diff * 111.32 ** 2  # Rough conversion
            
            density = len(buildings_gdf) / area_km2 if area_km2 > 0 else 0
            st.metric("Density", f"{density:.1f}/km²")
    
    def _show_before_after_map(self, processed_data: Dict[str, Any], bbox: List[float]):
        """Display before/after comparison map."""
        st.subheader("Before/After Comparison")
        
        # Feature and year selection
        available_features = [key for key in processed_data.keys() 
                            if len([gdf for gdf in processed_data[key].values() if not gdf.empty]) >= 2]
        
        if not available_features:
            st.error("Need at least 2 time periods with data for before/after comparison.")
            return
        
        feature_type = st.selectbox("Feature Type", available_features)
        feature_data = processed_data[feature_type]
        
        available_years = sorted([year for year, gdf in feature_data.items() if not gdf.empty])
        
        if len(available_years) < 2:
            st.error("Need at least 2 years with data for comparison.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            before_year = st.selectbox("Before Year", available_years[:-1])
        
        with col2:
            after_years = [year for year in available_years if year > before_year]
            after_year = st.selectbox("After Year", after_years)
        
        # Create comparison map
        with st.spinner("Creating before/after comparison map..."):
            map_obj = self.map_visualizer.create_before_after_map(
                feature_data[before_year],
                feature_data[after_year],
                before_year,
                after_year,
                tuple(bbox),
                feature_type
            )
        
        # Display map
        st_folium(map_obj, width=1200, height=600)
    
    def _show_charts_page(self):
        """Display the charts and analytics page."""
        st.header("Charts & Analytics")
        
        # Check if analysis results are available
        if 'analysis_results' not in st.session_state:
            st.warning("⚠️ Please run an analysis first to view charts.")
            if st.button("Go to Analysis"):
                st.session_state['page'] = 'Analysis'
                st.rerun()
            return
        
        results = st.session_state['analysis_results']
        quant_data = results.get('quantitative_analysis', {})
        
        # Chart selection
        chart_types = [
            'Growth Timeline',
            'Growth Rates',
            'Building Types Distribution',
            'Density Metrics',
            'Urban Sprawl Analysis',
            'Comparison Dashboard'
        ]
        
        selected_chart = st.selectbox("Select Chart Type", chart_types)
        
        if selected_chart == 'Growth Timeline':
            self._show_growth_timeline_chart(quant_data)
        
        elif selected_chart == 'Growth Rates':
            self._show_growth_rates_chart(quant_data)
        
        elif selected_chart == 'Building Types Distribution':
            self._show_building_types_chart(quant_data)
        
        elif selected_chart == 'Density Metrics':
            self._show_density_metrics_chart(quant_data)
        
        elif selected_chart == 'Urban Sprawl Analysis':
            self._show_sprawl_analysis_chart(results)
        
        elif selected_chart == 'Comparison Dashboard':
            self._show_comparison_dashboard(results)
    
    def _show_growth_timeline_chart(self, quant_data: Dict[str, Any]):
        """Display growth timeline chart."""
        st.subheader("Growth Timeline")
        
        building_metrics = quant_data.get('building_metrics', {})
        road_metrics = quant_data.get('road_metrics', {})
        
        if not building_metrics and not road_metrics:
            st.error("No growth data available.")
            return
        
        fig = self.chart_generator.create_growth_timeline_chart(
            building_metrics, road_metrics
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_growth_rates_chart(self, quant_data: Dict[str, Any]):
        """Display growth rates chart."""
        st.subheader("Growth Rates by Period")
        
        building_metrics = quant_data.get('building_metrics', {})
        
        if 'growth_rates' not in building_metrics:
            st.error("No growth rate data available.")
            return
        
        fig = self.chart_generator.create_growth_rate_chart(building_metrics)
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_building_types_chart(self, quant_data: Dict[str, Any]):
        """Display building types distribution chart."""
        st.subheader("Building Types Distribution")
        
        building_metrics = quant_data.get('building_metrics', {})
        
        if 'building_types' not in building_metrics:
            st.error("No building type data available.")
            return
        
        fig = self.chart_generator.create_building_type_distribution_chart(building_metrics)
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_density_metrics_chart(self, quant_data: Dict[str, Any]):
        """Display density metrics chart."""
        st.subheader("Urban Density Metrics")
        
        density_by_year = quant_data.get('density_by_year', {})
        
        if not density_by_year:
            st.error("No density data available.")
            return
        
        fig = self.chart_generator.create_density_metrics_chart(density_by_year)
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_sprawl_analysis_chart(self, results: Dict[str, Any]):
        """Display urban sprawl analysis chart."""
        st.subheader("Urban Sprawl Analysis")
        
        spatial_analysis = results.get('spatial_analysis', {})
        sprawl_data = spatial_analysis.get('urban_sprawl', {})
        
        if not sprawl_data:
            st.error("No sprawl analysis data available.")
            return
        
        fig = self.chart_generator.create_sprawl_analysis_chart(sprawl_data)
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_comparison_dashboard(self, results: Dict[str, Any]):
        """Display comprehensive comparison dashboard."""
        st.subheader("Comparison Dashboard")
        
        fig = self.chart_generator.create_comparison_dashboard(results)
        st.plotly_chart(fig, use_container_width=True)
    
    def _show_data_page(self):
        """Display the data exploration and export page."""
        st.header("Data Exploration & Export")
        
        # Check if analysis results are available
        if 'analysis_results' not in st.session_state:
            st.warning("⚠️ Please run an analysis first to explore data.")
            if st.button("Go to Analysis"):
                st.session_state['page'] = 'Analysis'
                st.rerun()
            return
        
        results = st.session_state['analysis_results']
        
        # Data exploration tabs
        tab1, tab2, tab3 = st.tabs(["📊 Summary Statistics", "🗺️ Raw Data", "📥 Export"])
        
        with tab1:
            self._show_summary_statistics(results)
        
        with tab2:
            self._show_raw_data_exploration(results)
        
        with tab3:
            self._show_export_options(results)
    
    def _show_summary_statistics(self, results: Dict[str, Any]):
        """Display summary statistics table."""
        st.subheader("Summary Statistics")
        
        # Create summary table
        summary_df = self.chart_generator.create_summary_statistics_table(results)
        
        if not summary_df.empty:
            st.dataframe(summary_df, use_container_width=True)
        else:
            st.info("No summary statistics available.")
    
    def _show_raw_data_exploration(self, results: Dict[str, Any]):
        """Display raw data exploration interface."""
        st.subheader("Raw Data Exploration")
        
        processed_data = results.get('processed_data', {})
        
        # Feature type selection
        available_features = list(processed_data.keys())
        
        if not available_features:
            st.error("No processed data available.")
            return
        
        feature_type = st.selectbox("Select Feature Type", available_features, key="data_feature")
        feature_data = processed_data[feature_type]
        
        # Year selection
        available_years = sorted([year for year, gdf in feature_data.items() if not gdf.empty])
        
        if not available_years:
            st.error(f"No data available for {feature_type}.")
            return
        
        selected_year = st.selectbox("Select Year", available_years, key="data_year")
        gdf = feature_data[selected_year]
        
        # Display data
        st.markdown(f"**{feature_type.title()} data for {selected_year}**")
        st.markdown(f"Total records: {len(gdf):,}")
        
        # Show sample of data
        if not gdf.empty:
            # Convert to regular DataFrame for display (drop geometry for readability)
            display_df = gdf.drop('geometry', axis=1) if 'geometry' in gdf.columns else gdf
            
            # Show first few rows
            st.dataframe(display_df.head(100), use_container_width=True)
            
            # Basic statistics
            if len(display_df.select_dtypes(include=[np.number]).columns) > 0:
                st.markdown("**Numeric Column Statistics**")
                st.dataframe(display_df.describe(), use_container_width=True)
    
    def _show_export_options(self, results: Dict[str, Any]):
        """Display data export options."""
        st.subheader("Export Data")
        
        st.markdown("""
        Export your analysis results in various formats for further analysis or reporting.
        """)
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Available Exports:**")
            
            # Analysis results (JSON)
            if st.button("📄 Export Analysis Results (JSON)"):
                self._export_analysis_results(results)
            
            # Summary statistics (CSV)
            if st.button("📊 Export Summary Statistics (CSV)"):
                self._export_summary_statistics(results)
            
        with col2:
            st.markdown("**Processed Data:**")
            
            # Processed data (GeoJSON)
            if st.button("🗺️ Export Processed Data (GeoJSON)"):
                self._export_processed_data(results)
            
            # Maps (HTML)
            if st.button("🌍 Export Interactive Maps (HTML)"):
                st.info("Feature coming soon!")
    
    def _export_analysis_results(self, results: Dict[str, Any]):
        """Export analysis results as JSON."""
        # Remove processed_data from export (too large)
        export_data = {k: v for k, v in results.items() if k != 'processed_data'}
        
        import json
        json_str = json.dumps(export_data, indent=2, default=str)
        
        st.download_button(
            label="Download Analysis Results",
            data=json_str,
            file_name="urban_growth_analysis_results.json",
            mime="application/json"
        )
    
    def _export_summary_statistics(self, results: Dict[str, Any]):
        """Export summary statistics as CSV."""
        summary_df = self.chart_generator.create_summary_statistics_table(results)
        
        if not summary_df.empty:
            csv = summary_df.to_csv(index=False)
            st.download_button(
                label="Download Summary Statistics",
                data=csv,
                file_name="urban_growth_summary_statistics.csv",
                mime="text/csv"
            )
        else:
            st.error("No summary statistics to export.")
    
    def _export_processed_data(self, results: Dict[str, Any]):
        """Export processed data as GeoJSON."""
        st.info("Select specific dataset to export:")
        
        processed_data = results.get('processed_data', {})
        
        for feature_type, feature_data in processed_data.items():
            for year, gdf in feature_data.items():
                if not gdf.empty:
                    if st.button(f"Export {feature_type.title()} {year}"):
                        geojson_str = gdf.to_json()
                        
                        st.download_button(
                            label=f"Download {feature_type.title()} {year}",
                            data=geojson_str,
                            file_name=f"{feature_type}_{year}.geojson",
                            mime="application/json",
                            key=f"export_{feature_type}_{year}"
                        )


def run_dashboard():
    """Run the Streamlit dashboard application."""
    app = DashboardApp()
    app.run()


if __name__ == "__main__":
    run_dashboard()
