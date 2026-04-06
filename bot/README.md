# 🤖 Bot de Telegram - TryHardeo Linkedin

Este módulo contiene la implementación del Bot de Telegram (basado en `python-telegram-bot`) encargado de gestionar y supervisar las operaciones automatizadas de scraping desde el dispositivo Raspberry Pi.

## 📌 Funcionalidades
- **/join**: Invoca el proceso de consolidación mensual (`scrapping/Join.py`) en un hilo secundario (con `subprocess.run`) con gestión de recursos específica (`MALLOC_TRIM_THRESHOLD_`). Captura la salida de los logs y te los envía vía Telegram.
- **Manejo Seguro de Excepciones**: Intercepta errores críticos del script de consolidación y avisa por el chat.
- **Notificaciones de Acceso**: Tiene implementado un filtro de usuario autorizado basado en un `ID_AUTORIZADO`. El bot intercepta e informa intentos de acceso de IDs de Telegram que no cuenten con autorización.
- **Gestión Ágil de Archivos**: Dispone de un `GestorArchivos` en patrón Singleton para localizar automáticamente los últimos logs emitidos.

## ⚙️ Configuración (.env)
Asegúrate de contar con tus variables de entorno configuradas previamente:
```bash
TEL_TOKEN='tu_token_de_bot_aqui'
ID_AUTORIZADO='tu_id_numerico_de_telegram'
```

## 🏗 Arquitectura
- **`bot.py`**: El Entry Point principal. Define los Handlers de comandos de Telegram.
- **`gestorArchivos.py`**: Facilita iterar entre subdirectorios para leer e instanciar los últimos logs registrados generados por scripts externos para poder reportarlos.
