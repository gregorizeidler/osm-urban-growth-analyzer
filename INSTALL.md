# 🚀 Guia de Instalação - OpenStreetMap Urban Growth Analysis

Este guia fornece instruções detalhadas para instalar e configurar o sistema de análise de crescimento urbano.

## 📋 Pré-requisitos

### Sistema Operacional
- **Linux/Ubuntu**: Recomendado para melhor performance
- **macOS**: Totalmente compatível
- **Windows**: Compatível (requer algumas configurações adicionais)

### Software Necessário
- **Python 3.8+**: Versão mínima requerida
- **pip**: Gerenciador de pacotes Python
- **Git**: Para clonagem do repositório
- **Conexão com Internet**: Para acessar dados do OpenStreetMap

### Dependências do Sistema

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip python3-venv
sudo apt-get install -y gdal-bin libgdal-dev libspatialindex-dev
sudo apt-get install -y build-essential
```

#### CentOS/RHEL/Fedora
```bash
sudo yum install -y python3-devel python3-pip
sudo yum install -y gdal gdal-devel spatialindex-devel
sudo yum install -y gcc gcc-c++ make
```

#### macOS
```bash
# Instalar Homebrew se não estiver instalado
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar dependências
brew install python3 gdal spatialindex
```

#### Windows
```bash
# Instalar Python 3.8+ do site oficial: https://www.python.org/downloads/
# Instalar Visual Studio Build Tools
# Instalar GDAL: https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal
```

## 🛠️ Instalação

### 1. Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/osmd.git
cd osmd
```

### 2. Criar Ambiente Virtual

```bash
# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\\Scripts\\activate
```

### 3. Instalar Dependências

```bash
# Atualizar pip
pip install --upgrade pip

# Instalar dependências principais
pip install -r requirements.txt

# Para desenvolvimento (opcional)
pip install -r requirements-dev.txt
```

### 4. Configuração Inicial

```bash
# Copiar arquivo de configuração
cp config.yaml config_local.yaml

# Editar configurações locais (opcional)
nano config_local.yaml  # ou seu editor preferido
```

### 5. Verificar Instalação

```bash
# Testar importações
python3 -c "import sys; sys.path.insert(0, 'src'); from osmd import UrbanGrowthAnalyzer; print('✅ Instalação bem-sucedida!')"

# Executar exemplo rápido
python3 example_analysis.py
```

## 🚀 Executando o Sistema

### Dashboard Web (Recomendado)

```bash
# Executar dashboard Streamlit
python3 run_dashboard.py

# Ou diretamente:
streamlit run src/osmd/visualization/dashboard.py
```

O dashboard estará disponível em: `http://localhost:8501`

### Uso Programático

```bash
# Executar análise de exemplo
python3 example_analysis.py

# Executar notebook Jupyter
jupyter notebook notebooks/01_Getting_Started.ipynb
```

## 🔧 Configuração Avançada

### Configuração de Cache

O sistema usa cache para otimizar performance. Configure em `config.yaml`:

```yaml
osm:
  cache_enabled: true
  cache_dir: "./data/cache"
  timeout: 300
```

### Configuração de Banco de Dados (Opcional)

Para análises grandes, configure PostgreSQL com PostGIS:

```yaml
database:
  host: localhost
  port: 5432
  name: osm_urban_growth
  user: postgres
  password: sua_senha
```

### Configuração de Proxy (Se Necessário)

```bash
export HTTP_PROXY=http://seu-proxy:porta
export HTTPS_PROXY=https://seu-proxy:porta
```

## 🐳 Instalação com Docker (Alternativa)

### Dockerfile (criar se necessário)

```dockerfile
FROM python:3.9-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \\
    gdal-bin libgdal-dev libspatialindex-dev \\
    build-essential && \\
    rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /app

# Copiar arquivos
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Expor porta do Streamlit
EXPOSE 8501

# Comando padrão
CMD ["streamlit", "run", "src/osmd/visualization/dashboard.py", "--server.address", "0.0.0.0"]
```

### Executar com Docker

```bash
# Construir imagem
docker build -t osmd .

# Executar container
docker run -p 8501:8501 osmd
```

## 🔍 Solução de Problemas

### Erro: "ModuleNotFoundError: No module named 'geopandas'"

```bash
# Reinstalar geopandas
pip uninstall geopandas
pip install geopandas

# Se persistir, instalar dependências separadamente
pip install fiona shapely pyproj rtree
pip install geopandas
```

### Erro: "GDAL not found"

```bash
# Ubuntu/Debian
sudo apt-get install gdal-bin libgdal-dev

# macOS
brew install gdal

# Verificar instalação
gdal-config --version
```

### Erro: "Microsoft Visual C++ 14.0 is required" (Windows)

1. Instalar Visual Studio Build Tools
2. Ou instalar pacotes pré-compilados:
   ```bash
   pip install --find-links https://www.lfd.uci.edu/~gohlke/pythonlibs/ geopandas
   ```

### Erro de Timeout do Overpass API

Ajustar timeout em `config.yaml`:

```yaml
osm:
  timeout: 600  # Aumentar para 10 minutos
```

### Problemas de Memória

Para áreas grandes, configurar limites:

```yaml
processing:
  chunk_size: 5000
  memory_limit_gb: 4
```

## 📊 Teste de Performance

### Teste Básico

```bash
python3 -c "
from src.osmd import UrbanGrowthAnalyzer
from src.osmd.utils import BoundingBox
import time

analyzer = UrbanGrowthAnalyzer()
bbox = BoundingBox(-23.55, -46.65, -23.54, -46.64)

start = time.time()
results = analyzer.analyze_urban_growth(bbox, [2020, 2024], ['building'])
end = time.time()

print(f'Análise concluída em {end-start:.1f} segundos')
"
```

### Benchmark Completo

```bash
python3 -c "
import time
import psutil
from src.osmd import UrbanGrowthAnalyzer

print('Sistema:', psutil.cpu_count(), 'CPUs,', psutil.virtual_memory().total // 1024**3, 'GB RAM')
print('Executando benchmark...')
# Adicionar código de benchmark aqui
"
```

## 📚 Recursos Adicionais

### Documentação
- **README.md**: Visão geral do projeto
- **notebooks/**: Exemplos interativos
- **docs/**: Documentação técnica detalhada

### Comunidade
- **Issues**: Reportar bugs e solicitar recursos
- **Discussions**: Perguntas e discussões
- **Wiki**: Documentação da comunidade

### Suporte
- **Email**: support@osmd-project.org
- **Discord**: [Link do servidor]
- **Stack Overflow**: Tag `osm-urban-growth`

---

## ✅ Checklist de Instalação

- [ ] Python 3.8+ instalado
- [ ] Dependências do sistema instaladas
- [ ] Repositório clonado
- [ ] Ambiente virtual criado e ativado
- [ ] Dependências Python instaladas
- [ ] Configuração copiada
- [ ] Teste de importação bem-sucedido
- [ ] Dashboard executando
- [ ] Análise de exemplo funcionando

**🎉 Parabéns! O sistema está pronto para uso!**
