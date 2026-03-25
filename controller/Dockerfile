FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip==20.3.4 \
    && pip install --no-cache-dir "setuptools<58.0.0"

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 6633 6653

CMD ["/bin/bash"]