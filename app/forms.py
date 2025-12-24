from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, IntegerField, TextAreaField, DecimalField
from wtforms.validators import InputRequired, Email, Length, EqualTo, Optional, NumberRange

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(message='Введите email'), Email(message='Некорректный email')])
    password = PasswordField('Пароль', validators=[InputRequired(message='Введите пароль')])
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    full_name = StringField('ФИО', validators=[InputRequired(message='Введите ФИО'), Length(min=2, max=150)])
    email = StringField('Email', validators=[InputRequired(message='Введите email'), Email(message='Некорректный email'), Length(max=100)])
    phone = StringField('Телефон', validators=[Optional(), Length(max=20)])
    birth_date = DateField('Дата рождения', validators=[Optional()])
    password = PasswordField('Пароль', validators=[InputRequired(message='Введите пароль'), Length(min=10, max=100)])
    confirm = PasswordField('Повторите пароль', validators=[InputRequired(), EqualTo('password', message='Пароли должны совпадать')])
    submit = SubmitField('Зарегистрироваться')
    
class ProfileForm(FlaskForm):
    full_name = StringField('ФИО', validators=[InputRequired(message='Введите ФИО'), Length(min=2, max=150)])
    phone = StringField('Телефон', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Сохранить изменения')

class ChangeEmailForm(FlaskForm):
    new_email = StringField('Новый Email', validators=[InputRequired(), Email(message='Некорректный email'), Length(max=100)])
    password = PasswordField('Текущий пароль', validators=[
        InputRequired(message='Введите пароль для подтверждения')
    ])
    submit = SubmitField('Изменить email')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Текущий пароль', validators=[InputRequired()])
    new_password = PasswordField('Новый пароль', validators=[InputRequired(), Length(min=10, max=100)])
    confirm = PasswordField('Повторите пароль', validators=[InputRequired(), EqualTo('new_password', message='Пароли должны совпадать')])
    submit = SubmitField('Изменить пароль')

class BookingForm(FlaskForm):
    check_in_date = DateField('Дата заезда', validators=[InputRequired()])
    check_out_date = DateField('Дата выезда', validators=[InputRequired()])
    guests_count = IntegerField('Количество гостей', validators=[InputRequired(), NumberRange(min=1)])
    payment_method = SelectField('Способ оплаты', choices=[
        ('card', 'Банковская карта'), 
        ('cash', 'Наличные при заселении')
    ])
    submit = SubmitField('Продолжить')


class HotelForm(FlaskForm):
    name = StringField('Название гостиницы', validators=[InputRequired(), Length(max=150)])
    stars = SelectField('Количество звёзд', choices=[
        (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')
    ], coerce=int)
    description = TextAreaField('Описание', validators=[Optional()])
    city_id = SelectField('Город', coerce=int, validators=[InputRequired()])
    submit = SubmitField('Сохранить')

class RoomTypeForm(FlaskForm):
    name = StringField('Название номера', validators=[InputRequired(), Length(max=50)])
    capacity = IntegerField('Вместимость (чел.)', validators=[InputRequired(), NumberRange(min=1)])
    area = DecimalField('Площадь (м²)', validators=[Optional()])
    price_per_night = DecimalField('Цена за ночь (руб.)', validators=[InputRequired(),NumberRange(min=0)])
    description = TextAreaField('Описание', validators=[Optional()])
    submit = SubmitField('Сохранить')