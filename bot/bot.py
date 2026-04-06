import os
import subprocess
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from utils.logger import MiLogger
from bot.gestorArchivos import gestor as gestorArchivos
from dotenv import load_dotenv

# Funciones del bot (definidas antes de main para usarlas como callbacks)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, logger: MiLogger) -> None:
    """Manejo de errores del bot"""
    logger.error(f"Error durante la ejecución: {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "Ha ocurrido un error al procesar tu solicitud."
        )

async def ejecutarJoin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ejecuta el comando join.py usando subprocess de forma segura"""    
    script = "scrapping.Join"
    python_bin = ".venv/bin/python3"
    
    await update.message.reply_text(f"Ejecutando {script} con subprocess...")
    
    env_custom = os.environ.copy()
    env_custom["MALLOC_TRIM_THRESHOLD_"] = "65536"
    env_custom["PYTHONMALLOC"] = "malloc"
    
    try:
        # Usamos subprocess.run que es más pythonico y bloqueante seguro
        resultado = subprocess.run(
            [python_bin, "-m", script],
            env=env_custom,
            capture_output=True,
            text=True
        )
        
        if resultado.returncode == 0:
            carpeta_logs = "scrapping/logs"
            ultimo_archivo = gestorArchivos.obtenerUltimoArchivo(carpeta_logs, "log")
            
            if ultimo_archivo:
                mensaje = gestorArchivos.leerArchivo(ultimo_archivo, n_tail=6)
                await update.message.reply_text(f"📜 Logs:\n{mensaje}")
            else:
                await update.message.reply_text("Hecho, pero no se encontraron logs.")
        else:
            await update.message.reply_text(f"⚠️ Error. Código de salida: {resultado.returncode}\nDetalles:\n{resultado.stderr[-500:]}")
            
    except Exception as e:
        await update.message.reply_text(f"🛑 Error crítico levantando proceso: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra la ayuda con los comandos disponibles"""
    help_text = (
        "Comandos disponibles:\n"
        "/join - Unir todos los csv de este mes\n"
        "/help - Mostrar esta ayuda\n"
    )
    await update.message.reply_text(help_text)


def main() -> None:
    load_dotenv()
    # Configuración de logging
    logger = MiLogger(str(Path(__file__).parent), Path(__file__).name)

    # Token del bot (se cargará desde variable de entorno o archivo .env)
    BOT_TOKEN = os.getenv("TEL_TOKEN")
    
    if not BOT_TOKEN:
        logger.error("No se ha definido TELEGRAM_BOT_TOKEN")
        print("Error: Define la variable de entorno TELEGRAM_BOT_TOKEN")
        print("Ejemplo: export TELEGRAM_BOT_TOKEN='tu_token_aqui'")
        return
    
    # Crear la aplicación
    logger.info("Inicializando aplicación...")
    application = Application.builder().token(BOT_TOKEN).build()

    # Registrar handlers de comandos
    application.add_handler(CommandHandler("join", ejecutarJoin))
    application.add_handler(CommandHandler("help", help_command))

    ADMIN_ID = int(os.getenv("ID_AUTORIZADO", "0"))
    user_filter = filters.User(user_id=ADMIN_ID)

    # Handler para mensajes de texto del usuario autorizado
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & user_filter, help_command))

    async def intruder_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.warning(f"⚠️ Intento de acceso de ID: {update.effective_user.id}")
    
    application.add_handler(MessageHandler(~user_filter, intruder_alert))

    # Manejo de errores (usamos lambda para pasar el logger)
    application.add_error_handler(lambda up, ctx: error_handler(up, ctx, logger))
    
    # Iniciar el bot
    print("🤖 Bot iniciado")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
