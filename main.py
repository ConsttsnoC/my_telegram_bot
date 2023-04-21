#модуль для открытия вебэстраницы
import webbrowser
import sqlite3

import openai
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
openai.api_key = config.openai.api_key


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
    # Создаем клавиатуру для выбора первой валюты
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(types.KeyboardButton('RUB'), types.KeyboardButton('USD'), types.KeyboardButton('EUR'),types.KeyboardButton('TRY'))
    bot.send_message(message.chat.id, "Выберите первую валюту, из которой будет произодиться конвертация", reply_markup=markup)
    bot.register_next_step_handler(message, select_first_currency)

def select_first_currency(message):
    try:
        # Получаем выбранную первую валюту и создаем клавиатуру для выбора второй валюты
        first_currency = message.text.strip().upper()
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add(types.KeyboardButton('RUB'), types.KeyboardButton('USD'), types.KeyboardButton('EUR'),types.KeyboardButton('TRY'))
        bot.send_message(message.chat.id, f"Выберите вторую валюту для конвертации из {first_currency}", reply_markup=markup)

        # Сохраняем выбранную первую валюту в глобальной переменной
        global currency_from
        currency_from = first_currency

        bot.register_next_step_handler(message, select_second_currency)

    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка: {}".format(str(e)))

def select_second_currency(message):
    try:
        # Получаем выбранную вторую валюту, создаем клавиатуру для ввода суммы и сохраняем выбранную вторую валюту
        second_currency = message.text.strip().upper()
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, f"Выбрана пара валют {currency_from}/{second_currency}. Введите сумму для конвертации", reply_markup=markup)
        global currency_to
        currency_to = second_currency
        bot.register_next_step_handler(message, convert)

    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка: {}".format(str(e)))

def convert(message):
    try:
        # Получаем введенную сумму, отправляем запрос к API и отправляем результат пользователю
        amount = float(message.text.strip())
        api_url = f"https://api.apilayer.com/exchangerates_data/convert?from={currency_from}&to={currency_to}&amount={amount}&apikey={api}"
        response = requests.get(api_url)
        result = response.json()['result']
        bot.send_message(message.chat.id, f"{amount} {currency_from} = {result} {currency_to}")
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка: введенное значение не является числом.")
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка: {}".format(str(e)))



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

# Обработчик команды /start_chatting, который отправляет приветственное сообщение
@bot.message_handler(commands=['start_chatting'])
#Функция start_chatting запускается, когда пользователь отправляет
def start_chatting(message):
    # Отправляем приветственное сообщение
    bot.send_message(message.chat.id, "Привет! Я ИИ-ассистент, готов общаться с вами. Что вы хотите спросить?")
# Функция, использующая API OpenAI для генерации ответа на входящее сообщение
def generate_openai_response(input_text):
    # Создание запроса к API OpenAI с использованием заданных параметров
    response = openai.Completion.create(
        engine="text-davinci-002", # Задаем используемую модель для обработки естественного языка
        prompt=f"{input_text} Ответьте на русском языке.",# Указываем начальный текст для запроса и требуем, чтобы ответ был на русском языке
        max_tokens=500,# Указываем максимальное количество токенов, которые могут быть сгенерированы
        n=1,# Указываем количество вариантов ответа, которые должны быть сгенерированы
        stop=None,# Указываем, что не требуется остановка генерации в определенном месте
        temperature=0.5,# Указываем температуру, которая контролирует вероятность выбора наиболее вероятного следующего токена
    )
    # Извлечение сгенерированного ответа из ответа API OpenAI
    message = response.choices[0].text.strip()
    # Возврат сгенерированного текста ответа
    return message

bot.polling(none_stop=True)