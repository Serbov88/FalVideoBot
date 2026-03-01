import os
import telebot
import fal_client
import time
import logging
import requests

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
FAL_KEY = os.environ.get('FAL_KEY')

if not BOT_TOKEN or not FAL_KEY:
    raise ValueError("❌ Нет токенов! Добавь BOT_TOKEN и FAL_KEY в переменные окружения")

os.environ['FAL_KEY'] = FAL_KEY
bot = telebot.TeleBot(BOT_TOKEN)

# ========== КОМАНДА START ==========
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
        "👋 Привет! Я бот для видео через FAL AI!\n\n"
        "📸 Отправь фото — я оживлю его через Kling\n"
        "🎬 /video текст — видео из текста\n"
        "💬 Просто напиши — отвечу (скоро)"
    )

# ========== ВИДЕО ИЗ ТЕКСТА ==========
@bot.message_handler(commands=['video'])
def generate_video(message):
    prompt = message.text.replace('/video', '').strip()
    if not prompt:
        bot.reply_to(message, "❌ Напиши запрос после /video, например: /video робот танцует")
        return
    
    msg = bot.reply_to(message, "🎥 Генерирую видео из текста через Kling... (до 60 секунд)")
    
    try:
        # Отправляем задачу в Kling (text-to-video)
        handler = fal_client.submit(
            "fal-ai/kling-video/v1.6/text-to-video",
            arguments={
                "prompt": prompt
            }
        )
        
        # Ждём результат
        result = handler.get()
        
        bot.delete_message(message.chat.id, msg.message_id)
        
        if result and result.get('video'):
            bot.send_message(message.chat.id, f"✅ Видео готово!\n{result['video']['url']}")
        else:
            bot.send_message(message.chat.id, "❌ Не удалось получить видео")
            
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {str(e)}", message.chat.id, msg.message_id)

# ========== ОЖИВЛЕНИЕ ФОТО ==========
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    msg = bot.reply_to(message, "🎬 Оживляю фото через Kling... (до 60 секунд)")
    
    try:
        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        photo = bot.download_file(file_info.file_path)
        
        # Сохраняем временно
        with open('photo.jpg', 'wb') as f:
            f.write(photo)
        
        # Загружаем фото на временный хостинг (нужен будет ImgBB или аналогичный)
        # Пока используем простой вариант
        with open('photo.jpg', 'rb') as f:
            response = requests.post(
                "https://api.imgbb.com/1/upload",
                params={"key": os.environ.get('IMGBB_KEY', '')},  # нужен ключ ImgBB
                files={"image": f}
            )
        
        os.remove('photo.jpg')
        
        if response.status_code == 200:
            image_url = response.json()['data']['url']
            
            # Отправляем в Kling (image-to-video)
            handler = fal_client.submit(
                "fal-ai/kling-video/v1.6/image-to-video",
                arguments={
                    "image_url": image_url,
                    "prompt": "make it move naturally"
                }
            )
            
            result = handler.get()
            
            bot.delete_message(message.chat.id, msg.message_id)
            
            if result and result.get('video'):
                bot.send_message(message.chat.id, f"✅ Фото ожило!\n{result['video']['url']}")
            else:
                bot.send_message(message.chat.id, "❌ Не удалось получить видео")
        else:
            bot.edit_message_text("❌ Ошибка загрузки фото", message.chat.id, msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {str(e)}", message.chat.id, msg.message_id)

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("🚀 Бот с FAL AI запускается...")
    print(f"🤖 Bot Token: {'✅' if BOT_TOKEN else '❌'}")
    print(f"🔄 FAL Key: {'✅' if FAL_KEY else '❌'}")
    
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(5)
