# 1. Usa l'immagine base ufficiale di Python 3.12 slim
FROM python:3.12-slim

# 2. Installa git e certificati SSL
RUN apt-get update && apt-get install -y \
    git \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 3. Imposta la directory di lavoro
WORKDIR /app

# 4. GitHub deposunu doğrudan çalışma dizinine klonla
RUN git clone https://github.com/Xquantum398/pulutoTV_Dizi8.git .

# 5. Aggiorna pip e installa le dipendenze (gevent dahil edildi)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gevent

# 6. Espone la porta 7860 per Gunicorn (HuggingFace Spaces)
EXPOSE 7860

# 7. Comando per avviare Gunicorn ottimizzato per HuggingFace Spaces
# Hata riskini azaltmak için CMD tek satırda düzeltildi
CMD ["gunicorn", "app:app", "-w", "2", "--worker-class", "gevent", "-b", "0.0.0.0:7860", "--timeout", "90", "--keep-alive", "5", "--log-level", "info"]
