FROM python:3.11-slim

# Evita que Python escriba archivos .pyc y fuerza el stdout sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Añade la raíz del proyecto y la carpeta apps al PATH de Python
ENV PYTHONPATH="/app:/app/apps"

WORKDIR /app

# Instalar dependencias
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
ENV DJANGO_SETTINGS_MODULE=tecvote.settings.dev

# Copiar todo el código (incluyendo .env si no está ignorado)
COPY . /app/

CMD ["gunicorn", "tecvote.wsgi:application", "--bind", "0.0.0.0:8000"]