import telebot
from telebot import types
from xml.etree import ElementTree
from bs4 import BeautifulSoup
import config
from selenium.common.exceptions import InvalidArgumentException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

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


bot = telebot.TeleBot(config.token)


@bot.message_handler(commands=['start'])
def start(message):
    global tree, user_list, root
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
    s = 0
    for user in user_list:  # пошагово по юзерам
        if user.attrib.get('id') == str(message.from_user.id):  # нахождение текущего юзера
            s += 1
            if user.find('Stop') is not None:
                if user.find('Stop').get('name') is not None:  # есть ли отслеживаемые остановки
                    stops = ''
                    for i, stop in enumerate(user.findall('Stop')):
                        stops += str(i + 1) + ' - ' + ''.join(stop.get('name')) + '\n'
                    keyboard = types.InlineKeyboardMarkup(row_width=1)
                    buttons = [
                        (types.InlineKeyboardButton(text='Изменение остановки🚏✅', callback_data='button_select')),
                        (types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='button_add'))]
                    keyboard.add(buttons[0], buttons[1])
                    bot.send_message(message.from_user.id, f'Ваши остановки:\n{stops}', reply_markup=keyboard)
            elif user.find('Stop') is None:
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                button = types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='button_add')
                keyboard.add(button)
                bot.send_message(message.from_user.id, 'У вас нет отслеживаемых остановок', reply_markup=keyboard)
    if s == 0:  # если юзера нет
        ElementTree.SubElement(user_list, 'User', id=str(message.from_user.id))
        tree.write('users.xml', encoding="UTF-8")
        start(message)


@bot.callback_query_handler(func=lambda func: True)
def callback_button(callback):
    global user_list
    if callback.data == 'button_add':
        bot.send_message(callback.from_user.id, 'Вставьте ссылку на остановку:')
    if callback.data == 'button_select':
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                if len(user.findall('Stop')) != 0:
                    keyboard = types.InlineKeyboardMarkup(row_width=1)
                    for i, stop in enumerate(user.findall('Stop')):
                        buttons = [(types.InlineKeyboardButton(text=str(i + 1) + ' - ' + ''.join(stop.get('name')),
                                                               callback_data=f'button_selected_{i}')),
                                   types.InlineKeyboardButton(text='Назад🔙', callback_data='button_start')]
                        keyboard.add(buttons[0], buttons[1])
                    bot.send_message(callback.from_user.id, 'Выберите остановку:', reply_markup=keyboard)
    if str(callback.data)[:16] == 'button_selected_':
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        buttons = [(types.InlineKeyboardButton(text='Назад🔙', callback_data='button_select')),
                   (types.InlineKeyboardButton(text='Удалить остановку🚏➕',
                                               callback_data=f'button_delete_stop_{str(callback.data)[16:]}'))]
        keyboard.add(buttons[0], buttons[1])
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                for i, stop in enumerate(user.findall('Stop')):
                    if str(i) == str(callback.data)[16:]:
                        bot.send_message(callback.from_user.id, str(stop.get('name')) + ':\n', reply_markup=keyboard)
    if str(callback.data)[:19] == 'button_delete_stop_':
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                for i, stop in enumerate(user.findall('Stop')):
                    if str(i) == str(callback.data)[19:]:
                        user.remove(stop)
                        tree.write('users.xml', encoding="UTF-8")
                        start(callback)
    if callback.data == 'button_start':
        start(callback)


@bot.message_handler(func=lambda m: True)
def text_handler(message):
    global tree
    duplicate = False
    if str(message.text).find('http') != -1:
        bot.send_message(message.from_user.id, 'Ждите...')
        stop_name = name_stop(str(message.text)[str(message.text).find('http'):])
        if stop_name is None:
            bot.send_message(message.from_user.id, 'Ошибка, ссылка неверна, попробуйте снова')
            start(message)
        else:
            for user in user_list:
                if user.attrib.get('id') == str(message.from_user.id):
                    for i, stop in enumerate(user.findall('Stop')):
                        if stop.get('link') == str(message.text)[str(message.text).find('http'):]:
                            bot.send_message(message.from_user.id, 'Такая остановка уже есть')
                            duplicate = True
                    if not duplicate:
                        stop = ElementTree.SubElement(user, 'Stop')
                        stop.set('name', stop_name)
                        stop.set('link', str(message.text)[str(message.text).find('http'):])
                        tree.write('users.xml', encoding="UTF-8")
                        duplicate = False
            start(message)


bot.infinity_polling()
