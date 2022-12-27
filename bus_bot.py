import telebot
from telebot import types
import config
from xml.etree import ElementTree
from bs4 import BeautifulSoup
import time
import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from urllib3.util import ssl_

CIPHERS = """ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-SHA256:AES256-SHA"""


class TlsAdapter(HTTPAdapter):

    def __init__(self, ssl_options=0, **kwargs):
        self.ssl_options = ssl_options
        super(TlsAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, *pool_args, **pool_kwargs):
        ctx = ssl_.create_urllib3_context(ciphers=CIPHERS, cert_reqs=ssl.CERT_REQUIRED, options=self.ssl_options)
        self.poolmanager = PoolManager(*pool_args, ssl_context=ctx, **pool_kwargs)


headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'ru, en; q=0.9',
    'device-memory': '8',
    'downlink': '3.2',
    'dpr': '2',
    'ect': '4g',
    'rtt': '100',
    'sec-ch-ua': 'Chromium;v=106, Yandex;v=22, Not;A=Brand;v=99',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': 'macOS',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 YaBrowser/22.11.3.823 Yowser/2.5 Safari/537.36',
    'viewport-width': '1470'
}
session = requests.session()
adapter = TlsAdapter(ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1)
session.mount("https://", adapter)
bot = telebot.TeleBot(config.token)

try:
    tree = ElementTree.parse('users.xml')  # инициализация дерева
except FileNotFoundError:  # если файла нет
    with open('users.xml', 'w'):
        root = ElementTree.Element('User_list')  # создание корня
        tree = ElementTree.ElementTree(root)  # создание дерева
        tree.write('users.xml')
except ElementTree.ParseError:  # если файл пустой
    root = ElementTree.Element('User_list')  # создание корня
    tree = ElementTree.ElementTree(root)  # создание дерева
    tree.write('users.xml')
user_list = tree.getroot()  # инициализация корня


def name_stop(stop_link):
    try:
        response = session.get(stop_link, headers=headers)
        response.encoding = 'utf-8'
    except Exception:
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        n_stop = soup.find('h1', class_='card-title-view__title').text
    except AttributeError:
        return None
    return n_stop


def buses_list(stop_link):
    try:
        response = session.get(stop_link, headers=headers)
        response.encoding = 'utf-8'
    except Exception:
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        buses = soup.find_all(class_='masstransit-vehicle-snippet-view__main-text')
    except AttributeError:
        return None
    return buses


def time_to_bus(stop_link, name_bus):
    response = session.get(stop_link, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    buses = soup.find_all(class_='masstransit-vehicle-snippet-view__main-text')
    for bus in buses:
        if bus.text == name_bus:
            t_to_bus = bus.find_next(class_='masstransit-prognoses-view__title-text').text
            return t_to_bus


def long_link(response):
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
    global tree, user_list
    tree = ElementTree.parse('users.xml')
    user_list = tree.getroot()
    for user in user_list:  # пошагово по юзерам
        if user.attrib.get('id') == str(message.from_user.id):  # нахождение текущего юзера
            if user.find('Stop') is not None:
                if user.find('Stop').get('name') is not None:  # есть ли отслеживаемые остановки
                    stops = ''
                    for i, stop in enumerate(user.findall('Stop')):
                        stops += stop.get('name') + '\n'
                    keyboard = types.InlineKeyboardMarkup(row_width=1)
                    buttons = [
                        (types.InlineKeyboardButton(text='Выбор остановки🚏✔️', callback_data='button_stop_select')),
                        (types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='button_stop_add'))]
                    keyboard.add(buttons[0], buttons[1])
                    bot.send_message(message.from_user.id, f'Ваши остановки:\n{stops}', reply_markup=keyboard)
                    break
            elif user.find('Stop') is None:
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                keyboard.add(
                    types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='button_stop_add'))
                bot.send_message(message.from_user.id, 'У вас нет отслеживаемых остановок', reply_markup=keyboard)
                break
    else:  # если юзера нет
        ElementTree.SubElement(user_list, 'User', id=str(message.from_user.id))
        tree.write('users.xml', encoding="UTF-8")
        start(message)


