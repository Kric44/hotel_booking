from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlsplit
from datetime import date, datetime
from app import app
import psycopg
from app.user import User
from app.forms import (
    LoginForm,
    RegistrationForm,
    ProfileForm,
    ChangePasswordForm,
    ChangeEmailForm,
    BookingForm,
    HotelForm,
    RoomTypeForm
)


def connection():
    if app.config.get('DATABASE_URL'):
        return psycopg.connect(app.config['DATABASE_URL'])
    return psycopg.connect(
        host=app.config['DB_SERVER'],
        port=app.config['DB_PORT'],
        dbname=app.config['DB_NAME'],
        user=app.config['DB_USER'],
        password=app.config['DB_PASSWORD'],
    )


@app.route('/')
def index():
    return render_template('index.html', title='Главная')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            with connection() as con:
                cur = con.execute(
                    'SELECT id, email, password, role, full_name, phone, birth_date '
                    'FROM users WHERE email = %s',
                    (form.email.data,)
                )
                row = cur.fetchone()

            if row is None or not check_password_hash(row[2], form.password.data):
                flash('Неверный email или пароль', 'danger')
                return redirect(url_for('login'))

            user = User(
                id=row[0], email=row[1], password=row[2], role=row[3],
                full_name=row[4], phone=row[5], birth_date=row[6]
            )
            login_user(user)
            flash(f'Добро пожаловать, {user.full_name}!', 'success')

            next_page = request.args.get('next')
            if not next_page or urlsplit(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)

        except Exception as e:
            flash(f'Ошибка входа: {e}', 'danger')

    return render_template('auth/login.html', title='Вход', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            with connection() as con:
                cur = con.execute('SELECT id FROM users WHERE email = %s', (form.email.data,))
                if cur.fetchone():
                    flash('Этот email уже зарегистрирован', 'danger')
                    return redirect(url_for('register'))

                password_hash = generate_password_hash(form.password.data)
                con.execute(
                    'INSERT INTO users (full_name, password, email, role, phone, birth_date) '
                    'VALUES (%s, %s, %s, %s, %s, %s)',
                    (form.full_name.data, password_hash, form.email.data, 'client',
                     form.phone.data or None, form.birth_date.data or None)
                )

            flash('Регистрация успешна! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash(f'Ошибка регистрации: {e}', 'danger')

    return render_template('auth/register.html', title='Регистрация', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()

    if form.validate_on_submit():
        try:
            with connection() as con:
                con.execute(
                    'UPDATE users SET full_name = %s, phone = %s WHERE id = %s',
                    (form.full_name.data, form.phone.data or None, current_user.id)
                )
            flash('Профиль обновлён!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            flash(f'Ошибка обновления профиля: {e}', 'danger')

    elif request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.phone.data = current_user.phone

    return render_template('auth/profile.html', title='Профиль', form=form)


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not check_password_hash(current_user.password, form.current_password.data):
            flash('Неверный текущий пароль', 'danger')
            return redirect(url_for('change_password'))

        try:
            with connection() as con:
                new_hash = generate_password_hash(form.new_password.data)
                con.execute('UPDATE users SET password = %s WHERE id = %s',
                            (new_hash, current_user.id))
            flash('Пароль изменён!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            flash(f'Ошибка изменения пароля: {e}', 'danger')

    return render_template('auth/change_password.html', title='Изменение пароля', form=form)


@app.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    form = ChangeEmailForm()

    if form.validate_on_submit():
        if not check_password_hash(current_user.password, form.password.data):
            flash('Неверный пароль', 'danger')
            return redirect(url_for('change_email'))

        try:
            with connection() as con:
                existing = con.execute(
                    'SELECT id FROM users WHERE email = %s AND id != %s',
                    (form.new_email.data, current_user.id)
                ).fetchone()

                if existing:
                    flash('Этот email уже используется другим пользователем', 'danger')
                    return redirect(url_for('change_email'))

                con.execute(
                    'UPDATE users SET email = %s WHERE id = %s',
                    (form.new_email.data, current_user.id)
                )
            flash('Email изменён! Используйте новый email для входа.', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            flash(f'Ошибка изменения email: {e}', 'danger')

    return render_template('auth/change_email.html', title='Изменение email', form=form)


@app.route('/bookings/<int:booking_id>/pay', methods=['POST'])
@login_required
def pay_booking(booking_id):
    try:
        with connection() as con:
            booking = con.execute('''
                SELECT id, status, payment_method FROM booking
                WHERE id = %s AND user_id = %s
            ''', (booking_id, current_user.id)).fetchone()

            if not booking:
                flash('Бронирование не найдено', 'danger')
                return redirect(url_for('my_bookings'))

            if booking[1] != 'new':
                flash('Это бронирование уже обработано', 'warning')
                return redirect(url_for('my_bookings'))

            if booking[2] != 'card':
                flash('Оплата картой не требуется для этого бронирования', 'warning')
                return redirect(url_for('my_bookings'))

            con.execute(
                "UPDATE booking SET status = 'confirmed' WHERE id = %s",
                (booking_id,)
            )

        flash('Оплата прошла успешно! Бронирование подтверждено.', 'success')
        return redirect(url_for('booking_details', booking_id=booking_id))
    except Exception as e:
        flash(f'Ошибка оплаты: {e}', 'danger')
        return redirect(url_for('my_bookings'))


@app.route('/hotels')
def hotels():
    country_id = request.args.get('country', type=int)
    city_id = request.args.get('city', type=int)
    stars = request.args.get('stars', type=int)

    try:
        with connection() as con:
            countries = con.execute('SELECT id, name FROM country ORDER BY name').fetchall()

            if country_id:
                cities = con.execute(
                    'SELECT id, name FROM city WHERE country_id = %s ORDER BY name',
                    (country_id,)
                ).fetchall()
            else:
                cities = con.execute('SELECT id, name FROM city ORDER BY name').fetchall()

            query = '''
                SELECT h.id, h.name, h.stars, h.description, c.name, co.name
                FROM hotel h
                JOIN city c ON h.city_id = c.id
                JOIN country co ON c.country_id = co.id
                WHERE 1=1
            '''
            params = []

            if country_id:
                query += ' AND co.id = %s'
                params.append(country_id)
            if city_id:
                query += ' AND c.id = %s'
                params.append(city_id)
            if stars:
                query += ' AND h.stars = %s'
                params.append(stars)

            query += ' ORDER BY h.stars DESC, h.name'

            hotels_list = con.execute(query, params).fetchall()

        return render_template('hotels/list.html', title='Гостиницы',
                               hotels=hotels_list, countries=countries, cities=cities,
                               selected_country=country_id, selected_city=city_id,
                               selected_stars=stars)
    except Exception as e:
        flash(f'Ошибка загрузки гостиниц: {e}', 'danger')
        return redirect(url_for('index'))


@app.route('/hotels/<int:hotel_id>')
def hotel_details(hotel_id):
    try:
        with connection() as con:
            hotel = con.execute('''
                SELECT h.id, h.name, h.stars, h.description, c.name, co.name
                FROM hotel h
                JOIN city c ON h.city_id = c.id
                JOIN country co ON c.country_id = co.id
                WHERE h.id = %s
            ''', (hotel_id,)).fetchone()

            if not hotel:
                flash('Гостиница не найдена', 'danger')
                return redirect(url_for('hotels'))

            amenities = con.execute('''
                SELECT ha.name FROM hotel_amenity ha
                JOIN hotel_amenity_link hal ON ha.id = hal.amenity_id
                WHERE hal.hotel_id = %s
                ORDER BY ha.name
            ''', (hotel_id,)).fetchall()

            room_types = con.execute('''
                SELECT id, name, capacity, area, price_per_night, description
                FROM room_type WHERE hotel_id = %s
                ORDER BY price_per_night
            ''', (hotel_id,)).fetchall()

            room_amenities = {}
            for room in room_types:
                room_amenities[room[0]] = con.execute('''
                    SELECT ra.name FROM room_amenity ra
                    JOIN room_type_amenity rta ON ra.id = rta.amenity_id
                    WHERE rta.room_type_id = %s
                    ORDER BY ra.name
                ''', (room[0],)).fetchall()

        return render_template('hotels/details.html', title=hotel[1],
                               hotel=hotel, amenities=amenities,
                               room_types=room_types, room_amenities=room_amenities)
    except Exception as e:
        flash(f'Ошибка загрузки гостиницы: {e}', 'danger')
        return redirect(url_for('hotels'))


@app.route('/book/<int:room_type_id>', methods=['GET', 'POST'])
@login_required
def book_room(room_type_id):
    try:
        with connection() as con:
            room = con.execute('''
                SELECT rt.id, rt.name, rt.capacity, rt.price_per_night, h.name, h.id
                FROM room_type rt
                JOIN hotel h ON rt.hotel_id = h.id
                WHERE rt.id = %s
            ''', (room_type_id,)).fetchone()

            if not room:
                flash('Тип номера не найден', 'danger')
                return redirect(url_for('hotels'))

        form = BookingForm()

        if form.validate_on_submit():
            check_in = form.check_in_date.data
            check_out = form.check_out_date.data
            guests = form.guests_count.data

            if check_in < date.today():
                flash('Дата заезда не может быть в прошлом', 'danger')
                return redirect(url_for('book_room', room_type_id=room_type_id))

            if check_out <= check_in:
                flash('Дата выезда должна быть позже даты заезда', 'danger')
                return redirect(url_for('book_room', room_type_id=room_type_id))

            if guests > room[2]:
                flash(f'Этот номер вмещает максимум {room[2]} гостей', 'danger')
                return redirect(url_for('book_room', room_type_id=room_type_id))

            nights = (check_out - check_in).days
            total_price = nights * float(room[3])

            session['booking_data'] = {
                'room_type_id': room_type_id,
                'check_in': check_in.isoformat(),
                'check_out': check_out.isoformat(),
                'guests_count': guests,
                'payment_method': form.payment_method.data,
                'total_price': total_price,
                'nights': nights
            }

            return redirect(url_for('add_travelers'))

        return render_template('bookings/book_room.html', title='Бронирование номера',
                               room=room, form=form)
    except Exception as e:
        flash(f'Ошибка: {e}', 'danger')
        return redirect(url_for('hotels'))


@app.route('/book/travelers', methods=['GET', 'POST'])
@login_required
def add_travelers():
    booking_data = session.get('booking_data')
    if not booking_data:
        flash('Пожалуйста, начните процесс бронирования заново', 'warning')
        return redirect(url_for('hotels'))

    guests_count = booking_data['guests_count']

    if request.method == 'POST':
        travelers = []
        valid = True

        for i in range(guests_count):
            name = request.form.get(f'traveler_{i}_name', '').strip()
            birth = request.form.get(f'traveler_{i}_birth', '').strip()
            passport = request.form.get(f'traveler_{i}_passport', '').strip()

            if not name or not birth or not passport:
                valid = False
                flash(f'Заполните все поля для гостя {i + 1}', 'danger')
                break

            travelers.append({
                'full_name': name,
                'birth_date': birth,
                'passport_number': passport
            })

        if valid:
            try:
                with connection() as con:
                    cur = con.execute('''
                        INSERT INTO booking 
                        (check_in_date, check_out_date, guests_count, total_price, 
                         payment_method, status, cancellation_fee, user_id, room_type_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    ''', (
                        booking_data['check_in'],
                        booking_data['check_out'],
                        booking_data['guests_count'],
                        booking_data['total_price'],
                        booking_data['payment_method'],
                        'new',
                        0,
                        current_user.id,
                        booking_data['room_type_id']
                    ))
                    booking_id = cur.fetchone()[0]

                    for t in travelers:
                        con.execute('''
                            INSERT INTO traveler (full_name, birth_date, passport_number, booking_id)
                            VALUES (%s, %s, %s, %s)
                        ''', (t['full_name'], t['birth_date'], t['passport_number'], booking_id))

                session.pop('booking_data', None)
                flash('Бронирование успешно создано!', 'success')
                return redirect(url_for('booking_details', booking_id=booking_id))

            except Exception as e:
                flash(f'Ошибка создания бронирования: {e}', 'danger')

    try:
        with connection() as con:
            room = con.execute('''
                SELECT rt.name, h.name, rt.price_per_night
                FROM room_type rt
                JOIN hotel h ON rt.hotel_id = h.id
                WHERE rt.id = %s
            ''', (booking_data['room_type_id'],)).fetchone()
    except:
        room = None

    return render_template('bookings/add_travelers.html', title='Данные гостей',
                           booking_data=booking_data, room=room,
                           guests_count=guests_count)


@app.route('/my-bookings')
@login_required
def my_bookings():
    try:
        with connection() as con:
            bookings = con.execute('''
                SELECT b.id, b.check_in_date, b.check_out_date, b.guests_count,
                       b.total_price, b.status, rt.name, h.name
                FROM booking b
                JOIN room_type rt ON b.room_type_id = rt.id
                JOIN hotel h ON rt.hotel_id = h.id
                WHERE b.user_id = %s
                ORDER BY b.check_in_date DESC
            ''', (current_user.id,)).fetchall()

        return render_template('my_bookings.html', title='Мои бронирования',
                               bookings=bookings, today=date.today())
    except Exception as e:
        flash(f'Ошибка загрузки бронирований: {e}', 'danger')
        return redirect(url_for('index'))


@app.route('/bookings/<int:booking_id>')
@login_required
def booking_details(booking_id):
    try:
        with connection() as con:
            booking = con.execute('''
                SELECT b.id, b.check_in_date, b.check_out_date, b.guests_count,
                       b.total_price, b.status, b.payment_method, b.cancellation_fee,
                       rt.name, h.name, c.name
                FROM booking b
                JOIN room_type rt ON b.room_type_id = rt.id
                JOIN hotel h ON rt.hotel_id = h.id
                JOIN city c ON h.city_id = c.id
                WHERE b.id = %s AND b.user_id = %s
            ''', (booking_id, current_user.id)).fetchone()

            if not booking:
                flash('Бронирование не найдено', 'danger')
                return redirect(url_for('my_bookings'))

            travelers = con.execute('''
                SELECT full_name, birth_date, passport_number
                FROM traveler WHERE booking_id = %s
            ''', (booking_id,)).fetchall()

        return render_template('bookings/details.html', title='Детали бронирования',
                               booking=booking, travelers=travelers, today=date.today())
    except Exception as e:
        flash(f'Ошибка загрузки бронирования: {e}', 'danger')
        return redirect(url_for('my_bookings'))


@app.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    try:
        with connection() as con:
            booking = con.execute('''
                SELECT id, check_in_date, status FROM booking
                WHERE id = %s AND user_id = %s
            ''', (booking_id, current_user.id)).fetchone()

            if not booking:
                flash('Бронирование не найдено', 'danger')
                return redirect(url_for('my_bookings'))

            if booking[2] == 'cancelled':
                flash('Бронирование уже отменено', 'warning')
                return redirect(url_for('my_bookings'))

            if booking[1] <= date.today():
                flash('Нельзя отменить бронирование после даты заезда', 'danger')
                return redirect(url_for('my_bookings'))

            con.execute("UPDATE booking SET status = 'cancelled' WHERE id = %s", (booking_id,))

        flash('Бронирование отменено', 'success')
        return redirect(url_for('my_bookings'))
    except Exception as e:
        flash(f'Ошибка отмены бронирования: {e}', 'danger')
        return redirect(url_for('my_bookings'))


@app.route('/manager')
@login_required
def manager_dashboard():
    if not current_user.is_manager():
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))

    try:
        with connection() as con:
            hotels_count = con.execute('SELECT COUNT(*) FROM hotel').fetchone()[0]
            rooms_count = con.execute('SELECT COUNT(*) FROM room_type').fetchone()[0]
            bookings_count = con.execute('SELECT COUNT(*) FROM booking').fetchone()[0]
    except:
        hotels_count = rooms_count = bookings_count = 0

    return render_template('manager/dashboard.html', title='Панель менеджера',
                           hotels_count=hotels_count, rooms_count=rooms_count,
                           bookings_count=bookings_count)


@app.route('/manager/hotels')
@login_required
def manager_hotels():
    if not current_user.is_manager():
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))

    try:
        with connection() as con:
            hotels = con.execute('''
                SELECT h.id, h.name, h.stars, c.name, co.name
                FROM hotel h
                JOIN city c ON h.city_id = c.id
                JOIN country co ON c.country_id = co.id
                ORDER BY h.name
            ''').fetchall()
        return render_template('manager/hotels/list.html', title='Управление гостиницами', hotels=hotels)
    except Exception as e:
        flash(f'Ошибка загрузки гостиниц: {e}', 'danger')
        return redirect(url_for('manager_dashboard'))


@app.route('/manager/hotels/add', methods=['GET', 'POST'])
@login_required
def manager_add_hotel():
    if not current_user.is_manager():
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))

    form = HotelForm()

    try:
        with connection() as con:
            cities = con.execute('''
                SELECT c.id, c.name, co.name
                FROM city c
                JOIN country co ON c.country_id = co.id
                ORDER BY co.name, c.name
            ''').fetchall()
            form.city_id.choices = [(c[0], f"{c[1]}, {c[2]}") for c in cities]
    except Exception as e:
        flash(f'Ошибка загрузки городов: {e}', 'danger')
        return redirect(url_for('manager_hotels'))

    if form.validate_on_submit():
        try:
            with connection() as con:
                con.execute('''
                    INSERT INTO hotel (name, stars, description, city_id)
                    VALUES (%s, %s, %s, %s)
                ''', (form.name.data, form.stars.data, form.description.data, form.city_id.data))
            flash('Гостиница добавлена!', 'success')
            return redirect(url_for('manager_hotels'))
        except Exception as e:
            flash(f'Ошибка добавления гостиницы: {e}', 'danger')

    return render_template('manager/hotels/form.html', title='Добавить гостиницу', form=form, action='Add')


