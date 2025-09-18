#!/usr/bin/env python3
"""
Convenience script to run the Urban Growth Analysis Dashboard.

This script provides an easy way to launch the Streamlit dashboard
with proper configuration and error handling.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'streamlit',
        'geopandas', 
        'folium',
        'plotly',
        'pandas',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nPlease install missing packages:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def check_config():
    """Check if configuration file exists."""
    config_file = project_root / "config.yaml"
    
    if not config_file.exists():
        print("❌ Configuration file not found: config.yaml")
        print("Please ensure config.yaml exists in the project root.")
        return False
    
    return True

def run_dashboard():
    """Run the Streamlit dashboard."""
    print("🏙️ Urban Growth Analysis Dashboard")
    print("=" * 50)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    # Check configuration
    print("⚙️ Checking configuration...")
    if not check_config():
        sys.exit(1)
    
    print("✅ All checks passed!")
    print("🚀 Starting dashboard...")
    print("\n" + "=" * 50)
    print("Dashboard will be available at: http://localhost:8501")
    print("Press Ctrl+C to stop the dashboard")
    print("=" * 50 + "\n")
    
    # Run Streamlit
    dashboard_script = src_path / "osmd" / "visualization" / "dashboard.py"
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_script),
            "--server.address", "localhost",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start dashboard: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    run_dashboard()
