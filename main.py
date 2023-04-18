#модуль для открытия вебэстраницы
import weather
import webbrowser
import telebot
import sqlite3
import config
from telebot import types

#Api для подключения бота
bot = telebot.TeleBot(config.TOKEN)

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

@bot.message_handler(commands=['weather'])
def get_weather(message):
    weather.weather(message)


#обработчик команды перехода на github
@bot.message_handler(commands=['github'])
def github(message):
    webbrowser.open('https://github.com/ConsttsnoC?tab=repositories')
#обработчик команды перехода на site
@bot.message_handler(commands=['site'])
def site(message):
    webbrowser.open('https://www.gilmanov.net/')



@bot.message_handler(commands=['help'])
    #message будет хранить в себе информацию про пользователя и чат
def main(message):
    #ответ на команду #help, третим аргументом передается параметр для форматирования строки в теги html
    bot.send_message(message.chat.id, '<b>help</b> <em>information</em>',parse_mode='html')


#декоратор для обработки прямых сообщений пользователя
@bot.message_handler()
#message будет хранить в себе информацию про пользователя и чат
def info(message):
    #получаем информацию, что именно пользователь прислал и приводим к нижнему регистру
    if message.text.lower() == 'привет':
        if message.from_user.first_name and message.from_user.last_name: # если у пользователя есть имя и фамилия, то выводим
            bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name} {message.from_user.last_name}!')
        elif message.from_user.first_name: #если у пользователя нет фамилии, то выводим только имя
            bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!')
    elif message.text.lower() == 'id':
            #ответ на предыдущее сообщение
        bot.reply_to(message, f'ID: {message.from_user.id}')




#чтобы бот работал постоянно
bot.polling(non_stop=True)