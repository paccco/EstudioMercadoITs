# 📊 TryHardeo Linkedin (Job Market Insight: IT Edition)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Raspberry Pi](https://img.shields.io/badge/-Raspberry_Pi-C51A4A?style=for-the-badge&logo=Raspberry-Pi&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)

Este repositorio corresponde a un proyecto modular que automatiza la extracción de ofertas de empleo tecnológico en España (con foco inicial en Málaga, Granada, Sevilla, Madrid, Barcelona y perfiles remotos), identificando tendencias mundiales en perfiles del sector IT, especialmente para nivel Junior. El ecosistema tecnológico se rige bajo una plataforma **Raspberry Pi Zero 2 W** asegurando una automatización de bajo consumo en hardware limitado.

## 📁 Estructura del Repositorio

El proyecto se divide de forma independiente en sus componentes (cada uno se desarrolla de manera asíncrona sobre su propia rama del repositorio `dev-*`):

### 1. `scrapping/` (Data Extraction & Processing)
Contiene la lógica *core* de minería de datos, empleando extracción diaria (cronjob al cierre de la madrugada) y consolidación mensual de registros, todo diseñado siguiendo principios *SOLID* y limpieza reactiva del Garbage Collector de Python.
> [📚 Visita la Documentación del Scraper](scrapping/README.md)

### 2. `bot/` (Telegram Management System)
Un bot de Telegram desarrollado asíncronamente implementado en base a `python-telegram-bot`. Encargado de levantar procesos nativos a demanda, permitir fusiones tempranas de datos desde el móvil (comando `/join`) y verificar de manera remota los registros y *logs* guardados.
> [📚 Visita la Documentación del Bot](bot/README.md)

### 3. `utils/` (Core Tools)
Incluye recursos y componentes transversales y estáticos consumibles por los otros módulos (como el sistema centralizado de *Logs* unificado empleando tipado estricto y la librería *Pathlib* globalmente).

## 💡 Objetivos Globales
- Visualizar de manera real, medible y unificada **el panorama y demandas tecnológicas** hacia los desarrolladores informáticos en el país.
- Lograr una ejecución altamente paralela de scraping usando un hardware limitado optimizando cada Byte de memoria.
- Explorar, y aplicar como fase de ampliación futura (actualmente en la pizarra de diseño), **Sistemas basados en LLM en el Edge** para procesar mediante NLP cada oferta con hardware ultraligero y descubrir con Inteligencia Artificial cuáles son esos lenguajes encubiertos requeridos en el cuerpo textual de las descripciones de las ofertas.
## 🛠 Historial de Refactorización
- `refactor(docker)`: Se crea ecosistema de microservicios. Se añaden `docker-compose.yml`, `Dockerfile.bot` y `Dockerfile.scrapping`.