@bot.callback_query_handler(func=lambda func: True)
def callback_button(callback):
    with open('log_callback_button.log', 'a', encoding='utf-8') as file:
        file.write(str(time.strftime("%H:%M:%S", time.localtime())) + ' ' +
                   str(callback.from_user.id) + ' ' + str(callback.data) + '\n')
    if callback.data == 'button_start':
        for user in user_list:  # пошагово по юзерам
            if user.attrib.get('id') == str(callback.from_user.id):  # нахождение текущего юзера
                if user.find('Stop') is not None:
                    if user.find('Stop').get('name') is not None:  # есть ли отслеживаемые остановки
                        stops = ''
                        for s_i, stop in enumerate(user.findall('Stop')):
                            stops += stop.get('name') + '\n'
                        keyboard = types.InlineKeyboardMarkup(row_width=1)
                        buttons = [
                            (types.InlineKeyboardButton(text='Выбор остановки🚏✔️',
                                                        callback_data='button_stop_select')),
                            (types.InlineKeyboardButton(text='Добавить остановку🚏➕',
                                                        callback_data='button_stop_add'))]
                        keyboard.add(buttons[0], buttons[1])
                        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                              text=f'Ваши остановки:\n{stops}', reply_markup=keyboard)
                elif user.find('Stop') is None:
                    keyboard = types.InlineKeyboardMarkup(row_width=1)
                    keyboard.add(
                        types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='button_stop_add'))
                    bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                          text='У вас нет отслеживаемых остановок', reply_markup=keyboard)
    elif callback.data == 'button_stop_add':
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(types.InlineKeyboardButton(text='Назад🔙', callback_data='button_start'))
        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                              text='Вставьте ссылку на остановку', reply_markup=keyboard)
    elif callback.data == 'button_stop_select':
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                for s_i, stop in enumerate(user.findall('Stop')):
                    keyboard.add((types.InlineKeyboardButton(text=stop.get('name'),
                                                             callback_data=f'button_stop_selected {s_i}')))
                keyboard.add(types.InlineKeyboardButton(text='Назад🔙', callback_data='button_start'))
                bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                      text='Выберите остановку:', reply_markup=keyboard)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'button_stop_selected':
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        buttons = [(types.InlineKeyboardButton(text='Назад🔙', callback_data='button_stop_select')),
                   (types.InlineKeyboardButton(text='Удалить остановку➖',
                                               callback_data=f'button_stop_delete {str(callback.data)[str(callback.data).find(" ") + 1:]}'))]
        keyboard.add(buttons[0], buttons[1])
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                for s_i, stop in enumerate(user.findall('Stop')):
                    if str(s_i) == str(callback.data)[str(callback.data).find(' ') + 1:]:
                        buses = ''
                        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                              text='Пожалуйста подождите...')
                        buses_from_stop = buses_list(stop.get('link'))
                        all_bus = True
                        duplicate = False
                        for bus_from_stop in buses_from_stop:
                            for bus in stop.findall('Bus'):
                                if bus.get('name') == bus_from_stop.text:
                                    duplicate = True
                                    break
                            if duplicate:
                                duplicate = False
                            else:
                                all_bus = False
                                break
                        if all_bus:
                            for bus in stop.findall('Bus'):
                                buses += bus.get('name') + '\n'
                            keyboard.add(types.InlineKeyboardButton(text='Выбрать автобус🚌✔️',
                                                                    callback_data=f'button_bus_select {s_i}'))
                        elif stop.find('Bus') is None:
                            keyboard.add(types.InlineKeyboardButton(text='Добавить автобус🚌➕',
                                                                    callback_data=f'button_bus_add {s_i}'))
                        elif stop.find('Bus') is not None:
                            for bus in stop.findall('Bus'):
                                buses += bus.get('name') + '\n'
                            buttons = [(types.InlineKeyboardButton(text='Выбрать автобус🚌✔️',
                                                                   callback_data=f'button_bus_select {s_i}')),
                                       types.InlineKeyboardButton(text='Добавить автобус🚌➕',
                                                                  callback_data=f'button_bus_add {s_i}')]
                            keyboard.add(buttons[0], buttons[1])
                        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                              text=str(stop.get('name')) + ':\n' + buses, reply_markup=keyboard)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'button_stop_delete':
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                for s_i, stop in enumerate(user.findall('Stop')):
                    if str(s_i) == str(callback.data)[str(callback.data).find(' ') + 1:]:
                        user.remove(stop)
                        tree.write('users.xml', encoding="UTF-8")
                        if user.find('Stop') is not None:
                            if user.find('Stop').get('name') is not None:  # есть ли отслеживаемые остановки
                                stops = ''
                                for s_i, stop in enumerate(user.findall('Stop')):
                                    stops += stop.get('name') + '\n'
                                keyboard = types.InlineKeyboardMarkup(row_width=1)
                                buttons = [
                                    (types.InlineKeyboardButton(text='Выбор остановки🚏✔️',
                                                                callback_data='button_stop_select')),
                                    (types.InlineKeyboardButton(text='Добавить остановку🚏➕',
                                                                callback_data='button_stop_add'))]
                                keyboard.add(buttons[0], buttons[1])
                                bot.edit_message_text(chat_id=callback.from_user.id,
                                                      message_id=callback.message.id,
                                                      text=f'Ваши остановки:\n{stops}', reply_markup=keyboard)
                        elif user.find('Stop') is None:
                            keyboard = types.InlineKeyboardMarkup(row_width=1)
                            keyboard.add(types.InlineKeyboardButton(text='Добавить остановку🚏➕',
                                                                    callback_data='button_stop_add'))
                            bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                                  text='У вас нет отслеживаемых остановок',
                                                  reply_markup=keyboard)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'button_bus_add':
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                for s_i, stop in enumerate(user.findall('Stop')):
                    if str(s_i) == str(callback.data)[str(callback.data).find(' ') + 1:]:
                        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                              text='Пожалуйста подождите...')
                        buses_from_stop = buses_list(stop.get('link'))
                        keyboard = types.InlineKeyboardMarkup(row_width=1)
                        duplicate = False
                        for b_i, bus_from_stop in enumerate(buses_from_stop):
                            for bus in stop.findall('Bus'):
                                if bus.get('name') == bus_from_stop.text:
                                    duplicate = True
                            if not duplicate:
                                keyboard.add(types.InlineKeyboardButton
                                             (text=buses_from_stop[b_i].text,
                                              callback_data=f'button_bus_selected_to_add {s_i} {bus_from_stop.text}'))
                            duplicate = False
                        keyboard.add(types.InlineKeyboardButton(text='Назад🔙',
                                                                callback_data=f'button_stop_selected {s_i}'))
                        buses = ''
                        for bus in stop.findall('Bus'):
                            buses += bus.get('name') + '\n'
                        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                              text=f'{stop.get("name")}:\n{buses}Выберите автобус:',
                                              reply_markup=keyboard)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'button_bus_selected_to_add':
        s = str(callback.data)[
            str(callback.data).find(' ') + 1:str(callback.data).find(' ', str(callback.data).find(' ') + 1)]
        bus_name = str(callback.data)[str(callback.data).rfind(' ') + 1:]
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        buttons = [(types.InlineKeyboardButton(text='Назад🔙', callback_data='button_stop_select')),
                   (types.InlineKeyboardButton(text='Удалить остановку➖',
                                               callback_data=f'button_stop_delete {s}'))]
        keyboard.add(buttons[0], buttons[1])
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                for s_i, stop in enumerate(user.findall('Stop')):
                    if str(s_i) == s:
                        bus = ElementTree.SubElement(stop, 'Bus')
                        bus.set('name', bus_name)
                        tree.write('users.xml', encoding="UTF-8")
                        buses = ''
                        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                              text='Пожалуйста подождите...')
                        buses_from_stop = buses_list(stop.get('link'))
                        all_bus = True
                        duplicate = False
                        for bus_from_stop in buses_from_stop:
                            for bus in stop.findall('Bus'):
                                if bus.get('name') == bus_from_stop.text:
                                    duplicate = True
                                    break
                            if duplicate:
                                duplicate = False
                            else:
                                all_bus = False
                                break
                        if all_bus:
                            for bus in stop.findall('Bus'):
                                buses += bus.get('name') + '\n'
                            keyboard.add(types.InlineKeyboardButton(text='Выбрать автобус🚌✔️',
                                                                    callback_data=f'button_bus_select {s_i}'))
                        elif stop.find('Bus') is None:
                            keyboard.add(types.InlineKeyboardButton(text='Добавить автобус🚌➕',
                                                                    callback_data=f'button_bus_add {s_i}'))
                        elif stop.find('Bus') is not None:
                            for bus in stop.findall('Bus'):
                                buses += bus.get('name') + '\n'
                            buttons = [(types.InlineKeyboardButton(text='Выбрать автобус🚌✔️',
                                                                   callback_data=f'button_bus_select {s_i}')),
                                       types.InlineKeyboardButton(text='Добавить автобус🚌➕',
                                                                  callback_data=f'button_bus_add {s_i}')]
                            keyboard.add(buttons[0], buttons[1])
                        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                              text=str(stop.get('name')) + ':\n' + buses, reply_markup=keyboard)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'button_bus_select':
        s = str(callback.data)[str(callback.data).find(' ') + 1:]
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                for s_i, stop in enumerate(user.findall('Stop')):
                    if str(s_i) == s:
                        for b_i, bus in enumerate(stop.findall('Bus')):
                            keyboard.add(types.InlineKeyboardButton(text=bus.get('name'),
                                                                    callback_data=f'button_bus_selected_to_setting {s_i} {b_i}'))
                        keyboard.add(
                            types.InlineKeyboardButton(text='Назад🔙', callback_data=f'button_stop_selected {s_i}'))
                        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                              text='Выберите автобус:', reply_markup=keyboard)
    elif str(callback.data)[:str(callback.data).find(' ')] == 'button_bus_selected_to_setting':
        s = str(callback.data)[
            str(callback.data).find(' ') + 1:str(callback.data).find(' ', str(callback.data).find(' ') + 1)]
        b = str(callback.data)[str(callback.data).find(' ', str(callback.data).find(' ') + 1) + 1:]
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                for s_i, stop in enumerate(user.findall('Stop')):
                    if str(s_i) == s:
                        for b_i, bus in enumerate(stop.findall('Bus')):
                            if str(b_i) == b:
                                t_to_bus = time_to_bus(stop.get('link'), bus.get('name'))
                                bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                                      text=f'{bus.get("name")} будет через: {t_to_bus}.')
        start(callback)


