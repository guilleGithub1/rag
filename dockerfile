FROM python:3.11-slim

# Actualiza el sistema y asegura que Git esté instalado
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    git \
    libbz2-1.0 \
    libc6 \
    libcom-err2 \
    libcrypt1 \
    libdb5.3 \
    libffi8 \
    libgdbm6 \
    libgssapi-krb5-2 \
    libk5crypto3 \
    libkeyutils1 \
    libkrb5-3 \
    libkrb5support0 \
    liblzma5 \
    libncursesw6 \
    libnsl2 \
    libpoppler-cpp-dev \
    libpq-dev \
    libreadline8 \
    libsqlite3-0 \
    libssl3 \
    libtinfo6 \
    libtirpc3 \
    libuuid1 \
    netbase \
    pkg-config \
    poppler-utils \
    tzdata \
    zlib1g \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash -E \
    && apt install -y nodejs 
    
    # Instala las dependencias de Node.js
    RUN npm install --global npm@latest
    RUN npm install --global docusaurus-init

# Crea el directorio de trabajo
WORKDIR /app

# Instala las dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .
CMD ["bash"]
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

