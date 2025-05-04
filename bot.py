import os
import telebot
from telebot import types
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv("TOKEN"))

#работа с нейросетью
isNeuro = False
is_processing = False

API_KEY = os.getenv("API_DEEPSEEK")
MODEL = "deepseek/deepseek-r1:free"

def process_content(content):
    return content.replace('<think>', '').replace('</think>', '')

def chat_completion(prompt, chat_id, message):
    global is_processing

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    system_message = {
        "role": "system",
        "content": "Ты - опытный и эмпатичный психолог. Ты помогаешь пользователям разобраться в их проблемах, даешь советы и поддерживаешь их. Твоя цель - предоставить полезные и конструктивные ответы, основанные на принципах психологии." 
    }
    
    data = {
        "model": MODEL,
        "messages": 
        [
            system_message,
            {"role": "user", "content": prompt},
        ],
        "stream": False
    }

    
    max_attempts = 4  # Максимальное количество попыток (опционально)
    attempt = 0

    while True:  # Бесконечный цикл
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            )

            response.raise_for_status()  # Проверяем статус ответа

            response_json = response.json()  # Парсим JSON

            if "choices" in response_json and len(response_json["choices"]) > 0:
                full_content = response_json["choices"][0]["message"]["content"]
                cleaned_content = process_content(full_content)
                if cleaned_content:  # Проверяем, что ответ не пустой
                    bot.reply_to(message, cleaned_content)  # Отправляем полный ответ
                    return cleaned_content
                else:
                    attempt += 1
                    if attempt >= max_attempts:  # Если попытки исчерпаны
                        bot.send_message(chat_id, "Не удалось получить ответ от нейросети после нескольких попыток.")
                        return ""
                    time.sleep(1)  # Задержка перед повторной попыткой
            else:
                attempt += 1
                if attempt >= max_attempts:  # Если попытки исчерпаны
                    bot.send_message(chat_id, "Не удалось получить ответ от нейросети после нескольких попыток.")
                    return ""
                time.sleep(1)  # Задержка перед повторной попыткой

        except requests.exceptions.RequestException as e:
            bot.send_message(chat_id, f"Ошибка при подключении к API: {str(e)}")
            return ""
        except json.JSONDecodeError as e:
            bot.send_message(chat_id, f"Ошибка декодирования ответа от нейросети: {str(e)}")
            return ""
        except Exception as e:
            bot.send_message(chat_id, f"Произошла неизвестная ошибка: {str(e)}")
            return ""



# Обработчики текста
@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    item1 = types.KeyboardButton("Нейропсихолог")
    item2 = types.KeyboardButton("Сайт психолога")
    item3 = types.KeyboardButton("Помощь")
    keyboard.add(item1, item2, item3)
    bot.send_message(message.chat.id, 'Привет! Я твой виртуальный помощник-психолог 🤍\nРад, что ты здесь! Я помогу тебе разобраться в сложных эмоциях, найти опору в трудный момент или просто выслушаю, если нужно выговориться.\nТы не один — я здесь, чтобы поддержать тебя. Просто выбирай нужный пункт, и мы начнем! 🌱\nP.S. Если заблудишься — всегда можно вернуться в меню или написать мне слово "Помощь".', reply_markup=keyboard)

@bot.message_handler(func=lambda message: True)
def on_click(message):
    global isNeuro, is_processing
    user_text = message.text

    if user_text == 'Сайт психолога':
        markup = types.InlineKeyboardMarkup()
        website_button = types.InlineKeyboardButton("Открыть веб-сайт:", url="https://www.bsuir.by/ru/spps")
        markup.add(website_button)
        bot.send_message(message.chat.id, "Нажмите кнопку ниже, чтобы открыть официальный сайт психолога БГУИРа:", reply_markup=markup)
    
    elif user_text == 'Нейропсихолог':
        isNeuro = True
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        stop_button = types.KeyboardButton("Остановить нейросеть")
        keyboard.add(stop_button)
        bot.send_message(message.chat.id, 'Теперь вы можете общаться с нашим нейро-психологом. Опишите подробно ему свою проблему. Чтобы выключить нейро-психолога, нажмите кнопку "Остановить нейросеть":', reply_markup=keyboard)
    
    elif user_text == 'Остановить нейросеть':
        isNeuro = False
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        item1 = types.KeyboardButton("Нейропсихолог")
        item2 = types.KeyboardButton("Сайт психолога")
        item3 = types.KeyboardButton("Помощь")
        keyboard.add(item1, item2, item3)
        bot.reply_to(message, 'Режим нейропсихолога выключен.\nЧтобы включить, нажмите соответствующую кнопку', reply_markup=keyboard)
    
    elif user_text == 'Помощь':
        bot.send_message(message.chat.id, '"Старт" - запуск бота,\n"Помощь" - все доступные команды,\n"Сайт психолога" - ссылка на официальный сайт психолога БГУИР,\n"Нейроспихолог" - наш нейроспихолог, работающий на базе DeepSeek R1 (для остановки нажмите кнопку "Остановить нейросеть")\n')
    
    elif isNeuro:
        if is_processing:
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(message.chat.id, "Нейросеть может обработать за раз только один запрос. Пожалуйста, подождите...")
        else:
            is_processing = True  # Устанавливаем флаг, что нейросеть занята
            bot.send_chat_action(message.chat.id, action="typing")
            chat_completion(user_text, message.chat.id, message)  # Вызываем нейросеть
            is_processing = False  # Сбрасываем флаг после завершения обработки
    
    else:
        bot.send_message(message.chat.id, 'Некорректный ввод. Используйте кнопки меню.')

#запуск бота   
if __name__ == "__main__":
    bot.remove_webhook()  # Удаляем возможные остатки вебхука
    time.sleep(1)         
    bot.polling(none_stop=True)