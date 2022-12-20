import telebot
from telebot import types
import config
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from xml.etree import ElementTree
from bs4 import BeautifulSoup
from selenium.common.exceptions import InvalidArgumentException

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
                        stops += str(i + 1) + ' - ' + ''.join(stop.get('name')) + '\n'
                    keyboard = types.InlineKeyboardMarkup(row_width=1)
                    buttons = [
                        (types.InlineKeyboardButton(text='Выбор остановки🚏✅', callback_data='button_select')),
                        (types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='button_add_stop'))]
                    keyboard.add(buttons[0], buttons[1])
                    bot.send_message(message.from_user.id, f'Ваши остановки:\n{stops}', reply_markup=keyboard)
                    break
            elif user.find('Stop') is None:
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                button = types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='button_add_stop')
                keyboard.add(button)
                bot.send_message(message.from_user.id, 'У вас нет отслеживаемых остановок', reply_markup=keyboard)
                break
    else:  # если юзера нет
        ElementTree.SubElement(user_list, 'User', id=str(message.from_user.id))
        tree.write('users.xml', encoding="UTF-8")
        start(message)


@bot.callback_query_handler(func=lambda func: True)
def callback_button(callback):
    if callback.data == 'button_add_stop':
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        button = types.InlineKeyboardButton(text='Назад🔙', callback_data='button_start')
        keyboard.add(button)
        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                              text='Вставьте ссылку на остановку', reply_markup=keyboard)
    elif callback.data == 'button_select':
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                if len(user.findall('Stop')) != 0:
                    keyboard = types.InlineKeyboardMarkup(row_width=1)
                    for i, stop in enumerate(user.findall('Stop')):
                        button_stop = (types.InlineKeyboardButton(text=str(i + 1) + ' - ' + ''.join(stop.get('name')),
                                                                  callback_data=f'button_selected_{i}'))
                        keyboard.add(button_stop)
                    button_back = types.InlineKeyboardButton(text='Назад🔙', callback_data='button_start')
                    keyboard.add(button_back)
                    bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                          text='Выберите остановку:', reply_markup=keyboard)
    elif str(callback.data)[:16] == 'button_selected_':
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        buttons = [(types.InlineKeyboardButton(text='Назад🔙', callback_data='button_select')),
                   (types.InlineKeyboardButton(text='Удалить остановку🚏➕',
                                               callback_data=f'button_delete_stop_{str(callback.data)[16:]}')),
                   (types.InlineKeyboardButton(text='Добавить автобус🚌➕', callback_data='button_add_bus'))]
        keyboard.add(buttons[0], buttons[1], buttons[2])
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                for i, stop in enumerate(user.findall('Stop')):
                    if str(i) == str(callback.data)[16:]:
                        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                              text=str(stop.get('name')) + ':\n', reply_markup=keyboard)
    elif str(callback.data)[:19] == 'button_delete_stop_':
        for user in user_list:
            if user.attrib.get('id') == str(callback.from_user.id):
                for i, stop in enumerate(user.findall('Stop')):
                    if str(i) == str(callback.data)[19:]:
                        user.remove(stop)
                        tree.write('users.xml', encoding="UTF-8")
                        for user in user_list:  # пошагово по юзерам
                            if user.attrib.get('id') == str(callback.from_user.id):  # нахождение текущего юзера
                                if user.find('Stop') is not None:
                                    if user.find('Stop').get('name') is not None:  # есть ли отслеживаемые остановки
                                        stops = ''
                                        for i, stop in enumerate(user.findall('Stop')):
                                            stops += str(i + 1) + ' - ' + ''.join(stop.get('name')) + '\n'
                                        keyboard = types.InlineKeyboardMarkup(row_width=1)
                                        buttons = [
                                            (types.InlineKeyboardButton(text='Выбор остановки🚏✅',
                                                                        callback_data='button_select')),
                                            (types.InlineKeyboardButton(text='Добавить остановку🚏➕',
                                                                        callback_data='button_add_stop'))]
                                        keyboard.add(buttons[0], buttons[1])
                                        bot.edit_message_text(chat_id=callback.from_user.id,
                                                              message_id=callback.message.id,
                                                              text=f'Ваши остановки:\n{stops}', reply_markup=keyboard)
                                        break
                                elif user.find('Stop') is None:
                                    keyboard = types.InlineKeyboardMarkup(row_width=1)
                                    button = types.InlineKeyboardButton(text='Добавить остановку🚏➕',
                                                                        callback_data='button_add_stop')
                                    keyboard.add(button)
                                    bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                                          text='У вас нет отслеживаемых остановок',
                                                          reply_markup=keyboard)
                                    break
    elif callback.data == 'button_start':
        for user in user_list:  # пошагово по юзерам
            if user.attrib.get('id') == str(callback.from_user.id):  # нахождение текущего юзера
                if user.find('Stop') is not None:
                    if user.find('Stop').get('name') is not None:  # есть ли отслеживаемые остановки
                        stops = ''
                        for i, stop in enumerate(user.findall('Stop')):
                            stops += str(i + 1) + ' - ' + ''.join(stop.get('name')) + '\n'
                        keyboard = types.InlineKeyboardMarkup(row_width=1)
                        buttons = [
                            (types.InlineKeyboardButton(text='Выбор остановки🚏✅', callback_data='button_select')),
                            (types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='button_add_stop'))]
                        keyboard.add(buttons[0], buttons[1])
                        bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                              text=f'Ваши остановки:\n{stops}', reply_markup=keyboard)
                        break
                elif user.find('Stop') is None:
                    keyboard = types.InlineKeyboardMarkup(row_width=1)
                    button = types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='button_add_stop')
                    keyboard.add(button)
                    bot.edit_message_text(chat_id=callback.from_user.id, message_id=callback.message.id,
                                          text='У вас нет отслеживаемых остановок', reply_markup=keyboard)
                    break


@bot.message_handler(func=lambda m: True)
def text_handler(message):
    global tree
    duplicate = False
    if str(message.text).find('http') != -1:
        bot.send_message(message.from_user.id, 'Ждите...')
        stop_name = name_stop(str(message.text)[str(message.text).find('http'):])
        if stop_name is None:
            bot.edit_message_text(chat_id=message.from_user.id, message_id=message.id + 1,
                                  text='Ошибка, ссылка неверна, попробуйте снова')
            start(message)
        else:
            for user in user_list:
                if user.attrib.get('id') == str(message.from_user.id):
                    for i, stop in enumerate(user.findall('Stop')):
                        if stop.get('link') == str(message.text)[str(message.text).find('http'):]:
                            bot.edit_message_text(chat_id=message.from_user.id, message_id=message.id + 1,
                                                  text='Такая остановка уже есть')
                            duplicate = True
                    if not duplicate:
                        bot.delete_message(message.chat.id, message.message_id + 1)
                        stop = ElementTree.SubElement(user, 'Stop')
                        stop.set('name', stop_name)
                        stop.set('link', str(message.text)[str(message.text).find('http'):])
                        tree.write('users.xml', encoding="UTF-8")
                        duplicate = False
        start(message)


bot.infinity_polling()
