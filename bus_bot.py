import telebot
from telebot import types
from xml.etree import ElementTree
import config

bot = telebot.TeleBot(config.token)


@bot.message_handler(commands=['start'])
def start(message):
    try:
        tree = ElementTree.parse('users.xml')  # инициализация дерева
    except FileNotFoundError:  # если файла нет
        with open('users.xml', 'w'):
            start(message)
    except ElementTree.ParseError:  # если файл пустой
        root = ElementTree.Element('User_list')  # создание корня
        tree = ElementTree.ElementTree(root)  # создание дерева
        tree.write('users.xml')
    user_list = tree.getroot()  # инициализация корня
    s = 0
    for user in user_list:  # пошагово по юзерам
        if user.attrib.get('id') == str(message.from_user.id):  # нахождение текущего юзера
            s += 1
            if s > 1:  # удаление повторяющихся юзеров
                user_list.remove(user)
                tree.write('users.xml', encoding="UTF-8")
            elif user.find('Stop').get('name') is not None:  # есть ли отслеживаемые остановки
                stops = ''
                for i, stop in enumerate(user.findall('Stop')):
                    stops += str(i + 1) + ' - ' + ''.join(stop.get('name')) + '\n'
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                buttons = [(types.InlineKeyboardButton(text='Выбрать остановку🚏✅', callback_data='button_select')),
                           (types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='button_add'))]
                keyboard.add(buttons[0], buttons[1])
                bot.send_message(message.from_user.id, f'Ваши остановки:\n{stops}', reply_markup=keyboard)
            elif user.find('Stop').get('name') is None:
                keyboard = types.InlineKeyboardMarkup(row_width=1)
                button = types.InlineKeyboardButton(text='Добавить остановку🚏➕', callback_data='button_add')
                keyboard.add(button)
                bot.send_message(message.from_user.id, 'У вас нет отслеживаемых остановок', reply_markup=keyboard)
    if s == 0:  # если юзера нет
        user = ElementTree.SubElement(user_list, 'User', id=str(message.from_user.id))
        stop = ElementTree.SubElement(user, 'Stop')
        bus = ElementTree.SubElement(stop, 'Bus')
        time_before_arrival = ElementTree.SubElement(bus, 'time_before_arrival')
        time_interval = ElementTree.SubElement(bus, 'time_interval')
        tree.write('users.xml')
        start(message)


# @bot.callback_query_handlers(func=lambda callback: callback.data)
# def callback_button(callback):
#     if callback == 'button_add':
#         bot.send_message(callback.from_user.id, 'У вас нет отслеживаемых остановок')


bot.infinity_polling()
