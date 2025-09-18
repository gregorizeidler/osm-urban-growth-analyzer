# 🏙️ OpenStreetMap Urban Growth Analysis

<div align="center">

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)
![GeoPandas](https://img.shields.io/badge/geopandas-1.0+-orange.svg)

**Sistema de análise de crescimento urbano baseado em dados OpenStreetMap com interface web interativa**

[🚀 Instalação](#-instalação) • [📊 Funcionalidades](#-funcionalidades-implementadas) • [🏗️ Arquitetura](#️-arquitetura-do-sistema) • [📖 API](#-api-principal)

</div>

---

## 🎯 Visão Geral

Este projeto implementa um **pipeline de análise geoespacial** para processamento de dados OpenStreetMap (OSM) e cálculo de métricas urbanas. O sistema coleta dados através da API Overpass, processa geometrias espaciais e gera visualizações interativas através de um dashboard Streamlit.

## 🏗️ Arquitetura do Sistema

```mermaid
flowchart TD
    A[📋 Configuração YAML] --> B[⚙️ ConfigManager]
    B --> C[🔬 UrbanGrowthAnalyzer]
    C --> D[📡 OSMDataCollector]
    C --> E[🔧 DataProcessor]
    C --> F[📈 GrowthMetrics]
    C --> G[🗺️ SpatialAnalyzer]
    
    D --> H[🌐 Overpass API]
    D --> I[💾 CacheManager]
    
    E --> J[✨ Geometria Cleaning]
    E --> K[🏷️ Tag Normalization]
    
    F --> L[🏢 Building Metrics]
    F --> M[🛣️ Road Metrics]
    F --> N[📊 Density Calculations]
    
    G --> O[🔥 Hotspot Detection]
    G --> P[🎯 Clustering Analysis]
    G --> Q[📐 Sprawl Metrics]
    
    C --> R[🗺️ MapVisualizer]
    C --> S[📊 ChartGenerator]
    R --> T[🌍 Folium Maps]
    S --> U[📈 Plotly Charts]
    
    T --> V[🖥️ Streamlit Dashboard]
    U --> V
    
    style A fill:#b3e5fc,stroke:#01579b,stroke-width:2px,color:#000
    style H fill:#ffcc80,stroke:#e65100,stroke-width:2px,color:#000
    style I fill:#d1c4e9,stroke:#4a148c,stroke-width:2px,color:#000
    style V fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px,color:#000
    style C fill:#ffcdd2,stroke:#b71c1c,stroke-width:3px,color:#000
```

## 📁 Estrutura do Projeto

```
🏙️ osmd/
├── 📦 src/osmd/
│   ├── 📡 data/              # Módulo de coleta e processamento
│   │   ├── collector.py      # Interface Overpass API
│   │   ├── processor.py      # Limpeza de dados geoespaciais
│   │   └── cache.py          # Sistema de cache
│   ├── 🔬 analysis/          # Módulo de análise
│   │   ├── analyzer.py       # Orquestrador principal
│   │   ├── metrics.py        # Cálculo de métricas urbanas
│   │   └── spatial.py        # Análise espacial
│   ├── 🎨 visualization/     # Módulo de visualização
│   │   ├── dashboard.py      # Interface Streamlit
│   │   ├── maps.py           # Mapas interativos
│   │   └── charts.py         # Gráficos analíticos
│   └── ⚙️ utils/             # Utilitários
│       ├── config.py         # Gerenciamento de configuração
│       ├── logger.py         # Sistema de logging
│       └── helpers.py        # Funções auxiliares
├── 📋 config.yaml           # Configuração principal
├── 📦 requirements.txt      # Dependências Python
└── 📓 notebooks/            # Jupyter notebooks
```

## 🔄 Fluxo de Processamento

```mermaid
graph LR
    A[🗺️ Bounding Box] --> B[🔍 Overpass Query]
    B --> C[📡 OSM Data Collection]
    C --> D[✅ Geometry Validation]
    D --> E[🏷️ Tag Normalization]
    E --> F[🏗️ Feature Classification]
    F --> G[📊 Metric Calculation]
    G --> H[🎯 Spatial Analysis]
    H --> I[📈 Visualization Generation]
    
    style A fill:#ffcdd2,stroke:#c62828,stroke-width:2px,color:#000
    style C fill:#bbdefb,stroke:#1565c0,stroke-width:2px,color:#000
    style F fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000
    style I fill:#ffe0b2,stroke:#ef6c00,stroke-width:2px,color:#000
```

## 🚀 Funcionalidades Implementadas

### 📡 **Coleta de Dados**
- 🌐 Interface com Overpass API do OpenStreetMap
- 🔄 Queries temporais para dados históricos
- 🚀 Divisão automática de áreas grandes
- 💾 Sistema de cache inteligente
- ⏱️ Rate limiting automático
- 🛡️ Tratamento de erros de rede
- 🎯 Otimização de queries por complexidade

### 🔧 **Processamento de Dados**
- ✅ Validação e limpeza de geometrias
- 🏷️ Normalização de tags OSM
- 🏢 Classificação de tipos de edificação
- 🎯 Filtragem por área e qualidade
- 🗺️ Projeção UTM automática para cálculos precisos

### 📊 **Análise Quantitativa**
- ⏰ Métricas de crescimento temporal
- 📈 Cálculos de densidade urbana com precisão geoespacial
- 🏗️ Análise de compacidade
- 📋 Taxas de crescimento por período
- 📐 Cálculos de área e distância em metros

### 🎯 **Análise Espacial**
- 🔥 Detecção de hotspots de crescimento
- 🎪 Clustering DBSCAN de edificações
- 📐 Análise de sprawl urbano
- 🔗 Métricas de conectividade
- 📏 Análise de fragmentação urbana

### 🎨 **Visualização**
- 🗺️ Mapas interativos com Folium
- 📊 Gráficos analíticos com Plotly
- 🖥️ Dashboard web com Streamlit
- 📤 Exportação de dados (JSON, CSV, GeoJSON)

## 🔄 Pipeline de Dados

```mermaid
sequenceDiagram
    participant C as 📋 ConfigManager
    participant A as 🔬 UrbanGrowthAnalyzer
    participant D as 📡 OSMDataCollector
    participant P as 🔧 DataProcessor
    participant M as 📊 GrowthMetrics
    participant S as 🎯 SpatialAnalyzer
    participant V as 🎨 Visualizer
    
    C->>A: ⚙️ Load configuration
    A->>D: 📡 Request OSM data
    D->>D: 🌐 Query Overpass API
    D->>A: 📦 Return raw GeoDataFrames
    A->>P: 🔧 Process geometries
    P->>P: ✨ Clean & normalize data
    P->>A: 📦 Return processed data
    A->>M: 📊 Calculate metrics
    M->>A: 📈 Return quantitative results
    A->>S: 🎯 Perform spatial analysis
    S->>A: 🗺️ Return spatial results
    A->>V: 🎨 Generate visualizations
    V->>A: 📊 Return maps & charts
```

## 🛠️ Instalação

### 📋 Pré-requisitos
- 🐍 Python 3.8+
- 📦 pip
- 🗺️ Dependências geoespaciais (GDAL, GEOS, PROJ)

### ⚙️ Setup
```bash
# 📥 Clonar repositório
git clone <repository-url>
cd osmd

# 🏠 Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # 🐧 Linux/Mac
# venv\Scripts\activate   # 🪟 Windows

# 📦 Instalar dependências
pip install -r requirements.txt
```

### 🚀 Execução
```bash
# 🖥️ Dashboard web
streamlit run src/osmd/visualization/dashboard.py

# 🔬 Análise programática
python example_analysis.py

# 📓 Jupyter notebook
jupyter notebook notebooks/01_Getting_Started.ipynb
```

## ⚙️ Configuração

O arquivo `config.yaml` define parâmetros do sistema:

```yaml
# 🌐 Configuração da API Overpass
osm:
  overpass_url: "https://overpass-api.de/api/interpreter"
  timeout: 300
  cache_enabled: true

# 🗺️ Área padrão de análise
analysis:
  default_bbox:
    south: -23.6821
    west: -46.9249
    north: -23.4323
    east: -46.3654
  
  comparison_years: [2010, 2015, 2020, 2024]
  
  features:
    buildings: ["building"]
    roads: ["highway"]
    landuse: ["landuse", "amenity"]
```

## 📊 Métricas Calculadas

<div align="center">

| 📈 **Métricas de Crescimento** | 📊 **Métricas de Densidade** | 🎯 **Métricas Espaciais** |
|:---:|:---:|:---:|
| 📋 Contagem de features por ano | 🏢 Edifícios por km² | 🔥 Detecção de hotspots (percentil 80) |
| 📐 Área total construída | 🛣️ Densidade viária (km/km²) | 🎪 Clustering DBSCAN (eps=100m) |
| 📈 Taxa de crescimento percentual | 🏗️ Ratio de cobertura predial | 📍 Distância média do centro urbano |
| ⏰ Crescimento anual médio | 📏 Área média de edificações | 🎯 Índice de compacidade (área/perímetro²) |

</div>

## 💻 API Principal

### 🔬 UrbanGrowthAnalyzer
```python
from osmd import UrbanGrowthAnalyzer, BoundingBox

# 🏗️ Inicializar analisador
analyzer = UrbanGrowthAnalyzer()
bbox = BoundingBox(south=-23.55, west=-46.65, north=-23.54, east=-46.64)

# 🚀 Executar análise
results = analyzer.analyze_urban_growth(
    bbox=bbox,
    years=[2015, 2020, 2024],
    features=['building', 'highway']
)
```

### 📦 Estrutura de Resultados
```python
{
    '📋 metadata': {
        'bbox': tuple,
        'years': list,
        'processing_time_seconds': float
    },
    '📊 quantitative_analysis': {
        'building_metrics': dict,
        'road_metrics': dict,
        'density_by_year': dict
    },
    '🎯 spatial_analysis': {
        'growth_hotspots': dict,
        'urban_sprawl': dict,
        'connectivity': dict
    },
    '📦 processed_data': {
        'buildings': dict,  # 📅 por ano
        'roads': dict,      # 📅 por ano
        'landuse': dict     # 📅 por ano
    }
}
```

## ⚠️ Limitações Conhecidas

### 📅 **Dados Históricos**
- 🔄 Queries temporais com fallback para simulação quando necessário
- 📊 Overpass API histórica limitada para períodos muito antigos
- 🗂️ Para análises de décadas, recomenda-se OSM History Planet files

### ⚡ **Performance**
- 🚀 Divisão automática de áreas grandes para evitar timeouts
- 💾 Sistema de cache otimizado para reduzir requests
- ⏱️ Rate limiting inteligente da Overpass API
- 🎯 Queries otimizadas automaticamente por complexidade

## 📦 Dependências Principais

<div align="center">

| 📚 **Biblioteca** | 🎯 **Função** | 📊 **Versão** |
|:---|:---|:---:|
| 🗺️ geopandas | Manipulação de dados geoespaciais | ≥1.0.0 |
| 🖥️ streamlit | Interface web | ≥1.28.0 |
| 🌍 folium | Mapas interativos | ≥0.15.0 |
| 📊 plotly | Gráficos interativos | ≥5.17.0 |
| 🌐 requests | HTTP requests | ≥2.31.0 |
| 📐 shapely | Operações geométricas | ≥2.0.0 |
| 📋 pandas | Manipulação de dados | ≥2.0.0 |
| 🗺️ pyproj | Projeções cartográficas | ≥3.4.0 |
| 🤖 scikit-learn | Algoritmos de clustering | ≥1.3.0 |

</div>

## 🛠️ Desenvolvimento

### 🧪 **Testes**
```bash
python -m pytest tests/
```

### 🎨 **Linting**
```bash
black src/ tests/
flake8 src/ tests/
```

### 🏗️ **Estrutura de Classes**

```mermaid
classDiagram
    class UrbanGrowthAnalyzer {
        +ConfigManager config
        +analyze_urban_growth() 🚀
        +analyze_specific_area() 🎯
    }
    
    class OSMDataCollector {
        +collect_historical_data() 📅
        +collect_buildings() 🏢
        +collect_roads() 🛣️
    }
    
    class DataProcessor {
        +process_buildings() 🏗️
        +process_roads() 🛤️
        +clean_geometries() ✨
    }
    
    class GrowthMetrics {
        +calculate_building_growth() 📈
        +calculate_road_growth() 🛣️
        +calculate_density_metrics() 📊
    }
    
    class SpatialAnalyzer {
        +detect_growth_hotspots() 🔥
        +analyze_urban_sprawl() 📐
        +detect_building_clusters() 🎪
    }
    
    UrbanGrowthAnalyzer --> OSMDataCollector
    UrbanGrowthAnalyzer --> DataProcessor
    UrbanGrowthAnalyzer --> GrowthMetrics
    UrbanGrowthAnalyzer --> SpatialAnalyzer
    
    style UrbanGrowthAnalyzer fill:#ffcdd2,stroke:#b71c1c,stroke-width:3px,color:#000
    style OSMDataCollector fill:#bbdefb,stroke:#0d47a1,stroke-width:2px,color:#000
    style DataProcessor fill:#c8e6c9,stroke:#1b5e20,stroke-width:2px,color:#000
    style GrowthMetrics fill:#ffe0b2,stroke:#e65100,stroke-width:2px,color:#000
    style SpatialAnalyzer fill:#e1bee7,stroke:#4a148c,stroke-width:2px,color:#000
```

---

<div align="center">

## 📄 Licença

**MIT License** - Ver arquivo LICENSE para detalhes

## 🛠️ Tecnologias

![Python](https://img.shields.io/badge/Backend-Python_3.8+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![OpenStreetMap](https://img.shields.io/badge/Dados-OpenStreetMap-7eaa00?style=for-the-badge&logo=openstreetmap&logoColor=white)
![GeoPandas](https://img.shields.io/badge/Processamento-GeoPandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![Scikit-learn](https://img.shields.io/badge/Análise-Scikit--learn-f7931e?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Plotly](https://img.shields.io/badge/Visualização-Plotly-3f4f75?style=for-the-badge&logo=plotly&logoColor=white)
![Streamlit](https://img.shields.io/badge/Interface-Streamlit-ff4b4b?style=for-the-badge&logo=streamlit&logoColor=white)

---

**🏙️ Desenvolvido para análise urbana baseada em dados abertos**

</div>