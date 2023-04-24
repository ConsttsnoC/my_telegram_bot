# модуль для открытия вебэстраницы
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
# Api для подключения бота
bot = telebot.TeleBot(config.TOKEN)
opi = config.OPI
api = config.API_KEY
openai.api_key = config.openai.api_key


# декоратор для команды start
@bot.message_handler(commands=['start'])
# message будет хранить в себе информацию про пользователя и чат
def start(message):
    # ответ на команду #start
    conn = sqlite3.connect('peopl.sql')
    cur = conn.cursor()
    # создаем таблицу users в бд
    cur.execute(
        'CREATE TABLE IF NOT EXISTS users (id int auto_increment primary key, name varchar(50), pass varchar(50))')
    user(message)  # добавить данные пользователя в базу данных
    conn.commit()
    cur.close()
    conn.close()
    # выводим приветсвенное сообщение пользователю, либо имя, любо имя и фамлия
    if message.from_user.first_name and message.from_user.last_name:
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name} {message.from_user.last_name}!')
    elif message.from_user.first_name:
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!')


# проеряем что пользователя нет в бд, и добавляем, а если есть, то не добавляем
def user(message):
    conn = sqlite3.connect('peopl.sql')
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE pass = ?", (message.from_user.id,))
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute("INSERT INTO users (name, pass) VALUES (?, ?)",
                    (message.from_user.first_name, message.from_user.id))
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


# обработчик команды перехода на github
@bot.message_handler(commands=['github'])
def github(message):
    webbrowser.open('https://github.com/ConsttsnoC?tab=repositories')


# обработчик команды перехода на site
@bot.message_handler(commands=['site'])
def site(message):
    webbrowser.open('https://www.gilmanov.net/')


# Обработчик команды "converter"
@bot.message_handler(commands=['converter'])
def converter(message):
    # Создаем клавиатуру для выбора первой валюты
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True) # создание объекта клавиатуры с 2 столбцами
    markup.add(types.KeyboardButton('RUB'), types.KeyboardButton('USD'), types.KeyboardButton('EUR'),
               types.KeyboardButton('TRY')) # добавление кнопок на клавиатуру
    bot.send_message(message.chat.id, "Выберите первую валюту, из которой будет произодиться конвертация",
                     reply_markup=markup) # отправка сообщения и клавиатуры пользователю
    bot.register_next_step_handler(message, select_first_currency) # регистрация следующего шага, функции select_first_currency



def select_first_currency(message):
    try:
        # Получаем выбранную первую валюту из текста сообщения и создаем клавиатуру выбора второй валюты
        first_currency = message.text.strip().upper()
        markup = types.ReplyKeyboardMarkup(row_width=2,
                                           resize_keyboard=True)  # создаем клавиатуру с двумя кнопками в строке и возможностью изменения размера
        markup.add(types.KeyboardButton('RUB'), types.KeyboardButton('USD'), types.KeyboardButton('EUR'),
                   # добавляем кнопки выбора валют
                   types.KeyboardButton('TRY'))
        bot.send_message(message.chat.id, f"Выберите вторую валюту для конвертации из {first_currency}",
                         # отправляем сообщение с просьбой выбрать вторую валюту
                         reply_markup=markup)

        # Сохраняем выбранную первую валюту в глобальной переменной
        global currency_from
        currency_from = first_currency

        # Регистрируем обработчик следующего шага (выбора второй валюты)
        bot.register_next_step_handler(message, select_second_currency)

    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка: {}".format(str(e)))


def select_second_currency(message):
    try:
        # Получаем выбранную вторую валюту из текста сообщения, удаляем пробелы и делаем буквы заглавными
        second_currency = message.text.strip().upper()

        # Создаем клавиатуру для ввода суммы и убираем клавиатуру выбора валют
        markup = types.ReplyKeyboardRemove()

        # Отправляем сообщение с выбранной парой валют и просим пользователя ввести сумму для конвертации
        bot.send_message(message.chat.id,
                         f"Выбрана пара валют {currency_from}/{second_currency}. Введите сумму для конвертации",
                         reply_markup=markup)

        # Сохраняем выбранную вторую валюту в глобальной переменной
        global currency_to
        currency_to = second_currency

        # Регистрируем обработчик следующего шага (ввода суммы для конвертации) с помощью функции "convert"
        bot.register_next_step_handler(message, convert)

    # Если возникла ошибка, отправляем сообщение с текстом ошибки
    except Exception as e:
        bot.send_message(message.chat.id, "Произошла ошибка: {}".format(str(e)))


