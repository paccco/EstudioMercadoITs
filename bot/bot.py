import os
import time
import httpx
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from utils.logger import MiLogger
from bot.gestorArchivos import gestor as gestorArchivos
from dotenv import load_dotenv

# Global manifest to build help menu
MANIFEST_DATA = {}

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, logger: MiLogger) -> None:
    """Manejo de errores del bot"""
    logger.error(f"Error durante la ejecución: {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "Ha ocurrido un error al procesar tu solicitud."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra la ayuda con los comandos disponibles desde el manifiesto"""
    help_text = "Comandos disponibles (Autodescubiertos):\n"
    for cmd in MANIFEST_DATA.get("commands", []):
        help_text += f"/{cmd['command']} - {cmd['description']}\n"
    help_text += "/help - Mostrar esta ayuda\n"
    await update.message.reply_text(help_text)

def fetch_manifest(logger: MiLogger) -> dict:
    """Obtiene el manifiesto del scrapping API con reintentos."""
    api_url = os.environ.get("SCRAPPING_API_URL", "http://scrapping-service:8000")
    logger.info(f"Intentando conectar al API: {api_url}/manifest")
    
    for intento in range(10):
        try:
            r = httpx.get(f"{api_url}/manifest", timeout=5.0)
            if r.status_code == 200:
                logger.info("Manifiesto obtenido exitosamente.")
                return r.json()
        except httpx.RequestError as e:
            logger.warning(f"Intento {intento+1}/10 fallido al conectar con API: {e}")
        time.sleep(2)
        
    logger.error("No se pudo obtener el manifiesto tras 10 intentos. Operando sin comandos dinámicos.")
    return {"commands": []}

def create_api_command_handler(endpoint: str, description: str, logger: MiLogger):
    """Crea un handler para un endpoint de la API."""
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        api_url = os.environ.get("SCRAPPING_API_URL", "http://scrapping-service:8000")
        await update.message.reply_text(f"🚀 Iniciando: {description}...\nEnviando petición a la API.")
        
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(f"{api_url}{endpoint}", timeout=10.0)
                if r.status_code == 200:
                    data = r.json()
                    await update.message.reply_text(f"✅ Respuesta del servidor:\n{data.get('message', str(data))}")
                else:
                    await update.message.reply_text(f"⚠️ El servidor respondió con código {r.status_code}:\n{r.text}")
        except Exception as e:
            logger.error(f"Error comunicando con API endpoint {endpoint}: {e}")
            await update.message.reply_text(f"🛑 Error de red comunicando con API: {e}")
            
    return handler


def main() -> None:
    load_dotenv()
    # Configuración de logging
    logger = MiLogger(str(Path(__file__).parent), Path(__file__).name)

    BOT_TOKEN = os.getenv("TEL_TOKEN")
    if not BOT_TOKEN:
        logger.error("No se ha definido TEL_TOKEN")
        print("Error: Define la variable de entorno TEL_TOKEN")
        return
    
    # 1. Obtener manifiesto y guardarlo globalmente
    global MANIFEST_DATA
    MANIFEST_DATA = fetch_manifest(logger)
    
    # 2. Crear la aplicación
    logger.info("Inicializando aplicación de Telegram...")
    application = Application.builder().token(BOT_TOKEN).build()

    # 3. Registrar handlers dinámicamente
    for cmd_info in MANIFEST_DATA.get("commands", []):
        cmd_name = cmd_info["command"]
        endpoint = cmd_info["endpoint"]
        desc = cmd_info["description"]
        
        handler = create_api_command_handler(endpoint, desc, logger)
        application.add_handler(CommandHandler(cmd_name, handler))
        logger.info(f"Comando /{cmd_name} registrado -> {endpoint}")

    # Handler fijo de ayuda
    application.add_handler(CommandHandler("help", help_command))

    # Filtros de seguridad
    ADMIN_ID = int(os.getenv("ID_AUTORIZADO", "0"))
    user_filter = filters.User(user_id=ADMIN_ID)

    # Handler para mensajes de texto perdidos
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & user_filter, help_command))

    async def intruder_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.warning(f"⚠️ Intento de acceso de ID: {update.effective_user.id}")
    
    application.add_handler(MessageHandler(~user_filter, intruder_alert))
    application.add_error_handler(lambda up, ctx: error_handler(up, ctx, logger))
    
    logger.info("🤖 Bot iniciado y escuchando comandos")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
