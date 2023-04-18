#модуль для открытия вебэстраницы
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
    conn = sqlite3.connect('people.sql')
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS users (id int auto_increment primary key, name varchar(50), pass varchar(50))')
    conn.commit()
    cur.close()
    conn.close()
    if message.from_user.first_name and message.from_user.last_name: #если у пользователя есть имя и фамилия, то выводим
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name} {message.from_user.last_name}!')
    elif message.from_user.first_name:#если у пользователя нет фамилии, то выводим только имя
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!')


def user(message):
    conn = sqlite3.connect('people.sql')
    cur = conn.cursor()
    cur.execute('INSERT INTO users (name, pass) VALUES ({message.from_user.first_name},{message.from_user.id})')
    conn.commit()
    cur.close()
    conn.close()


@bot.message_handler(commands=['github'])
def github(message):
    webbrowser.open('https://github.com/ConsttsnoC?tab=repositories')

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