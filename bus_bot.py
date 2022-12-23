import telebot
from telebot import types
import config
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from xml.etree import ElementTree
from bs4 import BeautifulSoup
from selenium.common.exceptions import InvalidArgumentException
import time

bot = telebot.TeleBot(config.token)
op = webdriver.ChromeOptions()
op.add_argument('headless')
ChromeDriverManager(path="drivers").install()
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=op)

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
        driver.get(stop_link)
    except InvalidArgumentException:
        return None
    soup = BeautifulSoup(driver.page_source, 'lxml')
    try:
        n_stop = soup.find('h1', class_='card-title-view__title').text
    except AttributeError:
        return None
    return n_stop


def buses_list(stop_link):
    try:
        driver.get(stop_link)
    except InvalidArgumentException:
        return None
    soup = BeautifulSoup(driver.page_source, 'lxml')
    try:
        buses = soup.find_all(class_='masstransit-vehicle-snippet-view__main-text')
    except AttributeError:
        return None
    return buses


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
                                                             callback_data=f'button_stop_selected{s_i}')))
                keyboard.add(types.InlineKeyboardButton(text='Назад🔙', callback_data='button_start'))
                bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                      text='Выберите остановку:', reply_markup=keyboard)
    elif str(callback.data)[:20] == 'button_stop_selected':
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        buttons = [(types.InlineKeyboardButton(text='Назад🔙', callback_data='button_stop_select')),
                   (types.InlineKeyboardButton(text='Удалить остановку➖',
                                               callback_data=f'button_stop_delete{str(callback.data)[20:]}'))]
        keyboard.add(buttons[0], buttons[1])
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                for s_i, stop in enumerate(user.findall('Stop')):
                    if str(s_i) == str(callback.data)[20:]:
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
                                                                    callback_data=f'button_bus_select{s_i}'))
                        elif stop.find('Bus') is None:
                            keyboard.add(types.InlineKeyboardButton(text='Добавить автобус🚌➕',
                                                                    callback_data=f'button_bus_add{s_i}'))
                        elif stop.find('Bus') is not None:
                            for bus in stop.findall('Bus'):
                                buses += bus.get('name') + '\n'
                            buttons = [(types.InlineKeyboardButton(text='Выбрать автобус🚌✔️',
                                                                   callback_data=f'button_bus_select{s_i}')),
                                       types.InlineKeyboardButton(text='Добавить автобус🚌➕',
                                                                  callback_data=f'button_bus_add{s_i}')]
                            keyboard.add(buttons[0], buttons[1])
                        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                              text=str(stop.get('name')) + ':\n' + buses, reply_markup=keyboard)
    elif str(callback.data)[:18] == 'button_stop_delete':
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                for s_i, stop in enumerate(user.findall('Stop')):
                    if str(s_i) == str(callback.data)[18:]:
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
    elif str(callback.data)[:14] == 'button_bus_add':
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                for s_i, stop in enumerate(user.findall('Stop')):
                    if str(s_i) == str(callback.data)[14:]:
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
                                              callback_data=f'button_bus_selected_to_add{s_i} {bus_from_stop.text}'))
                            duplicate = False
                        keyboard.add(types.InlineKeyboardButton(text='Назад🔙',
                                                                callback_data=f'button_stop_selected{s_i}'))
                        buses = ''
                        for bus in stop.findall('Bus'):
                            buses += bus.get('name') + '\n'
                        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                              text=f'{stop.get("name")}:\n{buses}Выберите автобус:',
                                              reply_markup=keyboard)
    elif str(callback.data)[:26] == 'button_bus_selected_to_add':
        s = str(callback.data)[26:str(callback.data).find(' ')]
        bus_name = str(callback.data)[str(callback.data).rfind(' ') + 1:]
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        buttons = [(types.InlineKeyboardButton(text='Назад🔙', callback_data='button_stop_select')),
                   (types.InlineKeyboardButton(text='Удалить остановку➖',
                                               callback_data=f'button_stop_delete{str(callback.data)[20:]}'))]
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
                                                                    callback_data=f'button_bus_select{s_i}'))
                        elif stop.find('Bus') is None:
                            keyboard.add(types.InlineKeyboardButton(text='Добавить автобус🚌➕',
                                                                    callback_data=f'button_bus_add{s_i}'))
                        elif stop.find('Bus') is not None:
                            for bus in stop.findall('Bus'):
                                buses += bus.get('name') + '\n'
                            buttons = [(types.InlineKeyboardButton(text='Выбрать автобус🚌✔️',
                                                                   callback_data=f'button_bus_select{s_i}')),
                                       types.InlineKeyboardButton(text='Добавить автобус🚌➕',
                                                                  callback_data=f'button_bus_add{s_i}')]
                            keyboard.add(buttons[0], buttons[1])
                        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                              text=str(stop.get('name')) + ':\n' + buses, reply_markup=keyboard)
    elif str(callback.data)[:17] == 'button_bus_select':
        s = str(callback.data)[17:]
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                for s_i, stop in enumerate(user.findall('Stop')):
                    if str(s_i) == s:
                        for b_i, bus in enumerate(stop.findall('Bus')):
                            keyboard.add(types.InlineKeyboardButton(text=bus.get('name'),
                                                                    callback_data=f'button_bus_selected_to_setting{s_i} {b_i}'))
                        keyboard.add(
                            types.InlineKeyboardButton(text='Назад🔙', callback_data=f'button_stop_selected{s_i}'))
                        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                              text='Выберите автобус:', reply_markup=keyboard)
    elif str(callback.data)[:30] == 'button_bus_selected_to_setting':
        s = str(callback.data)[26:str(callback.data).find(' ')]
        b = str(callback.data)[str(callback.data).rfind(' ') + 1:]


@bot.message_handler(func=lambda m: True)
def text_handler(message):
    global tree
    if str(message.text).find('yandex.ru/maps') != -1:
        duplicate = False
        link = str(message.text)[str(message.text).find('http'):]
        bot.send_message(message.from_user.id, 'Пожалуйста подождите...')
        if link.find('/org/') != -1 or link.find('/-/') != -1:
            driver.get(link)
            link = driver.current_url
        if link.find('/stops/') != -1:
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


bot.polling()
