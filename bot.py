import os
import telebot
import fal_client
import time
import logging
import requests

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
FAL_KEY = os.environ.get('FAL_KEY')
IMGBB_KEY = os.environ.get('IMGBB_KEY')

if not BOT_TOKEN or not FAL_KEY:
    raise ValueError("❌ Нет токенов! Добавь BOT_TOKEN и FAL_KEY в переменные окружения")

os.environ['FAL_KEY'] = FAL_KEY
bot = telebot.TeleBot(BOT_TOKEN)

# ========== КОМАНДА START ==========
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, 
        "👋 Привет! Я бот для видео через FAL AI!\n\n"
        "📸 **Отправь фото** — я оживлю его через Kling\n"
        "🎬 **/video текст** — видео из текста"
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
            "fal-ai/kling-video/v1-6/text-to-video",
            arguments={
                "prompt": prompt
            }
        )
        
        # Ждём результат
        result = handler.get()
        
        bot.delete_message(message.chat.id, msg.message_id)
        
        if result and result.get('video'):
            video_url = result['video']['url']
            bot.send_message(message.chat.id, f"✅ Видео готово!\n{video_url}")
        else:
            bot.send_message(message.chat.id, "❌ Не удалось получить видео")
            
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка видео: {str(e)}", message.chat.id, msg.message_id)

# ========== ОЖИВЛЕНИЕ ФОТО ==========
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    msg = bot.reply_to(message, "🎬 Оживляю фото через Kling... (до 60 секунд)")
    
    try:
        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        photo = bot.download_file(file_info.file_path)
        
        # Сохраняем временно
        temp_filename = f"temp_{message.from_user.id}_{int(time.time())}.jpg"
        with open(temp_filename, 'wb') as f:
            f.write(photo)
        
        # Загружаем на ImgBB (нужен ключ)
        if not IMGBB_KEY:
            bot.edit_message_text("❌ Нет ключа ImgBB. Добавь IMGBB_KEY в переменные окружения", 
                                 message.chat.id, msg.message_id)
            os.remove(temp_filename)
            return
        
        with open(temp_filename, 'rb') as f:
            response = requests.post(
                "https://api.imgbb.com/1/upload",
                params={"key": IMGBB_KEY},
                files={"image": f}
            )
        
        # Удаляем временный файл
        os.remove(temp_filename)
        
        if response.status_code == 200:
            image_url = response.json()['data']['url']
            
            # Отправляем в Kling (image-to-video) с правильным путем
            handler = fal_client.submit(
                "fal-ai/kling-video/v1-6/image-to-video",
                arguments={
                    "image_url": image_url,
                    "prompt": "make it move naturally"
                }
            )
            
            result = handler.get()
            
            bot.delete_message(message.chat.id, msg.message_id)
            
            if result and result.get('video'):
                video_url = result['video']['url']
                bot.send_message(message.chat.id, f"✅ Фото ожило!\n{video_url}")
            else:
                bot.send_message(message.chat.id, "❌ Не удалось получить видео")
        else:
            bot.edit_message_text(f"❌ Ошибка загрузки фото: {response.status_code}", 
                                 message.chat.id, msg.message_id)
            
    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {str(e)}", message.chat.id, msg.message_id)
        # Пробуем удалить временный файл, если он остался
        try:
            os.remove(temp_filename)
        except:
            pass

# ========== ОБРАБОТКА ТЕКСТА ==========
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    bot.reply_to(message, "Отправь фото или используй /video текст")

# ========== ЗАПУСК ==========
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Бот с FAL AI запускается...")
    print(f"🤖 Bot Token: {'✅' if BOT_TOKEN else '❌'}")
    print(f"🔄 FAL Key: {'✅' if FAL_KEY else '❌'}")
    print(f"📸 ImgBB Key: {'✅' if IMGBB_KEY else '❌'}")
    print("=" * 50)
    
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(5)
