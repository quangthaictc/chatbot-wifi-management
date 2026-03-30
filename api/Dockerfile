# Sử dụng image Python bản nhẹ (slim) để giảm dung lượng
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app .

CMD ["fastapi", "run", "main.py", "--port", "8000"]
