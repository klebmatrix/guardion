# Usa a imagem oficial do Python estável e leve
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Instala dependências do sistema necessárias para bibliotecas de imagem e crypto
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia o arquivo de requisitos primeiro (otimiza o cache)
COPY requirements.txt .

# Instala as bibliotecas do Agente
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto para o container
COPY . .

# Expõe a porta que o Render usa
EXPOSE 10000

# Comando para iniciar o Agente com Gunicorn (Produção)
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]