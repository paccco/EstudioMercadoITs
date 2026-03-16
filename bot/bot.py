import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from bot.logger import MiLogger
from bot.gestorArchivos import gestor as gestorArchivos
from dotenv import load_dotenv

# Funciones del bot (definidas antes de main para usarlas como callbacks)

WDIR = os.getcwd()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, logger: MiLogger):
    """Manejo de errores del bot"""
    logger.error(f"Error durante la ejecución: {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "Ha ocurrido un error al procesar tu solicitud."
        )

async def ejecutarJoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta el comando join.py"""    
    script=os.path.join(WDIR, "scrapping", "Join.py")
    bin=os.path.join(WDIR, ".venv/bin/python3")
    await update.message.reply_text(f"Ejecutando {script}...")
    debug = f"MALLOC_TRIM_THRESHOLD_=65536 PYTHONMALLOC=malloc {bin} -O {script}"
    resultado = os.system(debug)
    if resultado == 0:
        carpeta_logs = os.path.dirname(script) + "/logs/"
        mensaje = gestorArchivos.leerArchivo(gestorArchivos.obtenerUltimoArchivo(carpeta_logs, "log"), n_tail=6)
        await update.message.reply_text(mensaje)
    else:
        await update.message.reply_text(f"Error al ejecutar {script}. Código de salida: {resultado}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra la ayuda con los comandos disponibles"""
    help_text = (
        "Comandos disponibles:\n"
        "/join - Unir todos los csv de este mes\n"
        "/help - Mostrar esta ayuda\n"
    )
    await update.message.reply_text(help_text)


def main():
    load_dotenv()
    # Configuración de logging
    logger = MiLogger(os.path.dirname(__file__), os.path.basename(__file__))

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

    ADMIN_ID = int(os.getenv("ID_AUTORIZADO"))
    user_filter = filters.User(user_id=ADMIN_ID)

    # Handler para mensajes de texto del usuario autorizado
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & user_filter, help_command))

    async def intruder_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.warning(f"⚠️ Intento de acceso de ID: {update.effective_user.id}")
    
    application.add_handler(MessageHandler(~user_filter, intruder_alert))

    # Manejo de errores (usamos lambda para pasar el logger)
    application.add_error_handler(lambda update, context: error_handler(update, context, logger))
    
    # Iniciar el bot
    print("🤖 Bot iniciado")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
