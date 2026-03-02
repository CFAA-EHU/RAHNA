FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
 
WORKDIR /app
 
# Python + basics

RUN apt-get update && apt-get install -y --no-install-recommends \

    python3 python3-pip python3-venv \
&& rm -rf /var/lib/apt/lists/*
 
COPY requirements.txt .

RUN pip3 install --no-cache-dir --upgrade pip \
&& pip3 install --no-cache-dir torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu118

RUN pip3 install --no-cache-dir -r requirements.txt
 
COPY app_flask.py .

COPY ./rag/ .
 
EXPOSE 8080

CMD ["gunicorn", "-w", "1", "--worker-class", "sync", "-b", "0.0.0.0:8080", "--timeout", "0", "--graceful-timeout", "0", "app_flask:app"]
