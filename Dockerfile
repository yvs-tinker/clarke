FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.11 python3.11-venv python3-pip \
    ffmpeg curl wget git && \
    rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3.11 /usr/bin/python

WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

# Load FHIR data and start application
RUN chmod +x scripts/start.sh
EXPOSE 7860
ENV NUMBA_CACHE_DIR=/tmp/numba_cache
ENV NUMBA_DISABLE_JIT=1
ENV HF_HOME=/tmp/hf_cache
CMD ["scripts/start.sh"]
