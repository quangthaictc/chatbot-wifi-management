FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y \
  chromium \
  chromium-driver \
  fonts-liberation \
  fonts-noto-color-emoji \
  libnss3 \
  libgbm1 \
  libasound2 \
  && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN cd /app && mkdir topologies

ENV PYTHONPATH=/app

CMD ["python", "main.py"]
