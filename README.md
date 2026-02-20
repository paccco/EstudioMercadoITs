# 🚀 Job Market Insight: España (IT Edition)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/-Raspberry_Pi-C51A4A?style=for-the-badge&logo=Raspberry-Pi&logoColor=white)
![LinkedIn](https://img.shields.io/badge/linkedin-%230077B5.svg?style=for-the-badge&logo=linkedin&logoColor=white)
![Charts](https://img.shields.io/badge/Matplotlib-%23ffffff.svg?style=for-the-badge&logo=Matplotlib&logoColor=black)

Este proyecto automatiza la extracción de ofertas de empleo en el sector tecnológico para **Málaga** y **Granada**, analizando tanto el mercado local como el nacional en remoto.

El objetivo principal es identificar el **stack tecnológico real** que las empresas demandan para perfiles **Junior (Entry Level)** en 2026.

---

## 🤖 Automatización con Raspberry Pi (Edge Scraping)

Para garantizar una base de datos robusta sin intervención manual, el sistema se ha desplegado en una **Raspberry Pi Zero 2 W**, con procesos optimizados para hardware limitado:

* **Extracción Diaria (`Scrapping.py`):** Ejecución automatizada vía `cron` cada madrugada. Captura ofertas de las últimas 24h y las organiza en carpetas diarias dentro de `scraps/`.
* **Consolidación Mensual (`Join.py`):** El día 1 de cada mes, el sistema fusiona los CSVs del mes anterior, realiza una deduplicación profunda y genera un **Dataset Maestro**, eliminando los archivos temporales para optimizar el almacenamiento.

---

## 📊 Insights del Mercado (Febrero 2026)

### 🔝 Top 5 Tecnologías Globales (All Levels)
| Tecnología | Menciones | Rol en el Mercado |
| :--- | :--- | :--- |
| **Python** | 547 | Dominio absoluto en Data, Scripting y Backend |
| **SQL** | 390 | Base de datos: el requisito transversal por excelencia |
| **CI/CD** | 299 | Automatización de despliegue en casi el 55% de las ofertas |
| **AWS** | 285 | El proveedor Cloud preferido por las empresas |
| **Docker** | 259 | Estándar de facto para contenedorización |

### 👶 Perfil Junior / Entry Level
| Tecnología | Menciones | Observación |
| :--- | :--- | :--- |
| **Python** | 121 | La puerta de entrada más común al sector |
| **Kubernetes** | 71 | Tendencia crítica: ya se exige orquestación a Juniors |
| **Docker** | 67 | Conocimiento básico de contenedores indispensable |
| **CI/CD** | 64 | DevOps culture desde el primer día |
| **Go** | 63 | Sorprendente auge de Go para nuevos perfiles en sistemas/backend |

* **Análisis de Tendencia:** Se observa una "DevOps-ización" del perfil Junior. Ya no basta con saber programar (Python); el mercado exige que el desarrollador sepa dónde y cómo corre su código (**Kubernetes**, **Docker**, **CI/CD**).
* **Málaga vs Granada:** Málaga mantiene el liderazgo en volumen de ofertas Cloud, mientras que Granada muestra una especialización notable en arquitecturas eficientes (Go).

---

## 🛠️ Tecnologías y Librerías
* **Scraping:** `python-jobspy` (LinkedIn API Wrapper)
* **Automatización:** `Crontab` (Linux) & `Logging`
* **Análisis de Datos:** `Pandas`, `NumPy`, `Scikit-Learn`
* **Procesamiento de Texto:** `Regex` & `NLTK` (Stopwords)
* **Visualización:** `Matplotlib` & `Seaborn`

---

## 📁 Estructura del Proyecto
```text
├── scraps/                 # CSVs crudos organizados por fechas (DD-MM-YYYY o MM-YYYY)
├── logs/                   # Registros de ejecución de tareas programadas
├── Scrapping.py            # Script de extracción diaria (Producción)
├── Join.py                 # Script de consolidación mensual (Producción)
├── Tratamiento.ipynb       # Notebook de limpieza y procesamiento
└── README.md               # Documentación
```
## ⚙️ Automatización (Crontab Configuration)

Para garantizar la autonomía del proyecto en la **Raspberry Pi Zero 2 W**, se han programado dos tareas principales. Estas incluyen flags de optimización de memoria para evitar colapsos en los 512MB de RAM del dispositivo.

### 1. Extracción Diaria (Scraping)
Se ejecuta todas las madrugadas para capturar las nuevas ofertas publicadas en las últimas 24 horas.

```bash
00 05 * * * cd /home/pacc/Desktop/scrapping && MALLOC_TRIM_THRESHOLD_=65536 PYTHONMALLOC=malloc ./env/bin/python3 -O Scrapping.py >> logs/cron_diario_$(date +\%d-\%m-\%Y).log 2>&1
```

### 2. Consolidación mensual de datasets (Join)
```bash
00 01 1 * * cd /home/pacc/Desktop/scrapping && MALLOC_TRIM_THRESHOLD_=65536 PYTHONMALLOC=malloc ./env/bin/python3 -O Join.py >> logs/cron_mensual_$(date +\%m-\%Y).log 2>&1
```
## Ideas futuras

Se pretende añadir un NLP para tratamiento del texto de las ofertas y así obtener el stack tecnológico más querido por las empresas en el sector. También estudiar la evolución del mercado en base a las nuevas tendencias y aprender sobre administración de sistemas levantando una IA en local(ya sea el NLP previamente mencionado o un LLM) en un dispositivo de capacidades limitadas extrayendo la mayor eficiencia posible.
