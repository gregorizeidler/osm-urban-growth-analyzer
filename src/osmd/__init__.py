"""
OpenStreetMap Urban Growth Analysis
A comprehensive toolkit for analyzing urban development using historical OSM data.
"""

__version__ = "1.0.0"
__author__ = "Data Scientist"
__email__ = "analyst@example.com"

from .data import OSMDataCollector, DataProcessor
from .analysis import UrbanGrowthAnalyzer
from .visualization import MapVisualizer, DashboardApp
from .utils import ConfigManager, Logger

__all__ = [
    "OSMDataCollector",
    "DataProcessor", 
    "UrbanGrowthAnalyzer",
    "MapVisualizer",
    "DashboardApp",
    "ConfigManager",
    "Logger"
]
