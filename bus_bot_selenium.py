import telebot
from telebot import types
from config import token
import sqlite3
from bs4 import BeautifulSoup
import datetime
from threading import Thread
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

options = Options()
options.headless = True
driver = webdriver.Firefox(options=options)

bot = telebot.TeleBot(token)

with sqlite3.connect("src/users.db") as database:  # создание бд
    cursor = database.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER,
    stop_name TEXT,
    stop_link TEXT,
    transport_name TEXT,
    transport_time_interval TEXT,
    transport_time_to_arrival INTEGER,
    transport_weekdays TEXT,
    tracked INTEGER
    )""")
    database.commit()


def name_stop(stop_link):
    try:
        driver.get(stop_link)
    except Exception:
        return None
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    try:
        n_stop = soup.find('h1', class_='card-title-view__title').text
    except AttributeError:
        return None
    return n_stop


def transport_list(stop_link):
    try:
        driver.get(stop_link)
    except Exception:
        return None
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    try:
        print(driver.current_url)
        # print(driver.page_source)
        vehicles = []
        for transport in soup.find_all(class_='masstransit-vehicle-snippet-view__main-text'):
            vehicles.append(transport.text)
            vehicles.sort()
    except AttributeError:
        return None
    return vehicles


def time_to_transport(stop_link, transport_name):
    driver.get(stop_link)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    vehicles = soup.find_all(class_='masstransit-vehicle-snippet-view__main-text')
    for transport in vehicles:
        if transport.text == transport_name:
            try:
                t_to_transport = transport.find_next(class_='masstransit-prognoses-view__title-text').text
            except AttributeError:
                t_to_transport = 'Не известно'
            return t_to_transport


def long_link(stop_link):
    driver.get(stop_link)
    print(driver.current_url)
    # print(driver.page_source)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    body = soup.find('body')
    scripts = body.find_all(name='script', type='text/javascript')
    for s, script in enumerate(scripts):
        if s == 1:
            link = str(script)[str(script).find('<link rel="canonical" href="') + 28:
                               str(script).find('"', str(script).find('<link rel="canonical" href="') + 28) + 1]
            return link


def stop_link(user_id, s):
    with sqlite3.connect('src/users.db') as database:
        cursor = database.cursor()
        for s_i, stop in enumerate(cursor.execute(f"""
        SELECT DISTINCT stop_link
        FROM users
        WHERE user_id={user_id}
        """).fetchall()):
            if str(s_i) == s:
                return stop[0]


@bot.message_handler(commands=['start'])
def start(message):
    with sqlite3.connect("src/users.db") as database:
        cursor = database.cursor()
        user_stops = cursor.execute(f"""
        SELECT DISTINCT stop_link, stop_name
        FROM users
        WHERE user_id={message.from_user.id}
        """).fetchall()
        if len(user_stops) != 0:
            stops = ''
            for i, stop in enumerate(user_stops):
                stops += str(stop[1]) + '\n'
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(types.InlineKeyboardButton(text='Выбор остановки🚏✔️', callback_data='stop_select'),
                         types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='stop_add'))
            bot.send_message(message.from_user.id, f'Ваши остановки:\n{stops} ', reply_markup=keyboard)
        else:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='stop_add'))
            bot.send_message(message.from_user.id, 'У вас нет отслеживаемых остановок', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda func: True)
def callback_button(callback):
    with open('log_callback_button.log', 'a', encoding='utf-8') as file:
        file.write(str(datetime.datetime.now()) + ' ' + str(callback.from_user.id) + ' ' + str(callback.data) + '\n')
    if callback.data == 'start':
        with sqlite3.connect("src/users.db") as database:
            cursor = database.cursor()
            user_stops = cursor.execute(f"""
            SELECT DISTINCT stop_name
            FROM users
            WHERE user_id={callback.from_user.id}
            """).fetchall()
            if len(user_stops) != 0:
                stops = ''
                for i, stop in enumerate(user_stops):
                    stops += str(stop[0]) + '\n'
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                keyboard.add(types.InlineKeyboardButton(text='Выбор остановки🚏✔️', callback_data='stop_select'),
                             types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='stop_add'))
                bot.edit_message_text(text=f'Ваши остановки:\n{stops}', chat_id=callback.from_user.id,
                                      message_id=callback.message.id, reply_markup=keyboard)
            else:
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                keyboard.add(
                    types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='stop_add'))
                bot.edit_message_text(text='У вас нет отслеживаемых остановок', chat_id=callback.from_user.id,
                                      message_id=callback.message.id, reply_markup=keyboard)
    elif callback.data == 'stop_add':
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(types.InlineKeyboardButton(text='Назад🔙', callback_data='start'))
        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                              text='Вставьте ссылку на остановку', reply_markup=keyboard)
    elif callback.data == 'stop_select':
        with sqlite3.connect("src/users.db") as database:
            cursor = database.cursor()
            user_stops = cursor.execute(f"""
            SELECT DISTINCT stop_link, stop_name
            FROM users
            WHERE user_id={callback.from_user.id}
            """).fetchall()
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            for s_i, stop in enumerate(user_stops):
                keyboard.add((types.InlineKeyboardButton(text=stop[1],
                                                         callback_data=f'stop_selected {s_i}')))
            keyboard.add(types.InlineKeyboardButton(text='Назад🔙', callback_data='start'))
            bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                  text='Выберите остановку:', reply_markup=keyboard)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'stop_selected':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        bot.edit_message_text(text='Пожалуйста подождите...', chat_id=callback.from_user.id,
                              message_id=callback.message.id)
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            for s_i, stop in enumerate(cursor.execute(f"""
            SELECT DISTINCT stop_link
            FROM users
            WHERE user_id={callback.from_user.id}
            """).fetchall()):
                if str(s_i) == s:
                    schedule = str(cursor.execute(f"""
                    SELECT DISTINCT stop_name
                    FROM users
                    WHERE user_id={callback.from_user.id}
                    AND stop_link='{stop[0]}'
                    """).fetchall()[0][0])
                    transport_from_database = cursor.execute(f"""
                    SELECT transport_name
                    FROM users
                    WHERE user_id={callback.from_user.id}
                    AND stop_link='{stop[0]}'
                    AND transport_name!='NULL'
                    """).fetchall()
                    if len(transport_from_database) != 0:
                        schedule += ':'
                        for transport in transport_from_database:
                            schedule += f'\n{transport[0]} - {time_to_transport(stop[0], transport[0])}'
                    keyboard = types.InlineKeyboardMarkup(row_width=1)
                    if len(transport_from_database) != 0:
                        transport_at_stop = transport_list(stop[0])
                        user_stop_transport = [str(vehicle[0]) for vehicle in transport_from_database]
                        user_stop_transport.sort()
                        if str(transport_at_stop).strip('[]') in str(user_stop_transport).strip('[]'):
                            keyboard.add(types.InlineKeyboardButton(text='Выбрать автобус🚌✔️',
                                                                    callback_data=f'transport_select {s_i}'))
                        else:
                            keyboard.add(types.InlineKeyboardButton(text='Выбрать автобус🚌✔️',
                                                                    callback_data=f'transport_select {s_i}'),
                                         types.InlineKeyboardButton(text='Добавить автобус🚌➕',
                                                                    callback_data=f'transport_add {s_i}'))
                        keyboard.add(types.InlineKeyboardButton(text='Обновить🔄️',
                                                                callback_data=f'stop_selected {s_i}'))
                    else:
                        keyboard.add(types.InlineKeyboardButton(text='Добавить автобус🚌➕',
                                                                callback_data=f'transport_add {s_i}'))
                    keyboard.add(types.InlineKeyboardButton(text='Удалить остановку➖',
                                                            callback_data=f'stop_delete {s_i}'),
                                 types.InlineKeyboardButton(text='Назад🔙', callback_data='stop_select'))
                    try:
                        bot.edit_message_text(text=schedule, chat_id=callback.from_user.id,
                                              message_id=callback.message.id, reply_markup=keyboard)
                    except telebot.apihelper.ApiTelegramException:
                        pass
                    break
    elif str(callback.data)[:str(callback.data).find(' ')] == 'stop_delete':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            for s_i, stop in enumerate(cursor.execute(f"""
            SELECT DISTINCT stop_link
            FROM users
            WHERE user_id={callback.from_user.id}
            """).fetchall()):
                if str(s_i) == s:
                    cursor.execute(f"""
                    DELETE FROM users
                    WHERE user_id={callback.from_user.id}
                    AND stop_link='{stop[0]}'
                    """)
                    database.commit()
                    callback.data = 'start'
                    callback_button(callback)
                    break
    elif str(callback.data)[:str(callback.data).find(' ')] == 'transport_add':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        bot.edit_message_text(text='Пожалуйста подождите...', chat_id=callback.from_user.id,
                              message_id=callback.message.id)
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            for s_i, stop in enumerate(cursor.execute(f"""
            SELECT DISTINCT stop_link
            FROM users
            WHERE user_id={callback.from_user.id}
            """).fetchall()):
                if str(s_i) == s:
                    transport_from_stop = transport_list(stop[0])
                    transport_from_database = cursor.execute(f"""
                    SELECT DISTINCT transport_name
                    FROM users
                    WHERE user_id={callback.from_user.id}
                    AND stop_link='{stop[0]}'
                    """).fetchall()
                    transport_from_database = [str(vehicle[0]) for vehicle in transport_from_database]
                    transport_from_database.sort()
                    keyboard = types.InlineKeyboardMarkup(row_width=1)
                    transport_to_add_in_database = [x for x in transport_from_stop if x not in transport_from_database]
                    for transport in transport_to_add_in_database:
                        keyboard.add(types.InlineKeyboardButton(text=transport,
                                                                callback_data=f'transport_selected_to_add {s_i} {transport}'))
                    keyboard.add(types.InlineKeyboardButton(text='Назад🔙', callback_data=f'stop_selected {s_i}'))
                    bot.edit_message_text(text='Выберите автобус:', chat_id=callback.from_user.id,
                                          message_id=callback.message.id, reply_markup=keyboard)
                    break
    elif str(callback.data)[:str(callback.data).find(' ')] == 'transport_select':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            for s_i, stop in enumerate(cursor.execute(f"""
            SELECT DISTINCT stop_link
            FROM users
            WHERE user_id={callback.from_user.id}
            """).fetchall()):
                if str(s_i) == s:
                    keyboard = types.InlineKeyboardMarkup(row_width=1)
                    for transport in cursor.execute(f"""
                    SELECT DISTINCT transport_name
                    FROM users
                    WHERE user_id={callback.from_user.id}
                    AND stop_link='{stop[0]}'
                    """).fetchall():
                        keyboard.add(types.InlineKeyboardButton(text=transport[0],
                                                                callback_data=f'transport_selected_to_setting {s_i} {transport[0]}'))
                    keyboard.add(types.InlineKeyboardButton(text='Назад🔙', callback_data=f'stop_selected {s_i}'))
                    bot.edit_message_text(text='Выберите автобус:', chat_id=callback.from_user.id,
                                          message_id=callback.message.id, reply_markup=keyboard)
                    break
    elif str(callback.data)[:str(callback.data).find(' ')] == 'transport_selected_to_add':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        t = data[1]
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            for s_i, stop in enumerate(cursor.execute(f"""
            SELECT DISTINCT stop_name, stop_link
            FROM users
            WHERE user_id={callback.from_user.id}
            """).fetchall()):
                if str(s_i) == s:
                    if cursor.execute(f"""
                    SELECT transport_name
                    FROM users
                    WHERE user_id={callback.from_user.id}
                    AND stop_link='{stop[1]}'
                    """).fetchall()[0][0] is None:
                        cursor.execute(f"""
                        UPDATE users
                        SET transport_name = '{t}'
                        WHERE user_id={callback.from_user.id}
                        AND stop_link='{stop[1]}'
                        """)
                    else:
                        cursor.execute(f"""
                        INSERT INTO users (
                        user_id, stop_name, stop_link, transport_name, transport_time_interval, transport_time_to_arrival)
                        VALUES ('{callback.from_user.id}', '{stop[0]}', '{stop[1]}', '{t}', 'Никогда', 0)
                        """)
                    database.commit()
                    callback.data = f'stop_selected {s_i}'
                    callback_button(callback)
                    break
    elif str(callback.data)[:str(callback.data).find(' ')] == 'transport_selected_to_setting':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        t = data[1]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            types.InlineKeyboardButton(text='Начало отслеживания⌚️',
                                       callback_data=f'setting_transport_time_interval {s} {t}'),
            types.InlineKeyboardButton(text='Время до прибытия⏲️',
                                       callback_data=f'setting_transport_time_to_arrival {s} {t}'),
            types.InlineKeyboardButton(text='Дни недели🗓️',
                                       callback_data=f'setting_transport_weekdays {s} {t}'),
            types.InlineKeyboardButton(text='Удалить автобус➖️',
                                       callback_data=f'transport_delete {s} {t}'),
            types.InlineKeyboardButton(text='Назад🔙',
                                       callback_data=f'transport_select {s}'))
        bot.edit_message_text(text=f'{t}:', chat_id=callback.from_user.id, message_id=callback.message.id,
                              reply_markup=keyboard)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'transport_delete':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        t = data[1]
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            s_l = stop_link(callback.from_user.id, s)
            if len(cursor.execute(f"""
            SELECT * FROM users
            WHERE user_id={callback.from_user.id} AND stop_link='{s_l}'
            """).fetchall()) == 1:
                cursor.execute(f"""
                UPDATE users
                SET transport_name = NULL, transport_time_interval = NULL,
                transport_time_to_arrival = NULL, transport_weekdays = NULL
                WHERE user_id={callback.from_user.id} AND stop_link='{s_l}'
                """)
            else:
                cursor.execute(f"""
                DELETE FROM users
                WHERE user_id={callback.from_user.id} AND stop_link='{s_l}' AND transport_name='{t}'
                """)
            database.commit()
            callback.data = f'stop_selected {s}'
            callback_button(callback)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'setting_transport_time_interval':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        t = data[1]
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton(text='-1час', callback_data=f'interval_hours {s} {t} -1'),
            types.InlineKeyboardButton(text='+1час', callback_data=f'interval_hours {s} {t} 1'),
            types.InlineKeyboardButton(text='-4час', callback_data=f'interval_hours {s} {t} -4'),
            types.InlineKeyboardButton(text='+4час', callback_data=f'interval_hours {s} {t} 4'),
            types.InlineKeyboardButton(text='-1мин', callback_data=f'interval_minutes {s} {t} -1'),
            types.InlineKeyboardButton(text='+1мин', callback_data=f'interval_minutes {s} {t} 1'),
            types.InlineKeyboardButton(text='-5мин', callback_data=f'interval_minutes {s} {t} -5'),
            types.InlineKeyboardButton(text='+5мин', callback_data=f'interval_minutes {s} {t} 5'),
            types.InlineKeyboardButton(text='Никогда', callback_data=f'interval_never {s} {t}'),
            types.InlineKeyboardButton(text='Сейчас', callback_data=f'interval_now {s} {t}'),
            types.InlineKeyboardButton(text='Назад🔙', callback_data=f'transport_selected_to_setting {s} {t}'))
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            time_interval = cursor.execute(f"""
            SELECT transport_time_interval FROM users
            WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}' AND transport_name='{t}'
            """).fetchall()[0][0]
        bot.edit_message_text(text=f'Настройте начало отслеживания:\n{time_interval}', chat_id=callback.from_user.id,
                              message_id=callback.message.id, reply_markup=keyboard)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'interval_hours':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        t = data[1]
        h = data[2]
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            interval = cursor.execute(f"""
            SELECT transport_time_interval FROM users
            WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
            AND transport_name='{t}'
            """).fetchall()[0][0]
            if interval in ['Никогда', 'Сейчас']:
                hours = int(h)
                minutes = 0
            else:
                interval = str(interval).split(':')
                hours = int(interval[0]) + int(h)
                minutes = int(interval[1])
            if hours <= -1:
                hours = 24 - abs(hours)
            elif hours >= 24:
                hours = hours % 24
            if hours < 10:
                hours = '0' + str(hours)
            if minutes < 10:
                minutes = '0' + str(minutes)
            cursor.execute(f"""
            UPDATE users
            SET transport_time_interval = '{hours}:{minutes}'
            WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
            AND transport_name='{t}'
            """)
            database.commit()
            callback.data = f'setting_transport_time_interval {s} {t}'
            callback_button(callback)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'interval_minutes':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        t = data[1]
        m = data[2]
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            interval = cursor.execute(f"""
                    SELECT transport_time_interval FROM users
                    WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
                    AND transport_name='{t}'
                    """).fetchall()[0][0]
            if interval in ['Никогда', 'Сейчас']:
                hours = 0
                minutes = int(m)
            else:
                interval = str(interval).split(':')
                hours = int(interval[0])
                minutes = int(interval[1]) + int(m)
            if minutes <= -1:
                minutes = 60 - abs(minutes)
            elif minutes >= 60:
                minutes = minutes % 60
            if minutes < 10:
                minutes = '0' + str(minutes)
            if hours < 10:
                hours = '0' + str(hours)
            cursor.execute(f"""
                    UPDATE users
                    SET transport_time_interval = '{hours}:{minutes}'
                    WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
                    AND transport_name='{t}'
                    """)
            database.commit()
            callback.data = f'setting_transport_time_interval {s} {t}'
            callback_button(callback)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'interval_never':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        t = data[1]
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            if cursor.execute(f"""
            SELECT transport_time_interval FROM users
            WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
            AND transport_name='{t}'
            """).fetchall()[0][0] != 'Никогда':
                cursor.execute(f"""
                UPDATE users
                SET transport_time_interval = 'Никогда'
                WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
                AND transport_name='{t}'
                """)
                database.commit()
                callback.data = f'setting_transport_time_interval {s} {t}'
                callback_button(callback)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'interval_now':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        t = data[1]
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            if cursor.execute(f"""
                    SELECT transport_time_interval FROM users
                    WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
                    AND transport_name='{t}'
                    """).fetchall()[0][0] != str(datetime.datetime.now().strftime("%H:%M")):
                cursor.execute(f"""
                        UPDATE users
                        SET transport_time_interval = '{datetime.datetime.now().strftime("%H:%M")}'
                        WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
                        AND transport_name='{t}'
                        """)
                database.commit()
                callback.data = f'setting_transport_time_interval {s} {t}'
                callback_button(callback)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'setting_transport_time_to_arrival':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        t = data[1]
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton(text='-1мин', callback_data=f'arrival_minutes {s} {t} -1'),
            types.InlineKeyboardButton(text='+1мин', callback_data=f'arrival_minutes {s} {t} 1'),
            types.InlineKeyboardButton(text='-5мин', callback_data=f'arrival_minutes {s} {t} -5'),
            types.InlineKeyboardButton(text='+5мин', callback_data=f'arrival_minutes {s} {t} 5'),
            types.InlineKeyboardButton(text='Назад🔙', callback_data=f'transport_selected_to_setting {s} {t}'))
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            time_to_arrival = cursor.execute(f"""
            SELECT transport_time_to_arrival FROM users
            WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}' AND transport_name='{t}'
            """).fetchall()[0][0]
        bot.edit_message_text(text=f'Настройте время до прибытия(+/- 1мин):\n{time_to_arrival} мин',
                              chat_id=callback.from_user.id,
                              message_id=callback.message.id, reply_markup=keyboard)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'arrival_minutes':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        t = data[1]
        m = data[2]
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            interval = cursor.execute(f"""
            SELECT transport_time_to_arrival FROM users
            WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
            AND transport_name='{t}'
            """).fetchall()[0][0]
            if not (interval == 0 and int(m) < 0):
                minutes = interval + int(m)
                if minutes < 0:
                    minutes = 0
                cursor.execute(f"""
                UPDATE users
                SET transport_time_to_arrival = {minutes}
                WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
                AND transport_name='{t}'
                """)
                database.commit()
                callback.data = f'setting_transport_time_to_arrival {s} {t}'
                callback_button(callback)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'setting_transport_weekdays':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        t = data[1]
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            weekdays = str(cursor.execute(f"""
            SELECT transport_weekdays FROM users
            WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
            AND transport_name='{t}'
            """).fetchall()[0][0])
            names_weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            for w_i, name_weekday in enumerate(names_weekdays):
                if weekdays.find(str(w_i)) != -1:
                    keyboard.add(
                        types.InlineKeyboardButton(text=f'{name_weekday}✔️', callback_data=f'weekday {s} {t} {w_i}'))
                else:
                    keyboard.add(
                        types.InlineKeyboardButton(text=f'{name_weekday}✖️', callback_data=f'weekday {s} {t} {w_i}'))
            keyboard.add(
                types.InlineKeyboardButton(text='Вся неделя', callback_data=f'weekdays_all_week {s} {t}'),
                types.InlineKeyboardButton(text='Будни', callback_data=f'weekdays_workdays {s} {t}'),
                types.InlineKeyboardButton(text='Выходные', callback_data=f'weekdays_weekends {s} {t}'),
                types.InlineKeyboardButton(text='Назад🔙', callback_data=f'transport_selected_to_setting {s} {t}'))

            bot.edit_message_text(text='Выберите дни недели:', chat_id=callback.from_user.id,
                                  message_id=callback.message.id, reply_markup=keyboard)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'weekday':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        t = data[1]
        w = data[2]
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            weekdays = str(cursor.execute(f"""
            SELECT transport_weekdays FROM users
            WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
            AND transport_name='{t}'
            """).fetchall()[0][0])
            if weekdays.find(w) != -1:
                weekdays = weekdays.replace(f'{w} ', '')
            elif weekdays == 'None':
                weekdays = f'{w} '
            else:
                weekdays += f'{w} '
            weekdays = weekdays.split()
            weekdays.sort()
            weekdays = ' '.join(weekdays) + ' '
            cursor.execute(f"""
            UPDATE users
            SET transport_weekdays = '{weekdays}'
            WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
            AND transport_name='{t}'
            """)
            database.commit()
        callback.data = f'setting_transport_weekdays {s} {t}'
        callback_button(callback)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'weekdays_all_week':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        t = data[1]
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            weekdays = str(cursor.execute(f"""
                        SELECT transport_weekdays FROM users
                        WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
                        AND transport_name='{t}'
                        """).fetchall()[0][0])
            if weekdays != '0 1 2 3 4 5 6 ':
                weekdays = "'0 1 2 3 4 5 6 '"
            else:
                weekdays = 'NULL'
            cursor.execute(f"""
                        UPDATE users
                        SET transport_weekdays = {weekdays}
                        WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
                        AND transport_name='{t}'
                        """)
            database.commit()
        callback.data = f'setting_transport_weekdays {s} {t}'
        callback_button(callback)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'weekdays_workdays':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        t = data[1]
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            weekdays = str(cursor.execute(f"""
            SELECT transport_weekdays FROM users
            WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
            AND transport_name='{t}'
            """).fetchall()[0][0])
            if weekdays != '0 1 2 3 4 ':
                weekdays = "'0 1 2 3 4 '"
            else:
                weekdays = 'NULL'
            cursor.execute(f"""
            UPDATE users
            SET transport_weekdays = {weekdays}
            WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
            AND transport_name='{t}'
            """)
            database.commit()
        callback.data = f'setting_transport_weekdays {s} {t}'
        callback_button(callback)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'weekdays_weekends':
        data = str(callback.data)[str(callback.data).find(' ') + 1:].split()
        s = data[0]
        t = data[1]
        with sqlite3.connect('src/users.db') as database:
            cursor = database.cursor()
            weekdays = str(cursor.execute(f"""
            SELECT transport_weekdays FROM users
            WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
            AND transport_name='{t}'
            """).fetchall()[0][0])
            if weekdays != '5 6 ':
                weekdays = "'5 6 '"
            else:
                weekdays = 'NULL'
            cursor.execute(f"""
            UPDATE users
            SET transport_weekdays = {weekdays}
            WHERE user_id={callback.from_user.id} AND stop_link='{stop_link(callback.from_user.id, s)}'
            AND transport_name='{t}'
            """)
            database.commit()
        callback.data = f'setting_transport_weekdays {s} {t}'
        callback_button(callback)


@bot.message_handler(func=lambda m: True)
def text_handler(message):
    if str(message.text).find('yandex.ru/maps/') != -1:
        bot.send_message(message.from_user.id, 'Пожалуйста подождите...')
        link = str(message.text)[str(message.text).find('http'):]
        if link.find('/stops/') == -1:
            link = long_link(link)
        if link.find('/stops/') != -1:
            link = link[:link.find('/', link.find('/stops/') + 7) + 1]
            stop_name = name_stop(link)
            if stop_name is None:
                bot.edit_message_text(text=f'Ошибка, ссылка неверна, попробуйте снова',
                                      chat_id=message.from_user.id,
                                      message_id=message.id + 1)
                start(message)
            elif stop_name is not None:
                with sqlite3.connect("src/users.db") as database:
                    cursor = database.cursor()
                    if len(cursor.execute(f"""SELECT DISTINCT *
                    FROM users
                    WHERE user_id='{message.from_user.id}'
                    AND stop_link='{link}'""").fetchall()) == 0:
                        cursor.execute(f"""INSERT INTO users (
                        user_id, stop_name, stop_link, transport_time_interval, transport_time_to_arrival)
                        VALUES ('{message.from_user.id}', '{name_stop(link)}', '{link}', 'Никогда', 0)""")
                        bot.edit_message_text(text='Остановка успешно добавлена', chat_id=message.from_user.id,
                                              message_id=message.id + 1)
                    else:
                        bot.edit_message_text(text='Такая остановка уже есть', chat_id=message.from_user.id,
                                              message_id=message.id + 1)
                start(message)
        else:
            bot.edit_message_text(text='Ошибка, ссылка не ведёт на остановку, попробуйте снова',
                                  chat_id=message.from_user.id, message_id=message.id + 1)
            start(message)
    else:
        bot.send_message(chat_id=message.from_user.id, text='Ошибка, попробуйте снова')
        start(message)


flag_check_time_interval = True


def check_time_interval():
    global flag_check_time_interval
    while True:
        time = datetime.datetime.now() - datetime.timedelta(minutes=1)
        if int(datetime.datetime.now().strftime('%S')) == 0 and flag_check_time_interval:
            with sqlite3.connect('src/users.db') as database:
                cursor = database.cursor()
                cursor.execute(f"""
                UPDATE users
                SET tracked = 1
                WHERE transport_time_interval='{time.strftime('%H:%M')}'
                AND transport_weekdays LIKE '%{int(datetime.datetime.now().strftime('%u')) - 1}%'
                """)
            flag_check_time_interval = False
        elif int(datetime.datetime.now().strftime('%S')) != 0:
            flag_check_time_interval = True


flag_notification = True


def notification():
    global flag_notification
    while True:
        if int(datetime.datetime.now().strftime('%S')) == 0 and flag_notification:
            with sqlite3.connect('src/users.db') as database:
                cursor = database.cursor()
                tracked_vehicles = cursor.execute(f"""
                SELECT user_id, stop_name, stop_link, transport_name, transport_time_to_arrival FROM users
                WHERE tracked=1
                """).fetchall()
                for vehicle in tracked_vehicles:
                    time_arrival = str(time_to_transport(vehicle[2], vehicle[3]))
                    if time_arrival.find(':') != -1:
                        continue
                    try:
                        time_arrival = int(time_arrival[:-4])
                    except ValueError:
                        continue
                    print(vehicle[3], time_arrival)
                    if time_arrival == vehicle[4] - 1 or time_arrival == vehicle[4]:
                        bot.send_message(chat_id=vehicle[0],
                                         text=f'ВНИМАНИЕ‼️ {vehicle[3]} приедет через {time_arrival} мин')
                        cursor.execute(f"""
                        UPDATE users
                        SET tracked=0
                        WHERE user_id={vehicle[0]} AND stop_link='{vehicle[2]}'
                        AND transport_name='{vehicle[3]}'
                        """)
            flag_notification = False
        elif int(datetime.datetime.now().strftime('%S')) != 0:
            flag_notification = True


Thread(target=bot.infinity_polling).start()
Thread(target=check_time_interval).start()
Thread(target=notification).start()
