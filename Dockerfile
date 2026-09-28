FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente del proyecto
COPY . .

# Crear explícitamente la carpeta de logs y scraps para evitar fallos de I/O
RUN mkdir -p /app/scraps /app/logs

# Ajustar PYTHONPATH para que resuelva utils y subidaS3 sin colisiones
ENV PYTHONPATH=/app

# Comando apuntando al archivo respetando mayúsculas y ruta relativa exacta
CMD ["python", "scrapping/Scrapping.py"]