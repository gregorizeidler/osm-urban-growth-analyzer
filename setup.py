"""Setup script for the OpenStreetMap Urban Growth Analysis package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt', 'r') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="osm-urban-growth-analysis",
    version="1.0.0",
    author="Data Scientist",
    author_email="analyst@example.com",
    description="Comprehensive urban growth analysis using OpenStreetMap historical data",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/seu-usuario/osmd",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Visualization",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "jupyter>=1.0.0",
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "notebooks": [
            "jupyter>=1.0.0",
            "ipykernel>=6.0.0",
            "ipywidgets>=8.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "osmd-dashboard=osmd.visualization.dashboard:run_dashboard",
        ],
    },
    include_package_data=True,
    package_data={
        "osmd": [
            "config.yaml",
            "assets/*",
        ],
    },
    keywords=[
        "urban-planning",
        "openstreetmap",
        "geospatial-analysis", 
        "urban-growth",
        "gis",
        "data-visualization",
        "streamlit",
        "spatial-analysis"
    ],
    project_urls={
        "Bug Reports": "https://github.com/seu-usuario/osmd/issues",
        "Source": "https://github.com/seu-usuario/osmd",
        "Documentation": "https://github.com/seu-usuario/osmd/wiki",
    },
)