def convert(message):
    # Функция-обработчик для конвертации валют

    try:
        # Получаем введенную сумму
        amount = float(message.text.strip())

        # Формируем URL запроса к API и отправляем его
        api_url = f"https://api.apilayer.com/exchangerates_data/convert?from={currency_from}&to={currency_to}&amount={amount}&apikey={api}"
        response = requests.get(api_url)

        # Получаем результат из ответа API и отправляем его пользователю
        result = response.json()['result']
        bot.send_message(message.chat.id, f"{amount} {currency_from} = {result} {currency_to}")
    except ValueError:
        # Если введенное значение не является числом, отправляем сообщение об ошибке
        bot.send_message(message.chat.id, "Ошибка: введенное значение не является числом.")
    except Exception as e:
        # Если происходит какая-то другая ошибка, отправляем сообщение об ошибке с описанием
        bot.send_message(message.chat.id, "Произошла ошибка: {}".format(str(e)))


@bot.message_handler(commands=['weather'])
def weather(message):
    # Функция-обработчик команды /weather

    # Отправляем пользователю сообщение с запросом названия города
    bot.send_message(message.chat.id, 'Напишите название города')
    # Регистрируем следующую функцию в качестве обработчика следующего сообщения от пользователя
    bot.register_next_step_handler(message, get_weather)


def get_weather(message):
    # Функция для получения погоды в заданном городе

    # Получаем название города из сообщения пользователя и приводим его к нижнему регистру
    city = message.text.strip().lower()
    # Отправляем GET-запрос к API погоды, передавая в нем название города и API-ключ
    res = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={opi}&units=metric')
    # Проверяем, что запрос успешен (код ответа 200)
    if res.status_code == 200:
        # Если запрос успешен, преобразуем ответ в объект JSON
        data = json.loads(res.text)
        # Извлекаем температуру и описание погоды из данных, полученных от API
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        # Переводим описание погоды на русский язык, используя словарь WEATHER_TRANSLATIONS
        translated_description = WEATHER_TRANSLATIONS.get(description, description)
        # Формируем сообщение с данными о погоде
        message_text = f'Сейчас погода в городе {city.capitalize()}:\n\n{translated_description}, температура {temp:.1f}°C'
        # Отправляем сообщение пользователю с данными о погоде
        bot.reply_to(message, message_text)
    else:
        # Если запрос неуспешен, отправляем пользователю сообщение об ошибке
        bot.reply_to(message, 'Не удалось получить данные о погоде для данного города')


@bot.message_handler(commands=['id'])
# message будет хранить в себе информацию про пользователя и чат
def id(message):
    # ответ на команду #help, третим аргументом передается параметр для форматирования строки в теги html
    bot.reply_to(message, f'ID: {message.from_user.id}')


# Обработчик команды /start_chatting, который отправляет приветственное сообщение
@bot.message_handler(commands=['start_chatting'])
# Функция start_chatting запускается, когда пользователь отправляет
def start_chatting(message):
    # Отправляем приветственное сообщение
    bot.send_message(message.chat.id, "Привет! Я ИИ-ассистент, готов общаться с вами. Что вы хотите спросить?")


# Функция, использующая API OpenAI для генерации ответа на входящее сообщение
def generate_openai_response(input_text):
    # Создание запроса к API OpenAI с использованием заданных параметров
    response = openai.Completion.create(
        engine="text-davinci-002",  # Задаем используемую модель для обработки естественного языка
        prompt=f"{input_text} Ответьте на русском языке.",
        # Указываем начальный текст для запроса и требуем, чтобы ответ был на русском языке
        max_tokens=500,  # Указываем максимальное количество токенов, которые могут быть сгенерированы
        n=1,  # Указываем количество вариантов ответа, которые должны быть сгенерированы
        stop=None,  # Указываем, что не требуется остановка генерации в определенном месте
        temperature=0.5,
        # Указываем температуру, которая контролирует вероятность выбора наиболее вероятного следующего токена
    )
    # Извлечение сгенерированного ответа из ответа API OpenAI
    message = response.choices[0].text.strip()
    # Возврат сгенерированного текста ответа
    return message


