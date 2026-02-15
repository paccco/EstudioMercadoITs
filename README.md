# 🚀 Job Market Insight: Málaga & Granada (IT Edition)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
![LinkedIn](https://img.shields.io/badge/linkedin-%230077B5.svg?style=for-the-badge&logo=linkedin&logoColor=white)
![Charts](https://img.shields.io/badge/Matplotlib-%23ffffff.svg?style=for-the-badge&logo=Matplotlib&logoColor=black)

Este proyecto automatiza la extracción, limpieza y análisis de ofertas de empleo en el sector tecnológico para **Málaga** y **Granada**, analizando tanto el mercado local como el nacional en remoto.

El objetivo principal es identificar el **stack tecnológico real** que las empresas demandan para perfiles **Junior (Entry Level)** en 2026.

## 🛠️ Tecnologías y Librerías
* **Scraping:** `python-jobspy` (LinkedIn)
* **Análisis de Datos:** `Pandas`, `NumPy`, `Scikit-Learn`
* **Procesamiento de Texto:** `Regex` & `NLTK` (Stopwords)
* **Visualización:** `Matplotlib` & `Seaborn`

## 📊 Insights del Mercado (Febrero 2026)

### 🔝 Top 5 Tecnologías Globales
| Tecnología | Menciones | Rol en el Mercado |
| :--- | :--- | :--- |
| **Python** | 120 | Lenguaje estándar universal |
| **SQL** | 83 | Fundamental para Data & Backend |
| **Kubernetes** | 66 | Requisito clave para perfiles Cloud |
| **CI/CD** | 62 | Automatización obligatoria |
| **Docker** | 58 | Estándar de despliegue |

### 👶 Perfil Junior / Entry Level
* **Málaga:** Fuerte enfoque en **React**, **TypeScript** y herramientas de infraestructura como **Docker**.
* **Granada:** Mercado muy volcado al Backend y sistemas con una demanda inusual de **Go** y **Rust**.
* **Requisito Sorpresa:** Kubernetes aparece en más del 35% de las ofertas Junior, dejando de ser una habilidad exclusiva de Seniors.

## 📁 Estructura del Proyecto
```text
├── scraps/                 # CSVs crudos organizados por carpetas de fecha
├── plots/                  # Gráficas PNG generadas (Málaga vs Granada)(Por añadir)
├── Join.ipynb              # Unir los CSVs
├── Scrapping.ipynb         # Peticiones a linkedin
├── Tratamiento.ipynb       # Limpieza, deduplicación y extracción de skills
└── README.md               # Documentación del proyecto