@app.route('/manager/hotels/<int:hotel_id>/edit', methods=['GET', 'POST'])
@login_required
def manager_edit_hotel(hotel_id):
    if not current_user.is_manager():
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))

    form = HotelForm()

    try:
        with connection() as con:
            cities = con.execute('''
                SELECT c.id, c.name, co.name
                FROM city c
                JOIN country co ON c.country_id = co.id
                ORDER BY co.name, c.name
            ''').fetchall()
            form.city_id.choices = [(c[0], f"{c[1]}, {c[2]}") for c in cities]

            hotel = con.execute('''
                SELECT id, name, stars, description, city_id
                FROM hotel WHERE id = %s
            ''', (hotel_id,)).fetchone()

            if not hotel:
                flash('Гостиница не найдена', 'danger')
                return redirect(url_for('manager_hotels'))
    except Exception as e:
        flash(f'Ошибка загрузки данных: {e}', 'danger')
        return redirect(url_for('manager_hotels'))

    if form.validate_on_submit():
        try:
            with connection() as con:
                con.execute('''
                    UPDATE hotel SET name = %s, stars = %s, description = %s, city_id = %s
                    WHERE id = %s
                ''', (form.name.data, form.stars.data, form.description.data, form.city_id.data, hotel_id))
            flash('Гостиница обновлена!', 'success')
            return redirect(url_for('manager_hotels'))
        except Exception as e:
            flash(f'Ошибка обновления гостиницы: {e}', 'danger')

    elif request.method == 'GET':
        form.name.data = hotel[1]
        form.stars.data = hotel[2]
        form.description.data = hotel[3]
        form.city_id.data = hotel[4]

    return render_template('manager/hotels/form.html', title='Редактировать гостиницу',
                           form=form, action='Edit', hotel_id=hotel_id)


