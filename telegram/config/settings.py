import os

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN", "TELEGRAM_API_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "GEMINI_API_KEY")
RYU_URL = os.getenv("RYU_API_URL", "http://localhost:8080")
ALLOWED_USERS = os.getenv("ALLOWED_USERS", "")
