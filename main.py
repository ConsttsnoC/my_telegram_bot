#модуль для открытия вебэстраницы
import webbrowser
import sqlite3
import telebot
import config
import requests
import json
from translations import WEATHER_TRANSLATIONS
from telebot import types

amount = 0
#Api для подключения бота
bot = telebot.TeleBot(config.TOKEN)
opi = config.OPI
api = config.API_KEY


#декоратор для команды start
@bot.message_handler(commands=['start'])
#message будет хранить в себе информацию про пользователя и чат
def start(message):
    #ответ на команду #start
    conn = sqlite3.connect('peopl.sql')
    cur = conn.cursor()
    #создаем таблицу users в бд
    cur.execute('CREATE TABLE IF NOT EXISTS users (id int auto_increment primary key, name varchar(50), pass varchar(50))')
    user(message)  # добавить данные пользователя в базу данных
    conn.commit()
    cur.close()
    conn.close()
    #выводим приветсвенное сообщение пользователю, либо имя, любо имя и фамлия
    if message.from_user.first_name and message.from_user.last_name:
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name} {message.from_user.last_name}!')
    elif message.from_user.first_name:
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!')

#проеряем что пользователя нет в бд, и добавляем, а если есть, то не добавляем
def user(message):
    conn = sqlite3.connect('peopl.sql')
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE pass = ?", (message.from_user.id,))
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute("INSERT INTO users (name, pass) VALUES (?, ?)", (message.from_user.first_name, message.from_user.id))
        conn.commit()
    cur.close()
    conn.close()
# обработчик комманды users, выдает сообщением список всех пользователей записанных в бд
@bot.message_handler(commands=['users'])
def get_users(message):
    conn = sqlite3.connect('peopl.sql')
    cur = conn.cursor()
    cur.execute("SELECT name, pass FROM users")
    rows = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    users_list = ""
    for row in rows:
        users_list += f"{row[0]} - {row[1]}\n"
    bot.send_message(message.chat.id, users_list)

#обработчик команды перехода на github
@bot.message_handler(commands=['github'])
def github(message):
    webbrowser.open('https://github.com/ConsttsnoC?tab=repositories')
#обработчик команды перехода на site
@bot.message_handler(commands=['site'])
def site(message):
    webbrowser.open('https://www.gilmanov.net/')

@bot.message_handler(commands=['converter'])
def converter(message):
    bot.send_message(message.chat.id, 'Введите сумму')
    bot.register_next_step_handler(message, summa)

def summa(message):
    global amount
    try:
        amount = int(message.text.strip())

        if amount <= 0:
            raise ValueError("Сумма должна быть положительным числом")

        bot.send_message(message.chat.id, f"Вы указали сумму {amount} рублей. Теперь выберите пару валют:")

        mark = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton('RUB/TL', callback_data='TRY')
        btn2 = types.InlineKeyboardButton('RUB/USD', callback_data='USD')
        btn3 = types.InlineKeyboardButton('RUB/EUR', callback_data='EUR')

        mark.add(btn1,btn2,btn3)
        bot.send_message(message.chat.id, 'Выберите пару валют', reply_markup=mark)

    except ValueError:
        bot.send_message(message.chat.id, "Ошибка: введенное значение не является положительным числом.")
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка: {}".format(str(e)))



@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        # получаем значение валюты из callback_data
        currency = call.data

        api_url = f"https://api.apilayer.com/exchangerates_data/convert?from=RUB&to={currency}&amount={amount}&apikey={api}"
        response = requests.get(api_url)
        result = response.json()['result']
        bot.answer_callback_query(callback_query_id=call.id, text=f"{amount} рублей = {result} {currency}")
        bot.send_message(call.message.chat.id, f"{amount} рублей = {result} {currency}")
    except Exception as e:
        bot.send_message(call.message.chat.id, "Произошла ошибка: {}".format(str(e)))





@bot.message_handler(commands=['weather'])
def weather(message):
    bot.send_message(message.chat.id, 'Напишите название города')
    bot.register_next_step_handler(message, get_weather)

def get_weather(message):
    city = message.text.strip().lower()
    res = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={opi}&units=metric')
    if res.status_code == 200:
        data = json.loads(res.text)
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        translated_description = WEATHER_TRANSLATIONS.get(description, description)
        message_text = f'Сейчас погода в городе {city.capitalize()}:\n\n{translated_description}, температура {temp:.1f}°C'
        bot.reply_to(message, message_text)
    else:
        bot.reply_to(message, 'Не удалось получить данные о погоде для данного города')


@bot.message_handler(commands=['id'])
    #message будет хранить в себе информацию про пользователя и чат
def id(message):
    #ответ на команду #help, третим аргументом передается параметр для форматирования строки в теги html
    bot.reply_to(message, f'ID: {message.from_user.id}')


bot.polling(none_stop=True)