from werkzeug.security import generate_password_hash
import psycopg
from app.config import Config

# Данные менеджера
EMAIL = "manager@hotel.com"
PASSWORD = "manager123"
FULL_NAME = "Hotel Manager"

# Создаём хеш пароля
password_hash = generate_password_hash(PASSWORD)

# Подключаемся к БД и создаём менеджера
try:
    with psycopg.connect(
            host=Config.DB_SERVER,
            port=Config.DB_PORT,
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
    ) as con:
        # Проверяем, есть ли уже такой email
        existing = con.execute(
            'SELECT id FROM users WHERE email = %s', (EMAIL,)
        ).fetchone()

        if existing:
            # Обновляем роль на менеджера
            con.execute(
                'UPDATE users SET role = %s, password = %s WHERE email = %s',
                ('manager', password_hash, EMAIL)
            )
            print(f"User {EMAIL} updated to manager role")
        else:
            # Создаём нового менеджера
            con.execute(
                'INSERT INTO users (email, password, full_name, role) VALUES (%s, %s, %s, %s)',
                (EMAIL, password_hash, FULL_NAME, 'manager')
            )
            print(f"Manager created: {EMAIL}")

        print(f"Password: {PASSWORD}")

except Exception as e:
    print(f"Error: {e}")