@bot.message_handler(func=lambda m: True)
def text_handler(message):
    global tree
    if str(message.text).find('yandex.ru/maps/') != -1:
        bot.send_message(message.from_user.id, 'Пожалуйста подождите...')
        duplicate = False
        link = str(message.text)[str(message.text).find('http'):]
        if link.find('/stops/') == -1:
            response = session.get(link, headers=headers)
            response.encoding = 'utf-8'
            link = long_link(response)
        if link.find('/stops/') != -1:
            link = link[:link.find('/', link.find('stop__')) + 1]
            stop_name = name_stop(link[link.find('http'):])
            if stop_name is None:
                bot.edit_message_text(chat_id=message.from_user.id, message_id=message.id + 1,
                                      text='Ошибка, ссылка неверна, попробуйте снова')
                start(message)
            elif stop_name is not None:
                for user in user_list:
                    if user.attrib.get('id') == str(message.from_user.id):
                        for stop in user.findall('Stop'):
                            if stop.get('link') == link[link.find('http'):]:
                                bot.edit_message_text(chat_id=message.from_user.id, message_id=message.id + 1,
                                                      text='Такая остановка уже есть')
                                duplicate = True
                        if not duplicate:
                            stop = ElementTree.SubElement(user, 'Stop')
                            stop.set('name', stop_name)
                            stop.set('link', link[link.find('http'):])
                            tree.write('users.xml', encoding="UTF-8")
                            bot.delete_message(message.chat.id, message.message_id + 1)
                start(message)
        else:
            bot.edit_message_text(chat_id=message.from_user.id, message_id=message.id + 1,
                                  text='Ошибка, ссылка не ведёт на остановку, попробуйте снова')
            start(message)


bot.infinity_polling()
