import telebot
from telebot import types
from xml.etree import ElementTree
from selenium.common.exceptions import InvalidArgumentException
from selenium import webdriver
from bs4 import BeautifulSoup
import config


def name_stop(stop_link):
    op = webdriver.ChromeOptions()
    op.add_argument('headless')
    driver = webdriver.Chrome(options=op)
    try:
        driver.get(stop_link)
    except InvalidArgumentException:
        return None
    soup = BeautifulSoup(driver.page_source, 'lxml')
    n_stop = soup.find('h1', class_='card-title-view__title').text
    return n_stop


bot = telebot.TeleBot(config.token)


@bot.message_handler(commands=['start'])
def start(message):
    global tree, user_list
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
                    buttons = [(types.InlineKeyboardButton(text='Выбрать остановку🚏✅', callback_data='button_select')),
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
        # stop = ElementTree.SubElement(user, 'Stop')
        # bus = ElementTree.SubElement(stop, 'Bus')
        # time_before_arrival = ElementTree.SubElement(bus, 'time_before_arrival')
        # time_interval = ElementTree.SubElement(bus, 'time_interval')
        tree.write('users.xml')
        start(message)


add = False


@bot.callback_query_handler(func=lambda func: True)
def callback_button(callback):
    global add
    if callback.data == 'button_add':
        bot.send_message(callback.from_user.id, 'Вставьте ссылку на остановку:')
        add = True


@bot.message_handler(func=lambda m: True)
def text_handler(message):
    global add, tree
    if add:
        bot.send_message(message.from_user.id, 'Ждите...')
        stop_name = name_stop(message.text)
        if stop_name is None:
            bot.send_message(message.from_user.id, 'Ошибка, ссылка неверна, попробуйте снова')
            start(message)
        else:
            for user in user_list:
                if user.attrib.get('id') == str(message.from_user.id):
                    stop = ElementTree.SubElement(user, 'Stop')
                    stop.set('name', stop_name)
                    stop.set('link', message.text)
                    tree.write('users.xml', encoding="UTF-8")
            start(message)
        add = False


bot.infinity_polling()