# Обработчик команды /add_word
@bot.message_handler(commands=['add_word'])
def add_word(message):
    # Подключаемся к базе данных
    conn = sqlite3.connect('peopl.sql')
    # создает объект-курсор, который используется для выполнения запросов к базе данных через соединение conn.
    # Курсор позволяет перебирать результаты запроса, а также вставлять, обновлять и удалять данные в базе данных.
    cur = conn.cursor()

    # Создаем таблицу слов для каждого пользователя, если она не существует
    cur.execute(
        "CREATE TABLE IF NOT EXISTS words (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, word_number INTEGER, english_word TEXT, russian_word TEXT)")

    # Запрашиваем у пользователя слово на английском языке
    user_id = message.chat.id
    bot.send_message(user_id, "Введите слово на английском языке:")

    # Регистрируем следующий шаг - обработчик add_english_word
    bot.register_next_step_handler(message, add_english_word)

    cur.close()
    conn.close()


def add_english_word(message):
    english_word = message.text  # сохраняем введенное пользователем слово на английском языке

    # Сохраняем слово на английском языке и запрашиваем перевод на русский язык
    conn = sqlite3.connect('peopl.sql')  # подключаемся к базе данных
    cur = conn.cursor()  # создаем курсор для работы с базой данных
    user_id = message.chat.id  # определяем идентификатор пользователя

    # Определяем порядковый номер слова пользователя
    cur.execute("SELECT MAX(word_number) FROM words WHERE user_id = ?", (user_id,))
    max_word_number = cur.fetchone()[0]
    word_number = 1 if max_word_number is None else max_word_number + 1  # Если пользователь еще не добавлял ни одного слова и максимальный номер слова max_word_number равен None, то порядковый номер нового слова будет равен 1.

    # Добавляем слово в таблицу words
    cur.execute("INSERT INTO words (user_id, word_number, english_word, russian_word) VALUES (?, ?, ?, ?)",
                (user_id, word_number, english_word, ""))
    conn.commit()  # сохраняем изменения в базе данных
    cur.close()  # закрываем курсор
    conn.close()  # закрываем соединение с базой данных

    bot.send_message(user_id,
                     f"Введите перевод слова '{english_word}' на русский язык:")  # отправляем сообщение пользователю, запрашивая перевод на русский язык
    bot.register_next_step_handler(message, add_russian_word,
                                   english_word)  # регистрируем обработчик следующего шага, который будет добавлять перевод слова на русский язык в базу данных


def add_english_word(message):
    # Извлекаем английское слово из сообщения пользователя
    english_word = message.text

    # Устанавливаем соединение с базой данных SQLite и создаем объект-курсор для выполнения SQL-запросов
    conn = sqlite3.connect('peopl.sql')
    cur = conn.cursor()  # создаем объект-курсор для выполнения SQL-запросов

    # Получаем идентификатор чата пользователя
    user_id = message.chat.id

    # Выполняем SQL-запрос на добавление слова в таблицу 'words' в базе данных
    cur.execute("INSERT INTO words (user_id, english_word, russian_word) VALUES (?, ?, ?)", (user_id, english_word, ""))

    # Сохраняем изменения в базе данных
    conn.commit()

    # Закрываем объект-курсор и соединение с базой данных
    cur.close()
    conn.close()

    # Отправляем пользователю сообщение с просьбой ввести перевод слова на русский язык
    bot.send_message(user_id, f"Введите перевод слова '{english_word}' на русский язык:")

    # Регистрируем обработчик следующего сообщения от пользователя с помощью функции add_russian_word
    # и передаем ей английское слово, которое нужно перевести на русский язык
    bot.register_next_step_handler(message, add_russian_word, english_word)


