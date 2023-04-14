import webbrowser

import telebot
#Api для подключения бота
bot = telebot.TeleBot('5953707821:AAEc55Jy2aBOIQcGiigohgVowMQk9tCvQkE')

@bot.message_handler(commands=['site','website'])
def site(message):
    webbrowser.open('https://www.gilmanov.net/')


#декоратор для команды start
@bot.message_handler(commands=['start'])
    #message будет хранить в себе информацию про пользователя и чат
def main(message):
    #ответ на команду #start
    if message.from_user.first_name and message.from_user.last_name: #если у пользователя есть имя и фамилия, то выводим
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name} {message.from_user.last_name}!')
    elif message.from_user.first_name:#если у пользователя нет фамилии, то выводим только имя
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!')



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