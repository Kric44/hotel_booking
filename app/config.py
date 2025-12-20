import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # Поддержка DATABASE_URL (для Render/облака) или отдельных переменных (для локальной разработки)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Локальные настройки (если DATABASE_URL не задан)
    DB_SERVER = os.environ.get('DB_SERVER') or 'localhost'
    DB_PORT = os.environ.get('DB_PORT') or '5432'
    DB_NAME = os.environ.get('DB_NAME') or 'cp'
    DB_USER = os.environ.get('DB_USER') or 'postgres'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or ''