def add_russian_word(message, english_word):
    # Проверяем, было ли введено английское слово
    if not english_word:
        # Если не было, выводим сообщение об ошибке
        bot.send_message(message.chat.id, "Для добавления перевода сначала используйте команду /add_word")
        return

    # Получаем русский перевод из сообщения пользователя
    russian_word = message.text

    # Устанавливаем соединение с базой данных и создаем объект-курсор
    conn = sqlite3.connect('peopl.sql')
    cur = conn.cursor()

    # Получаем идентификатор пользователя
    user_id = message.chat.id

    # Обновляем русский перевод для данного английского слова
    cur.execute("UPDATE words SET russian_word = ? WHERE user_id = ? AND english_word = ?",
                (russian_word, user_id, english_word))

    # Сохраняем изменения и закрываем соединение с базой данных
    conn.commit()
    cur.close()
    conn.close()

    # Выводим сообщение о том, что слово было успешно добавлено
    bot.send_message(user_id, f"Слово '{english_word}' успешно добавлено с переводом '{russian_word}'!")


# Импортируем модуль для работы с базой данных SQLite
import sqlite3


# Определяем функцию обработчика сообщений бота
# Декоратор `commands=['get_words']` указывает на то, что функция будет обрабатывать сообщения, начинающиеся с команды '/get_words'
@bot.message_handler(commands=['get_words'])
def get_words(message):
    # Устанавливаем соединение с базой данных 'peopl.sql' (если её нет, то она будет создана)
    conn = sqlite3.connect('peopl.sql')
    # Создаем курсор, с помощью которого будем выполнять запросы к базе данных
    cur = conn.cursor()

    # Получаем идентификатор пользователя из сообщения
    user_id = message.chat.id

    # Выполняем запрос к базе данных на получение слов пользователя с указанным идентификатором
    cur.execute("SELECT english_word, russian_word FROM words WHERE user_id = ?", (user_id,))
    # Получаем все строки, соответствующие запросу
    rows = cur.fetchall()

    # Сохраняем изменения в базе данных
    conn.commit()
    # Закрываем курсор и соединение с базой данных
    cur.close()
    conn.close()

    # Формируем список слов для отправки пользователю
    words_list = ""
    # Используем цикл for для перебора всех строк, полученных из базы данных
    for i, row in enumerate(rows, 1):
        # Добавляем очередную строку в список слов с номером строки и английским и русским словом, разделенными дефисом
        words_list += f"{i}. {row[0]} - {row[1]}\n"

    # Отправляем список слов пользователю
    if words_list:
        bot.send_message(user_id, words_list)
    else:
        bot.send_message(user_id, "Список слов пуст")


@bot.message_handler(commands=['delete_word'])
def delete_word(message):
    # Обрабатываем команду /delete_word и запрашиваем у пользователя слово на русском языке, которое нужно удалить

    # Получаем идентификатор пользователя
    user_id = message.chat.id
    # Отправляем сообщение с запросом на ввод слова
    bot.send_message(user_id, "Введите слово на русском языке, которое нужно удалить:")
    # Регистрируем следующий обработчик сообщений, который будет вызван, когда пользователь введет слово
    bot.register_next_step_handler(message, delete_word_by_russian_step1)


def delete_word_by_russian_step1(message):
    # Проверяем, что пользователь ввел корректное слово на русском языке

    # Получаем введенное пользователем слово и убираем лишние пробелы
    russian_word = message.text.strip()
    # Проверяем, что слово состоит только из букв русского алфавита
    if not russian_word.isalpha() or not all('\u0400' <= c <= '\u04FF' for c in russian_word):
        # Если слово не соответствует требованиям, отправляем пользователю сообщение с просьбой ввести корректное слово
        bot.send_message(message.chat.id, "Некорректный ввод. Введите слово на русском языке:")
        # Регистрируем следующий обработчик сообщений, который будет вызван, когда пользователь введет слово
        bot.register_next_step_handler(message, delete_word_by_russian_step1)
        return

    # Подключаемся к базе данных и удаляем слово
    conn = sqlite3.connect('peopl.sql')
    cur = conn.cursor()
    cur.execute("DELETE FROM words WHERE user_id = ? AND russian_word = ?", (message.chat.id, russian_word))
    conn.commit()
    cur.close()
    conn.close()

    # Отправляем пользователю подтверждение удаления слова
    bot.send_message(message.chat.id, f"Слово '{russian_word}' удалено из словаря.")


bot.polling(none_stop=True)