@app.route('/manager/hotels/<int:hotel_id>/delete', methods=['POST'])
@login_required
def manager_delete_hotel(hotel_id):
    if not current_user.is_manager():
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))

    try:
        with connection() as con:
            bookings = con.execute('''
                SELECT COUNT(*) FROM booking b
                JOIN room_type rt ON b.room_type_id = rt.id
                WHERE rt.hotel_id = %s
            ''', (hotel_id,)).fetchone()[0]

            if bookings > 0:
                flash('Нельзя удалить гостиницу с существующими бронированиями', 'danger')
                return redirect(url_for('manager_hotels'))

            con.execute('DELETE FROM hotel_amenity_link WHERE hotel_id = %s', (hotel_id,))
            con.execute(
                'DELETE FROM room_type_amenity WHERE room_type_id IN (SELECT id FROM room_type WHERE hotel_id = %s)',
                (hotel_id,))
            con.execute('DELETE FROM room_type WHERE hotel_id = %s', (hotel_id,))
            con.execute('DELETE FROM hotel WHERE id = %s', (hotel_id,))

        flash('Гостиница удалена!', 'success')
    except Exception as e:
        flash(f'Ошибка удаления гостиницы: {e}', 'danger')

    return redirect(url_for('manager_hotels'))


@app.route('/manager/hotels/<int:hotel_id>/rooms')
@login_required
def manager_hotel_rooms(hotel_id):
    if not current_user.is_manager():
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))

    try:
        with connection() as con:
            hotel = con.execute('SELECT id, name FROM hotel WHERE id = %s', (hotel_id,)).fetchone()
            if not hotel:
                flash('Гостиница не найдена', 'danger')
                return redirect(url_for('manager_hotels'))

            rooms = con.execute('''
                SELECT id, name, capacity, area, price_per_night, description
                FROM room_type WHERE hotel_id = %s
                ORDER BY price_per_night
            ''', (hotel_id,)).fetchall()

        return render_template('manager/rooms/list.html', title='Управление номерами',
                               hotel=hotel, rooms=rooms)
    except Exception as e:
        flash(f'Ошибка загрузки номеров: {e}', 'danger')
        return redirect(url_for('manager_hotels'))


