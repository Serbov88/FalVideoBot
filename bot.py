import os
import telebot
import fal_client
import time
import logging

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
FAL_KEY = os.environ.get('FAL_KEY')

if not BOT_TOKEN or not FAL_KEY:
    raise ValueError("❌ Нет токенов! Добавь BOT_TOKEN и FAL_KEY в переменные окружения")

os.environ['FAL_KEY'] = FAL_KEY
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
        "👋 Привет! Я бот для видео через FAL AI!\n\n"
        "📸 Отправь фото — я оживлю его (Kling)\n"
        "🎬 /video текст — видео из текста"
    )

@bot.message_handler(commands=['video'])
def generate_video(message):
    prompt = message.text.replace('/video', '').strip()
    if not prompt:
        bot.reply_to(message, "❌ Напиши запрос после /video")
        return
    
    msg = bot.reply_to(message, "🎥 Генерирую видео...")
    try:
        # Здесь будет код для генерации видео из текста
        bot.edit_message_text("✅ Видео готово! (ссылка)", message.chat.id, msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {str(e)}", message.chat.id, msg.message_id)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    msg = bot.reply_to(message, "🎬 Оживляю фото через Kling...")
    
    try:
        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        photo = bot.download_file(file_info.file_path)
        
        # Здесь будет код отправки в FAL AI
        
        bot.edit_message_text("✅ Видео готово! (ссылка)", message.chat.id, msg.message_id)
        
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {str(e)}", message.chat.id, msg.message_id)

if __name__ == "__main__":
    print("🚀 Бот с FAL AI запускается...")
    bot.infinity_polling()
