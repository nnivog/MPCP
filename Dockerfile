FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cache optimization)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# HF Spaces runs as non-root; ensure /data is writable if mounted
RUN mkdir -p /data

EXPOSE 7860

CMD ["python", "app.py"]