@app.route('/manager/hotels/<int:hotel_id>/rooms/add', methods=['GET', 'POST'])
@login_required
def manager_add_room(hotel_id):
    if not current_user.is_manager():
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))

    form = RoomTypeForm()

    try:
        with connection() as con:
            hotel = con.execute('SELECT id, name FROM hotel WHERE id = %s', (hotel_id,)).fetchone()
            if not hotel:
                flash('Гостиница не найдена', 'danger')
                return redirect(url_for('manager_hotels'))
    except Exception as e:
        flash(f'Ошибка: {e}', 'danger')
        return redirect(url_for('manager_hotels'))

    if form.validate_on_submit():
        try:
            with connection() as con:
                con.execute('''
                    INSERT INTO room_type (name, capacity, area, price_per_night, description, hotel_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (form.name.data, form.capacity.data, form.area.data,
                      form.price_per_night.data, form.description.data, hotel_id))
            flash('Тип номера добавлен!', 'success')
            return redirect(url_for('manager_hotel_rooms', hotel_id=hotel_id))
        except Exception as e:
            flash(f'Ошибка добавления номера: {e}', 'danger')

    return render_template('manager/rooms/form.html', title='Добавить тип номера',
                           form=form, hotel=hotel, action='Add')


@app.route('/manager/rooms/<int:room_id>/edit', methods=['GET', 'POST'])
@login_required
def manager_edit_room(room_id):
    if not current_user.is_manager():
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))

    form = RoomTypeForm()

    try:
        with connection() as con:
            room = con.execute('''
                SELECT rt.id, rt.name, rt.capacity, rt.area, rt.price_per_night, 
                       rt.description, rt.hotel_id, h.name
                FROM room_type rt
                JOIN hotel h ON rt.hotel_id = h.id
                WHERE rt.id = %s
            ''', (room_id,)).fetchone()

            if not room:
                flash('Тип номера не найден', 'danger')
                return redirect(url_for('manager_hotels'))

            hotel = (room[6], room[7])
    except Exception as e:
        flash(f'Ошибка: {e}', 'danger')
        return redirect(url_for('manager_hotels'))

    if form.validate_on_submit():
        try:
            with connection() as con:
                con.execute('''
                    UPDATE room_type 
                    SET name = %s, capacity = %s, area = %s, price_per_night = %s, description = %s
                    WHERE id = %s
                ''', (form.name.data, form.capacity.data, form.area.data,
                      form.price_per_night.data, form.description.data, room_id))
            flash('Тип номера обновлён!', 'success')
            return redirect(url_for('manager_hotel_rooms', hotel_id=room[6]))
        except Exception as e:
            flash(f'Ошибка обновления номера: {e}', 'danger')

    elif request.method == 'GET':
        form.name.data = room[1]
        form.capacity.data = room[2]
        form.area.data = room[3]
        form.price_per_night.data = room[4]
        form.description.data = room[5]

    return render_template('manager/rooms/form.html', title='Редактировать тип номера',
                           form=form, hotel=hotel, action='Edit', room_id=room_id)


@app.route('/manager/rooms/<int:room_id>/delete', methods=['POST'])
@login_required
def manager_delete_room(room_id):
    if not current_user.is_manager():
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))

    try:
        with connection() as con:
            room = con.execute('SELECT hotel_id FROM room_type WHERE id = %s', (room_id,)).fetchone()
            if not room:
                flash('Тип номера не найден', 'danger')
                return redirect(url_for('manager_hotels'))

            hotel_id = room[0]

            bookings = con.execute('SELECT COUNT(*) FROM booking WHERE room_type_id = %s', (room_id,)).fetchone()[0]
            if bookings > 0:
                flash('Нельзя удалить тип номера с существующими бронированиями', 'danger')
                return redirect(url_for('manager_hotel_rooms', hotel_id=hotel_id))

            con.execute('DELETE FROM room_type_amenity WHERE room_type_id = %s', (room_id,))
            con.execute('DELETE FROM room_type WHERE id = %s', (room_id,))

        flash('Тип номера удалён!', 'success')
        return redirect(url_for('manager_hotel_rooms', hotel_id=hotel_id))
    except Exception as e:
        flash(f'Ошибка удаления номера: {e}', 'danger')
        return redirect(url_for('manager_hotels'))


@app.route('/manager/amenities')
@login_required
def manager_amenities():
    if not current_user.is_manager():
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))

    try:
        with connection() as con:
            hotel_amenities = con.execute('SELECT id, name FROM hotel_amenity ORDER BY name').fetchall()
            room_amenities = con.execute('SELECT id, name FROM room_amenity ORDER BY name').fetchall()
        return render_template('manager/amenities/list.html', title='Управление удобствами',
                               hotel_amenities=hotel_amenities, room_amenities=room_amenities)
    except Exception as e:
        flash(f'Ошибка загрузки удобств: {e}', 'danger')
        return redirect(url_for('manager_dashboard'))


@app.route('/manager/amenities/hotel/add', methods=['POST'])
@login_required
def manager_add_hotel_amenity():
    if not current_user.is_manager():
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))

    name = request.form.get('name', '').strip()
    if not name:
        flash('Введите название удобства', 'danger')
        return redirect(url_for('manager_amenities'))

    try:
        with connection() as con:
            con.execute('INSERT INTO hotel_amenity (name) VALUES (%s)', (name,))
        flash('Удобство гостиницы добавлено!', 'success')
    except Exception as e:
        flash(f'Ошибка: {e}', 'danger')

    return redirect(url_for('manager_amenities'))


@app.route('/manager/amenities/hotel/<int:amenity_id>/delete', methods=['POST'])
@login_required
def manager_delete_hotel_amenity(amenity_id):
    if not current_user.is_manager():
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))

    try:
        with connection() as con:
            con.execute('DELETE FROM hotel_amenity_link WHERE amenity_id = %s', (amenity_id,))
            con.execute('DELETE FROM hotel_amenity WHERE id = %s', (amenity_id,))
        flash('Удобство удалено!', 'success')
    except Exception as e:
        flash(f'Ошибка: {e}', 'danger')

    return redirect(url_for('manager_amenities'))


@app.route('/manager/amenities/room/add', methods=['POST'])
@login_required
def manager_add_room_amenity():
    if not current_user.is_manager():
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))

    name = request.form.get('name', '').strip()
    if not name:
        flash('Введите название удобства', 'danger')
        return redirect(url_for('manager_amenities'))

    try:
        with connection() as con:
            con.execute('INSERT INTO room_amenity (name) VALUES (%s)', (name,))
        flash('Удобство номера добавлено!', 'success')
    except Exception as e:
        flash(f'Ошибка: {e}', 'danger')

    return redirect(url_for('manager_amenities'))


@app.route('/manager/amenities/room/<int:amenity_id>/delete', methods=['POST'])
@login_required
def manager_delete_room_amenity(amenity_id):
    if not current_user.is_manager():
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))

    try:
        with connection() as con:
            con.execute('DELETE FROM room_type_amenity WHERE amenity_id = %s', (amenity_id,))
            con.execute('DELETE FROM room_amenity WHERE id = %s', (amenity_id,))
        flash('Удобство удалено!', 'success')
    except Exception as e:
        flash(f'Ошибка: {e}', 'danger')

    return redirect(url_for('manager_amenities'))


@app.route('/manager/hotels/<int:hotel_id>/amenities', methods=['GET', 'POST'])
@login_required
def manager_hotel_amenities(hotel_id):
    if not current_user.is_manager():
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))

    try:
        with connection() as con:
            hotel = con.execute('SELECT id, name FROM hotel WHERE id = %s', (hotel_id,)).fetchone()
            if not hotel:
                flash('Гостиница не найдена', 'danger')
                return redirect(url_for('manager_hotels'))

            if request.method == 'POST':
                selected = request.form.getlist('amenities')

                con.execute('DELETE FROM hotel_amenity_link WHERE hotel_id = %s', (hotel_id,))
                for amenity_id in selected:
                    con.execute('INSERT INTO hotel_amenity_link (hotel_id, amenity_id) VALUES (%s, %s)',
                                (hotel_id, int(amenity_id)))

                flash('Удобства гостиницы обновлены!', 'success')
                return redirect(url_for('manager_hotels'))

            all_amenities = con.execute('SELECT id, name FROM hotel_amenity ORDER BY name').fetchall()
            current_amenities = con.execute(
                'SELECT amenity_id FROM hotel_amenity_link WHERE hotel_id = %s', (hotel_id,)
            ).fetchall()
            current_ids = [a[0] for a in current_amenities]

        return render_template('manager/hotels/amenities.html', title='Удобства гостиницы',
                               hotel=hotel, all_amenities=all_amenities, current_ids=current_ids)
    except Exception as e:
        flash(f'Ошибка: {e}', 'danger')
        return redirect(url_for('manager_hotels'))


@app.route('/manager/rooms/<int:room_id>/amenities', methods=['GET', 'POST'])
@login_required
def manager_room_amenities(room_id):
    if not current_user.is_manager():
        flash('Доступ запрещён', 'danger')
        return redirect(url_for('index'))

    try:
        with connection() as con:
            room = con.execute('''
                SELECT rt.id, rt.name, rt.hotel_id, h.name
                FROM room_type rt
                JOIN hotel h ON rt.hotel_id = h.id
                WHERE rt.id = %s
            ''', (room_id,)).fetchone()

            if not room:
                flash('Тип номера не найден', 'danger')
                return redirect(url_for('manager_hotels'))

            if request.method == 'POST':
                selected = request.form.getlist('amenities')

                con.execute('DELETE FROM room_type_amenity WHERE room_type_id = %s', (room_id,))
                for amenity_id in selected:
                    con.execute('INSERT INTO room_type_amenity (room_type_id, amenity_id) VALUES (%s, %s)',
                                (room_id, int(amenity_id)))

                flash('Удобства номера обновлены!', 'success')
                return redirect(url_for('manager_hotel_rooms', hotel_id=room[2]))

            all_amenities = con.execute('SELECT id, name FROM room_amenity ORDER BY name').fetchall()
            current_amenities = con.execute(
                'SELECT amenity_id FROM room_type_amenity WHERE room_type_id = %s', (room_id,)
            ).fetchall()
            current_ids = [a[0] for a in current_amenities]

        return render_template('manager/rooms/amenities.html', title='Удобства номера',
                               room=room, all_amenities=all_amenities, current_ids=current_ids)
    except Exception as e:
        flash(f'Ошибка: {e}', 'danger')
        return redirect(url_for('manager_hotels'))