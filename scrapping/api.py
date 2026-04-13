from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import os
import sys

app = FastAPI(title="Scrapping API", version="1.0.0")

# Manifiesto de comandos para el bot
MANIFEST = {
    "commands": [
        {
            "command": "join",
            "description": "Unir todos los csv de este mes manualmente",
            "endpoint": "/api/join",
            "method": "POST"
        },
        {
            "command": "scrape",
            "description": "Ejecutar la extracción de ofertas de empleo",
            "endpoint": "/api/scrape",
            "method": "POST"
        }
    ]
}

async def run_script_in_background(script_module: str, args: list = []):
    """Ejecuta un script en segundo plano para no bloquear el API."""
    python_bin = sys.executable
    cmd = [python_bin, "-m", script_module] + args
    
    # Añadimos variables especiales para el recolector de basura (como estaba en bot.py)
    env_custom = os.environ.copy()
    env_custom["MALLOC_TRIM_THRESHOLD_"] = "65536"
    env_custom["PYTHONMALLOC"] = "malloc"

    process = await asyncio.create_subprocess_exec(
        *cmd,
        env=env_custom,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    # Lógica de logging o espera podría añadirse aquí si fuera necesario
    # await process.communicate()
    # Por ahora simplemente lo dejamos corriendo (fire and forget)
    
@app.get("/manifest")
async def get_manifest():
    """Devuelve el manifiesto de comandos disponibles."""
    return JSONResponse(content=MANIFEST)

@app.post("/api/join")
async def run_join(background_tasks: BackgroundTasks):
    """Endpoint para ejecutar el join manualmente."""
    try:
        background_tasks.add_task(run_script_in_background, "scrapping.Join")
        return {"status": "success", "message": "Join iniciado en segundo plano. Revisa los logs en la carpeta de sistema."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scrape")
async def run_scrape(background_tasks: BackgroundTasks):
    """Endpoint para ejecutar el scraping manualmente."""
    try:
        background_tasks.add_task(run_script_in_background, "scrapping.Scrapping")
        return {"status": "success", "message": "Scraping iniciado en segundo plano. Revisa los logs."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
