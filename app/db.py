import psycopg
from app import app

def get_connection():
    # Если есть DATABASE_URL (облако), используем его
    database_url = app.config.get('DATABASE_URL')
    
    if database_url:
        # Добавляем client_encoding для правильной работы с русским языком
        return psycopg.connect(database_url, client_encoding='UTF8')
    
    # Иначе используем отдельные переменные (локальная разработка)
    return psycopg.connect(
        host=app.config['DB_SERVER'],
        port=app.config['DB_PORT'],
        dbname=app.config['DB_NAME'],
        user=app.config['DB_USER'],
        password=app.config['DB_PASSWORD'],
        client_encoding='UTF8'
    )