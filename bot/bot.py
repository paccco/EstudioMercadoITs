import os
import json
import asyncio
import subprocess
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
    help_text = "Comandos disponibles (Autodescubiertos Serverless):\n"
    for cmd in MANIFEST_DATA.get("commands", []):
        help_text += f"/{cmd['command']} - {cmd['description']}\n"
    help_text += "/help - Mostrar esta ayuda\n"
    await update.message.reply_text(help_text)

def fetch_manifest(logger: MiLogger) -> dict:
    """Obtiene el manifiesto ejecutando el script de manifest en un contenedor efímero."""
    logger.info("Intentando obtener el manifiesto usando Podman/Docker en modo DooD...")
    try:
        cmd = [
            "docker", "run", "--rm",
            "linkedin-scrapping",
            "python", "-m", "scrapping.manifest"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            logger.info("Manifiesto obtenido exitosamente desde contenedor efímero.")
            return json.loads(result.stdout)
        else:
            logger.error(f"Error cargando manifest. Salida: {result.stderr}")
    except Exception as e:
        logger.error(f"Error crítico en fetch_manifest: {e}")
        
    return {"commands": []}

def create_ephemeral_handler(script: str, description: str, logger: MiLogger):
    """Crea un handler que lanza un contenedor efímero con Socket de Podman."""
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"🚀 Iniciando: {description}...\nLevantando entorno de memoria controlada y desechable.")
        
        try:
            # Mapeamos explícitamente los volúmenes del compose en formato DooD
            cmd = [
                "docker", "run", "--rm",
                "-v", "linkedintryhardeo_data_volume:/app/scrapping/scraps",
                "-v", "linkedintryhardeo_data_mensual_volume:/app/scrapping/data_mensual",
                "-v", "linkedintryhardeo_logs_volume:/app/logs",
                "-e", "LOGS_DIR=/app/logs",
                "linkedin-scrapping",
                "python", "-m", script
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                await update.message.reply_text(f"✅ Tarea completada exitosamente. Contenedor aniquilado.\nSalida:\n{stdout.decode()[-500:]}")
            else:
                await update.message.reply_text(f"⚠️ El contenedor colapsó o reportó error (Código {process.returncode}):\n{stderr.decode()[-500:]}")
        except Exception as e:
            logger.error(f"Error de sistema gestionando contenedor efímero para {script}: {e}")
            await update.message.reply_text(f"🛑 Error crítico levantando contenedor de la API: {e}")
            
    return handler


def main() -> None:
    load_dotenv()
    logger = MiLogger(str(Path(__file__).parent), Path(__file__).name)

    BOT_TOKEN = os.getenv("TEL_TOKEN")
    if not BOT_TOKEN:
        logger.error("No se ha definido TEL_TOKEN")
        print("Error: Define la variable de entorno TEL_TOKEN")
        return
    
    # Obtener manifiesto invocando el motor del HOST
    global MANIFEST_DATA
    MANIFEST_DATA = fetch_manifest(logger)
    
    logger.info("Inicializando aplicación de Telegram...")
    application = Application.builder().token(BOT_TOKEN).build()

    for cmd_info in MANIFEST_DATA.get("commands", []):
        cmd_name = cmd_info["command"]
        script_path = cmd_info["script"]
        desc = cmd_info["description"]
        
        handler = create_ephemeral_handler(script_path, desc, logger)
        application.add_handler(CommandHandler(cmd_name, handler))
        logger.info(f"Comando Serverless /{cmd_name} registrado -> {script_path}")

    application.add_handler(CommandHandler("help", help_command))

    ADMIN_ID = int(os.getenv("ID_AUTORIZADO", "0"))
    user_filter = filters.User(user_id=ADMIN_ID)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & user_filter, help_command))

    async def intruder_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.warning(f"⚠️ Intento de acceso foráneo de ID: {update.effective_user.id}")
    
    application.add_handler(MessageHandler(~user_filter, intruder_alert))
    application.add_error_handler(lambda up, ctx: error_handler(up, ctx, logger))
    
    logger.info("🤖 Bot Node iniciado. Motor Podman/Docker adjuntado.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
