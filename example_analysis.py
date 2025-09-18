#!/usr/bin/env python3
"""
Example script demonstrating programmatic usage of the Urban Growth Analysis system.

This script shows how to use the OSM Urban Growth Analysis toolkit programmatically
without the Streamlit dashboard interface.
"""

import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from osmd import UrbanGrowthAnalyzer, ConfigManager
from osmd.utils import BoundingBox, Logger
from osmd.visualization import MapVisualizer, ChartGenerator

def main():
    """Run example urban growth analysis."""
    
    # Initialize logger
    logger = Logger("ExampleAnalysis")
    logger.info("Starting example urban growth analysis")
    
    # Initialize components
    config = ConfigManager()
    analyzer = UrbanGrowthAnalyzer(config)
    map_visualizer = MapVisualizer(config)
    chart_generator = ChartGenerator(config)
    
    # Define analysis parameters
    # Example: São Paulo city center
    sao_paulo_bbox = BoundingBox(
        south=-23.6821,
        west=-46.9249, 
        north=-23.4323,
        east=-46.3654
    )
    
    # Analysis years
    years = [2015, 2020, 2024]
    
    # Features to analyze
    features = ['building', 'highway', 'landuse']
    
    logger.info(f"Analyzing area: {sao_paulo_bbox.to_tuple()}")
    logger.info(f"Years: {years}")
    logger.info(f"Features: {features}")
    
    try:
        # Run comprehensive analysis
        logger.info("Starting comprehensive urban growth analysis...")
        results = analyzer.analyze_urban_growth(
            bbox=sao_paulo_bbox,
            years=years,
            features=features
        )
        
        # Display key results
        print("\n" + "="*60)
        print("🏙️ URBAN GROWTH ANALYSIS RESULTS")
        print("="*60)
        
        # Metadata
        metadata = results['metadata']
        print(f"\n📊 Analysis Overview:")
        print(f"   Area: {metadata['bbox']}")
        print(f"   Years: {metadata['years']}")
        print(f"   Processing time: {metadata['processing_time_seconds']:.1f} seconds")
        
        # Building metrics
        quant_data = results.get('quantitative_analysis', {})
        building_metrics = quant_data.get('building_metrics', {})
        
        if 'building_counts' in building_metrics:
            print(f"\n🏢 Building Analysis:")
            building_counts = building_metrics['building_counts']
            
            for year in sorted(building_counts.keys()):
                count = building_counts[year]
                print(f"   {year}: {count:,} buildings")
            
            # Growth rates
            if 'growth_rates' in building_metrics:
                print(f"\n📈 Building Growth Rates:")
                growth_rates = building_metrics['growth_rates']
                
                for period, rates in growth_rates.items():
                    count_growth = rates.get('count_growth_percent', 0)
                    area_growth = rates.get('area_growth_percent', 0)
                    print(f"   {period}: {count_growth:+.1f}% count, {area_growth:+.1f}% area")
        
        # Road metrics
        road_metrics = quant_data.get('road_metrics', {})
        
        if 'road_counts' in road_metrics:
            print(f"\n🛣️ Road Network Analysis:")
            road_counts = road_metrics['road_counts']
            road_lengths = road_metrics.get('total_length_km', {})
            
            for year in sorted(road_counts.keys()):
                count = road_counts[year]
                length = road_lengths.get(year, 0)
                print(f"   {year}: {count:,} roads, {length:.1f} km total length")
        
        # Density metrics
        if 'density_by_year' in quant_data:
            print(f"\n🏘️ Urban Density Metrics:")
            density_data = quant_data['density_by_year']
            
            for year in sorted(density_data.keys()):
                metrics = density_data[year]
                building_density = metrics.get('buildings_per_km2', 0)
                road_density = metrics.get('road_length_km_per_km2', 0)
                coverage = metrics.get('building_coverage_ratio', 0) * 100
                
                print(f"   {year}: {building_density:.1f} buildings/km², "
                      f"{road_density:.1f} km roads/km², "
                      f"{coverage:.1f}% coverage")
        
        # Spatial analysis
        spatial_data = results.get('spatial_analysis', {})
        
        if 'growth_hotspots' in spatial_data:
            hotspots_data = spatial_data['growth_hotspots']
            
            if 'hotspots' in hotspots_data:
                print(f"\n🔥 Growth Hotspots:")
                hotspots = hotspots_data['hotspots']
                
                for period, hotspot_gdf in hotspots.items():
                    if not hotspot_gdf.empty:
                        avg_growth = hotspot_gdf['absolute_growth'].mean()
                        max_growth = hotspot_gdf['absolute_growth'].max()
                        print(f"   {period}: {len(hotspot_gdf)} hotspots, "
                              f"avg growth: {avg_growth:.2f}, max: {max_growth:.2f}")
        
        if 'urban_sprawl' in spatial_data:
            sprawl_data = spatial_data['urban_sprawl']
            
            if 'sprawl_indices' in sprawl_data:
                print(f"\n🌆 Urban Sprawl Analysis:")
                sprawl_indices = sprawl_data['sprawl_indices']
                
                for year in sorted(sprawl_indices.keys()):
                    indices = sprawl_indices[year]
                    mean_dist = indices.get('mean_distance_from_center', 0) / 1000  # Convert to km
                    max_dist = indices.get('max_distance_from_center', 0) / 1000
                    building_count = indices.get('buildings_count', 0)
                    
                    print(f"   {year}: {building_count:,} buildings, "
                          f"mean distance: {mean_dist:.1f} km, "
                          f"max distance: {max_dist:.1f} km")
        
        print(f"\n" + "="*60)
        print("✅ Analysis completed successfully!")
        
        # Generate example visualizations
        print(f"\n🗺️ Generating example visualizations...")
        
        # Create temporal comparison map
        processed_data = results.get('processed_data', {})
        if processed_data.get('buildings'):
            bbox_tuple = metadata['bbox']
            temporal_map = map_visualizer.create_temporal_comparison_map(
                processed_data, bbox_tuple, 'buildings'
            )
            
            # Save map
            output_dir = project_root / "output"
            output_dir.mkdir(exist_ok=True)
            
            temporal_map.save(str(output_dir / "temporal_comparison_map.html"))
            logger.info(f"Saved temporal comparison map to: {output_dir}/temporal_comparison_map.html")
        
        # Create growth timeline chart
        if building_metrics and road_metrics:
            timeline_chart = chart_generator.create_growth_timeline_chart(
                building_metrics, road_metrics
            )
            
            timeline_chart.write_html(str(output_dir / "growth_timeline_chart.html"))
            logger.info(f"Saved growth timeline chart to: {output_dir}/growth_timeline_chart.html")
        
        # Export results
        import json
        
        # Remove processed_data for export (too large)
        export_results = {k: v for k, v in results.items() if k != 'processed_data'}
        
        with open(output_dir / "analysis_results.json", 'w') as f:
            json.dump(export_results, f, indent=2, default=str)
        
        logger.info(f"Exported analysis results to: {output_dir}/analysis_results.json")
        
        print(f"\n📁 Output files saved to: {output_dir}")
        print(f"   - temporal_comparison_map.html")
        print(f"   - growth_timeline_chart.html") 
        print(f"   - analysis_results.json")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"\n❌ Analysis failed: {e}")
        sys.exit(1)

