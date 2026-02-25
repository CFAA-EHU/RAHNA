FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
 
WORKDIR /app
 
# Python + basics

RUN apt-get update && apt-get install -y --no-install-recommends \

    python3 python3-pip python3-venv \
&& rm -rf /var/lib/apt/lists/*
 
COPY requirements.txt .
 
# Instala primero PyTorch con CUDA 12.1 (muy importante)

RUN pip3 install --no-cache-dir --upgrade pip \
&& pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
 
# Luego el resto

RUN pip3 install --no-cache-dir -r requirements.txt
 
COPY app_flask.py .

COPY ./rag/ .
 
EXPOSE 8080

CMD ["gunicorn", "-w", "1", "--worker-class", "sync", "-b", "0.0.0.0:8080", "--timeout", "0", "--graceful-timeout", "0", "app_flask:app"]
