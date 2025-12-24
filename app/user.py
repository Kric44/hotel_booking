from flask_login import UserMixin
from app import login_manager


class User(UserMixin):
    def __init__(self, id, email, password, role, full_name, phone=None, birth_date=None):
        self.id = id
        self.email = email
        self.password = password
        self.role = role
        self.full_name = full_name
        self.phone = phone
        self.birth_date = birth_date

    def is_manager(self):
        return self.role == 'manager'

    def is_client(self):
        return self.role == 'client'

@login_manager.user_loader
def load_user(user_id):
    from app.routes import connection
    try:
        with connection() as con:
            cur = con.execute(
                'SELECT id, email, password, role, full_name, phone, birth_date '
                'FROM users WHERE id = %s',
                (user_id,)
            )
            row = cur.fetchone()
            if row:
                return User(
                    id=row[0],
                    email=row[1],
                    password=row[2],
                    role=row[3],
                    full_name=row[4],
                    phone=row[5],
                    birth_date=row[6]
                )
    except Exception as e:
        print(f"Ошибка подключения: {e}")
    return None