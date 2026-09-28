FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código fuente del scrapper y asegura la carpeta de scraps
COPY . .
RUN mkdir -p /app/scraps

# Define /app como raíz de módulos para que 'src.s3_uploader' resuelva directamente
ENV PYTHONPATH=/app

CMD ["python", "src/main.py"]