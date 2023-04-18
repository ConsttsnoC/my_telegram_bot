import telebot
import config
import requests
import json
from translations import WEATHER_TRANSLATIONS

#Api для подключения бота
bot = telebot.TeleBot(config.TOKEN)
opi = config.OPI

@bot.message_handler(commands=['weather'])
def weather(message):
    bot.send_message(message.chat.id, 'Напишите название города')



@bot.message_handler(content_types=['text'])
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

bot.polling()