def example_custom_analysis():
    """Example of custom analysis with specific parameters."""
    
    logger = Logger("CustomAnalysis")
    
    # Initialize analyzer
    analyzer = UrbanGrowthAnalyzer()
    
    # Define a smaller area for faster processing
    custom_bbox = BoundingBox(
        south=-23.550,
        west=-46.640,
        north=-23.540,
        east=-46.630
    )
    
    logger.info("Running custom analysis on smaller area...")
    
    # Analyze only buildings for recent years
    results = analyzer.analyze_specific_area(
        bbox=custom_bbox,
        years=[2020, 2024],
        feature_types=['buildings']
    )
    
    # Display results
    building_metrics = results['quantitative_analysis']['building_metrics']
    
    print(f"\n🏢 Custom Building Analysis Results:")
    print(f"   Area: {custom_bbox.to_tuple()}")
    
    if 'building_counts' in building_metrics:
        counts = building_metrics['building_counts']
        for year, count in counts.items():
            print(f"   {year}: {count:,} buildings")
        
        if len(counts) >= 2:
            years = sorted(counts.keys())
            growth = counts[years[-1]] - counts[years[0]]
            growth_rate = (growth / counts[years[0]] * 100) if counts[years[0]] > 0 else 0
            print(f"   Growth: {growth:+,} buildings ({growth_rate:+.1f}%)")

if __name__ == "__main__":
    print("🏙️ Urban Growth Analysis - Example Script")
    print("=" * 50)
    
    # Run main analysis
    main()
    
    print(f"\n" + "-" * 50)
    
    # Run custom analysis example
    example_custom_analysis()
    
    print(f"\n✨ Example analysis completed!")
    print(f"Run 'python run_dashboard.py' to explore results interactively.")
