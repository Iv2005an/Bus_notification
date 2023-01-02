import telebot
from telebot import types
from config import token
import sqlite3
from bs4 import BeautifulSoup
import time
from session import session, headers

bot = telebot.TeleBot(token)

with sqlite3.connect("users.db") as database:  # создание бд
    cursor = database.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
                        user_id INTEGER,
                        stop_name TEXT,
                        stop_link TEXT,
                        transport_name TEXT,
                        transport_time_interval INTEGER,
                        transport_time_to_arrival TEXT)""")
    database.commit()


def name_stop(stop_link):
    try:
        response = session.get(stop_link, headers=headers)
    except Exception:
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        n_stop = soup.find('h1', class_='card-title-view__title').text
    except AttributeError:
        return None
    return n_stop


def transport_list(stop_link):
    try:
        response = session.get(stop_link, headers=headers)
    except Exception:
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        print(response.text)
        vehicles = []
        for transport in soup.find_all(class_='masstransit-vehicle-snippet-view__main-text'):
            vehicles.append(transport.text)
            vehicles.sort()
    except AttributeError:
        return None
    return vehicles


def time_to_transport(stop_link, transport_name):
    response = session.get(stop_link, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    vehicles = soup.find_all(class_='masstransit-vehicle-snippet-view__main-text')
    for transport in vehicles:
        if transport.text == transport_name:
            t_to_transport = transport.find_next(class_='masstransit-prognoses-view__title-text').text
            return t_to_transport


def long_link(response):
    print(response.url)
    soup = BeautifulSoup(response.text, 'html.parser')
    body = soup.find('body')
    scripts = body.find_all(name='script', type='text/javascript')
    for s, script in enumerate(scripts):
        if s == 1:
            link = str(script)[str(script).find('<link rel="canonical" href="') + 28:
                               str(script).find('"', str(script).find('<link rel="canonical" href="') + 28) + 1]
            return link


@bot.message_handler(commands=['start'])
def start(message):
    with sqlite3.connect("users.db") as database:
        cursor = database.cursor()
        user_stops = cursor.execute(
            f"""SELECT DISTINCT stop_name
            FROM users
            WHERE user_id={message.from_user.id}""").fetchall()
        if len(user_stops) != 0:
            stops = ''
            for i, stop in enumerate(user_stops):
                stops += str(stop[0]) + '\n'
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(types.InlineKeyboardButton(text='Выбор остановки🚏✔️', callback_data='button_stop_select'),
                         types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='button_stop_add'))
            bot.send_message(message.from_user.id, f'Ваши остановки:\n{stops}', reply_markup=keyboard)
        else:
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='button_stop_add'))
            bot.send_message(message.from_user.id, 'У вас нет отслеживаемых остановок', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda func: True)
def callback_button(callback):
    with open('log_callback_button.log', 'a', encoding='utf-8') as file:
        file.write(str(time.strftime("%H:%M:%S", time.localtime())) + ' ' +
                   str(callback.from_user.id) + ' ' + str(callback.data) + '\n')
    if callback.data == 'button_start':
        with sqlite3.connect("users.db") as database:
            cursor = database.cursor()
            user_stops = cursor.execute(
                f"""SELECT DISTINCT stop_name
                FROM users
                WHERE user_id={callback.from_user.id}""").fetchall()
            if len(user_stops) != 0:
                stops = ''
                for i, stop in enumerate(user_stops):
                    stops += str(stop[0]) + '\n'
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                keyboard.add(types.InlineKeyboardButton(text='Выбор остановки🚏✔️', callback_data='button_stop_select'),
                             types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='button_stop_add'))
                bot.edit_message_text(text=f'Ваши остановки:\n{stops}', chat_id=callback.from_user.id,
                                      message_id=callback.message.id, reply_markup=keyboard)
            else:
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                keyboard.add(
                    types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='button_stop_add'))
                bot.edit_message_text(text='У вас нет отслеживаемых остановок', chat_id=callback.from_user.id,
                                      message_id=callback.message.id, reply_markup=keyboard)
    elif callback.data == 'button_stop_add':
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(types.InlineKeyboardButton(text='Назад🔙', callback_data='button_start'))
        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                              text='Вставьте ссылку на остановку', reply_markup=keyboard)
    elif callback.data == 'button_stop_select':
        with sqlite3.connect("users.db") as database:
            cursor = database.cursor()
            user_stops = cursor.execute(
                f"""SELECT DISTINCT stop_name
                FROM users
                WHERE user_id={callback.from_user.id}""").fetchall()
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            for s_i, stop in enumerate(user_stops):
                keyboard.add((types.InlineKeyboardButton(text=stop[0],
                                                         callback_data=f'button_stop_selected {s_i}')))
            keyboard.add(types.InlineKeyboardButton(text='Назад🔙', callback_data='button_start'))
            bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                  text='Выберите остановку:', reply_markup=keyboard)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'button_stop_selected':
        with sqlite3.connect('users.db') as database:
            cursor = database.cursor()
            for s_i, stop in enumerate(cursor.execute(
                    f"""SELECT DISTINCT stop_link
                    FROM users
                    WHERE user_id={callback.from_user.id}""").fetchall()):
                if str(s_i) == str(callback.data)[str(callback.data).find(' ') + 1:]:
                    schedule = str(cursor.execute(f"""SELECT DISTINCT stop_name
                    FROM users
                    WHERE user_id={callback.from_user.id}
                    AND stop_link='{stop[0]}'""").fetchall()[0][0])
                    transport_from_database = cursor.execute(f"""SELECT transport_name
                    FROM users
                    WHERE user_id={callback.from_user.id}
                    AND stop_link='{stop[0]}'
                    AND transport_name!='NULL'""").fetchall()
                    if len(transport_from_database) != 0:
                        schedule += ':'
                        for transport in transport_from_database:
                            schedule += f'\n{transport[0]} - {time_to_transport(stop[0], transport[0])}'
                    keyboard = types.InlineKeyboardMarkup(row_width=2)
                    keyboard.add(types.InlineKeyboardButton(text='Назад🔙', callback_data='button_stop_select'),
                                 types.InlineKeyboardButton(text='Удалить остановку➖',
                                                            callback_data=f'button_stop_delete {s_i}'))
                    if len(transport_from_database) != 0:
                        transport_at_stop = transport_list(stop[0])
                        user_stop_transport = [str(vehicle[0]) for vehicle in transport_from_database]
                        user_stop_transport.sort()
                        if str(transport_at_stop).strip('[]') in str(user_stop_transport).strip('[]'):
                            keyboard.add(types.InlineKeyboardButton(text='Выбрать автобус🚌✔️',
                                                                    callback_data=f'button_transport_add {s_i}'))
                        else:
                            keyboard.add(types.InlineKeyboardButton(text='Выбрать автобус🚌✔️',
                                                                    callback_data=f'button_transport_add {s_i}'),
                                         types.InlineKeyboardButton(text='Добавить автобус🚌➕',
                                                                    callback_data=f'button_transport_add {s_i}'))
                        keyboard.add(types.InlineKeyboardButton(text='Обновить🔄️',
                                                                callback_data=f'button_stop_selected {s_i}'))
                    else:
                        keyboard.add(types.InlineKeyboardButton(text='Добавить автобус🚌➕',
                                                                callback_data=f'button_transport_add {s_i}'))
                    try:
                        bot.edit_message_text(text=schedule, chat_id=callback.from_user.id,
                                              message_id=callback.message.id, reply_markup=keyboard)
                    except telebot.apihelper.ApiTelegramException:
                        pass
                    break
    elif str(callback.data)[:str(callback.data).find(' ')] == 'button_stop_delete':
        with sqlite3.connect('users.db') as database:
            cursor = database.cursor()
            for s_i, stop in enumerate(cursor.execute(
                    f"""SELECT DISTINCT stop_link
                    FROM users
                    WHERE user_id={callback.from_user.id}""").fetchall()):
                if str(s_i) == str(callback.data)[str(callback.data).find(' ') + 1:]:
                    cursor.execute(
                        f"""DELETE FROM users WHERE user_id={callback.from_user.id} AND stop_link='{stop[0]}'""")
                    database.commit()
                    callback.data = 'button_start'
                    callback_button(callback)
                    break
    elif str(callback.data)[:str(callback.data).find(' ')] == 'button_transport_add':
        with sqlite3.connect('users.db') as database:
            cursor = database.cursor()
            bot.send_message(callback.from_user.id, 'Пожалуйста подождите...')
            for s_i, stop in enumerate(cursor.execute(
                    f"""SELECT DISTINCT stop_link
                    FROM users
                    WHERE user_id={callback.from_user.id}""").fetchall()):
                if str(s_i) == str(callback.data)[str(callback.data).find(' ') + 1:]:
                    transport_from_stop = transport_list(stop[0])
                    transport_from_database = cursor.execute(
                        f"""SELECT DISTINCT transport_name
                        FROM users
                        WHERE user_id={callback.from_user.id}
                        AND stop_link='{stop[0]}'""").fetchall()
                    transport_from_database = [str(vehicle[0]) for vehicle in transport_from_database]
                    transport_from_database.sort()
                    keyboard = types.InlineKeyboardMarkup(row_width=1)
                    if transport_from_database[0][0] is None:
                        for transport in transport_from_stop:
                            keyboard.add(types.InlineKeyboardButton(text=transport,
                                                                    callback_data=f'transport_selected_to_add {transport}'))
                    print(transport_from_stop)
                    print(transport_from_database)
                    keyboard.add(types.InlineKeyboardButton(text='Назад🔙', callback_data=f'button_stop_selected {s_i}'))
                    bot.edit_message_text(text='Выберите автобус:', chat_id=callback.from_user.id,
                                          message_id=callback.message.id + 1, reply_markup=keyboard)
                    break
    # elif str(callback.data)[:str(callback.data).find(' ')] == 'button_bus_add':
    #     for user in user_list:
    #         if user.attrib.get('id') == str(callback.from_user.id):
    #             for s_i, stop in enumerate(user.findall('Stop')):
    #                 if str(s_i) == str(callback.data)[str(callback.data).find(' ') + 1:]:
    #                     bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
    #                                           text='Пожалуйста подождите...')
    #                     buses_from_stop = buses_list(stop.get('link'))
    #                     keyboard = types.InlineKeyboardMarkup(row_width=1)
    #                     duplicate = False
    #                     for b_i, bus_from_stop in enumerate(buses_from_stop):
    #                         for bus in stop.findall('Bus'):
    #                             if bus.get('name') == bus_from_stop.text:
    #                                 duplicate = True
    #                         if not duplicate:
    #                             keyboard.add(types.InlineKeyboardButton
    #                                          (text=buses_from_stop[b_i].text,
    #                                           callback_data=f'button_bus_selected_to_add {s_i} {bus_from_stop.text}'))
    #                         duplicate = False
    #                     keyboard.add(types.InlineKeyboardButton(text='Назад🔙',
    #                                                             callback_data=f'button_stop_selected {s_i}'))
    #                     buses = ''
    #                     for bus in stop.findall('Bus'):
    #                         buses += bus.get('name') + '\n'
    #                     bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
    #                                           text=f'{stop.get("name")}:\n{buses}Выберите автобус:',
    #                                           reply_markup=keyboard)
    # elif str(callback.data)[:str(callback.data).find(' ')] == 'button_bus_selected_to_add':
    #     s = str(callback.data)[
    #         str(callback.data).find(' ') + 1:str(callback.data).find(' ', str(callback.data).find(' ') + 1)]
    #     bus_name = str(callback.data)[str(callback.data).rfind(' ') + 1:]
    #     keyboard = types.InlineKeyboardMarkup(row_width=2)
    #     buttons = [(types.InlineKeyboardButton(text='Назад🔙', callback_data='button_stop_select')),
    #                (types.InlineKeyboardButton(text='Удалить остановку➖',
    #                                            callback_data=f'button_stop_delete {s}'))]
    #     keyboard.add(buttons[0], buttons[1])
    #     for user in user_list:
    #         if user.attrib.get('id') == str(callback.from_user.id):
    #             for s_i, stop in enumerate(user.findall('Stop')):
    #                 if str(s_i) == s:
    #                     bus = ElementTree.SubElement(stop, 'Bus')
    #                     bus.set('name', bus_name)
    #                     tree.write('users.xml', encoding="UTF-8")
    #                     buses = ''
    #                     bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
    #                                           text='Пожалуйста подождите...')
    #                     buses_from_stop = buses_list(stop.get('link'))
    #                     all_bus = True
    #                     duplicate = False
    #                     for bus_from_stop in buses_from_stop:
    #                         for bus in stop.findall('Bus'):
    #                             if bus.get('name') == bus_from_stop.text:
    #                                 duplicate = True
    #                                 break
    #                         if duplicate:
    #                             duplicate = False
    #                         else:
    #                             all_bus = False
    #                             break
    #                     if all_bus:
    #                         for bus in stop.findall('Bus'):
    #                             buses += bus.get('name') + '\n'
    #                         keyboard.add(types.InlineKeyboardButton(text='Выбрать автобус🚌✔️',
    #                                                                 callback_data=f'button_bus_select {s_i}'))
    #                     elif stop.find('Bus') is None:
    #                         keyboard.add(types.InlineKeyboardButton(text='Добавить автобус🚌➕',
    #                                                                 callback_data=f'button_bus_add {s_i}'))
    #                     elif stop.find('Bus') is not None:
    #                         for bus in stop.findall('Bus'):
    #                             buses += bus.get('name') + '\n'
    #                         buttons = [(types.InlineKeyboardButton(text='Выбрать автобус🚌✔️',
    #                                                                callback_data=f'button_bus_select {s_i}')),
    #                                    types.InlineKeyboardButton(text='Добавить автобус🚌➕',
    #                                                               callback_data=f'button_bus_add {s_i}')]
    #                         keyboard.add(buttons[0], buttons[1])
    #                     bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
    #                                           text=str(stop.get('name')) + ':\n' + buses, reply_markup=keyboard)
    # elif str(callback.data)[:str(callback.data).find(' ')] == 'button_bus_select':
    #     s = str(callback.data)[str(callback.data).find(' ') + 1:]
    #     for user in user_list:
    #         if user.attrib.get('id') == str(callback.from_user.id):
    #             keyboard = types.InlineKeyboardMarkup(row_width=1)
    #             for s_i, stop in enumerate(user.findall('Stop')):
    #                 if str(s_i) == s:
    #                     for b_i, bus in enumerate(stop.findall('Bus')):
    #                         keyboard.add(types.InlineKeyboardButton(text=bus.get('name'),
    #                                                                 callback_data=f'button_bus_selected_to_setting {s_i} {b_i}'))
    #                     keyboard.add(
    #                         types.InlineKeyboardButton(text='Назад🔙', callback_data=f'button_stop_selected {s_i}'))
    #                     bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
    #                                           text='Выберите автобус:', reply_markup=keyboard)
    # elif str(callback.data)[:str(callback.data).find(' ')] == 'button_bus_selected_to_setting':
    #     s = str(callback.data)[
    #         str(callback.data).find(' ') + 1:str(callback.data).find(' ', str(callback.data).find(' ') + 1)]
    #     b = str(callback.data)[str(callback.data).find(' ', str(callback.data).find(' ') + 1) + 1:]
    #     for user in user_list:
    #         if user.attrib.get('id') == str(callback.from_user.id):
    #             for s_i, stop in enumerate(user.findall('Stop')):
    #                 if str(s_i) == s:
    #                     for b_i, bus in enumerate(stop.findall('Bus')):
    #                         if str(b_i) == b:
    #                             t_to_bus = time_to_bus(stop.get('link'), bus.get('name'))
    #                             bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
    #                                                   text=f'{bus.get("name")} будет через: {t_to_bus}.')
    #     start(callback)


@bot.message_handler(func=lambda m: True)
def text_handler(message):
    if str(message.text).find('yandex.ru/maps/') != -1:
        bot.send_message(message.from_user.id, 'Пожалуйста подождите...')
        link = str(message.text)[str(message.text).find('http'):]
        if link.find('/stops/') == -1:
            response = session.get(link, headers=headers)
            link = long_link(response)
        if link.find('/stops/') != -1:
            link = link[:link.find('/', link.find('/stops/') + 7) + 1]
            stop_name = name_stop(link)
            if stop_name is None:
                bot.edit_message_text(text=f'Ошибка, ссылка неверна, попробуйте снова',
                                      chat_id=message.from_user.id,
                                      message_id=message.id + 1)
                start(message)
            elif stop_name is not None:
                with sqlite3.connect("users.db") as database:
                    cursor = database.cursor()
                    if len(cursor.execute(f"""SELECT DISTINCT *
                    FROM users
                    WHERE user_id='{message.from_user.id}'
                    AND stop_link='{link}'""").fetchall()) == 0:
                        cursor.execute(f"""INSERT INTO users (user_id, stop_name, stop_link)
                        VALUES ('{message.from_user.id}', '{name_stop(link)}', '{link}')""")
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


bot.infinity_polling()
