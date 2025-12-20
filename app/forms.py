from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, DateField, IntegerField, TextAreaField, DecimalField
from wtforms.validators import InputRequired, Email, Length, EqualTo, Optional, NumberRange

# ==================== ФОРМЫ АВТОРИЗАЦИИ ====================

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(message='Введите email'), Email(message='Некорректный email')])
    password = PasswordField('Пароль', validators=[InputRequired(message='Введите пароль')])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    full_name = StringField('ФИО', validators=[
        InputRequired(message='Введите ФИО'), 
        Length(min=2, max=150, message='ФИО должно быть от 2 до 150 символов')
    ])
    email = StringField('Email', validators=[
        InputRequired(message='Введите email'), 
        Email(message='Некорректный email'), 
        Length(max=100)
    ])
    phone = StringField('Телефон', validators=[Optional(), Length(max=20)])
    birth_date = DateField('Дата рождения', validators=[Optional()])
    password = PasswordField('Пароль', validators=[
        InputRequired(message='Введите пароль'),
        Length(min=6, message='Пароль должен быть не менее 6 символов')
    ])
    confirm_password = PasswordField('Подтверждение пароля', validators=[
        InputRequired(message='Подтвердите пароль'),
        EqualTo('password', message='Пароли должны совпадать')
    ])
    submit = SubmitField('Зарегистрироваться')

class ProfileForm(FlaskForm):
    full_name = StringField('ФИО', validators=[
        InputRequired(message='Введите ФИО'), 
        Length(min=2, max=150)
    ])
    phone = StringField('Телефон', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Сохранить изменения')

class ChangeEmailForm(FlaskForm):
    new_email = StringField('Новый Email', validators=[
        InputRequired(message='Введите новый email'),
        Email(message='Некорректный email'),
        Length(max=100)
    ])
    password = PasswordField('Текущий пароль', validators=[
        InputRequired(message='Введите пароль для подтверждения')
    ])
    submit = SubmitField('Изменить email')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Текущий пароль', validators=[InputRequired(message='Введите текущий пароль')])
    new_password = PasswordField('Новый пароль', validators=[
        InputRequired(message='Введите новый пароль'),
        Length(min=6, message='Пароль должен быть не менее 6 символов')
    ])
    confirm_password = PasswordField('Подтверждение пароля', validators=[
        InputRequired(message='Подтвердите пароль'),
        EqualTo('new_password', message='Пароли должны совпадать')
    ])
    submit = SubmitField('Изменить пароль')

# ==================== ФОРМЫ БРОНИРОВАНИЯ ====================

class BookingForm(FlaskForm):
    check_in_date = DateField('Дата заезда', validators=[InputRequired(message='Выберите дату заезда')])
    check_out_date = DateField('Дата выезда', validators=[InputRequired(message='Выберите дату выезда')])
    guests_count = IntegerField('Количество гостей', validators=[
        InputRequired(message='Укажите количество гостей'), 
        NumberRange(min=1, max=10, message='От 1 до 10 гостей')
    ])
    payment_method = SelectField('Способ оплаты', choices=[
        ('card', 'Банковская карта'), 
        ('cash', 'Наличные при заселении')
    ])
    submit = SubmitField('Продолжить')

class TravelerForm(FlaskForm):
    full_name = StringField('ФИО', validators=[InputRequired(), Length(min=2, max=150)])
    birth_date = DateField('Дата рождения', validators=[InputRequired()])
    passport_number = StringField('Номер паспорта', validators=[InputRequired(), Length(min=5, max=20)])

# ==================== ФОРМЫ МЕНЕДЖЕРА ====================

class HotelForm(FlaskForm):
    name = StringField('Название гостиницы', validators=[
        InputRequired(message='Введите название'), 
        Length(max=150)
    ])
    stars = SelectField('Количество звёзд', choices=[
        (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')
    ], coerce=int)
    description = TextAreaField('Описание', validators=[Optional()])
    city_id = SelectField('Город', coerce=int, validators=[InputRequired(message='Выберите город')])
    submit = SubmitField('Сохранить')

class RoomTypeForm(FlaskForm):
    name = StringField('Название номера', validators=[
        InputRequired(message='Введите название'), 
        Length(max=50)
    ])
    capacity = IntegerField('Вместимость (чел.)', validators=[
        InputRequired(message='Укажите вместимость'), 
        NumberRange(min=1, max=10)
    ])
    area = DecimalField('Площадь (м²)', validators=[Optional()])
    price_per_night = DecimalField('Цена за ночь (руб.)', validators=[
        InputRequired(message='Укажите цену'), 
        NumberRange(min=0)
    ])
    description = TextAreaField('Описание', validators=[Optional()])
    submit = SubmitField('Сохранить')