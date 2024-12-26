FROM python:3.11-slim

# Actualiza el sistema y asegura que Git esté instalado
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Crea el directorio de trabajo
WORKDIR /app

# Instala las dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .
CMD ["bash"]
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]