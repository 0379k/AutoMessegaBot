import telebot
import time
import threading
import re
from datetime import datetime

BOT_TOKEN = "8721233798:AAFCqgy_TqwJ6snKMph20ea9jhwoLRo417Y"
YOUR_USER_ID = 5603035274

bot = telebot.TeleBot(BOT_TOKEN)
timers = {}

COT_VARIANTS = re.compile(r'(кот|котик|котейка|котакбас|cat|kitty)', re.IGNORECASE)

def contains_cot_variant(text):
    return bool(COT_VARIANTS.search(text))

def is_owner_mentioned(text):
    return '@qwerty0379' in text.lower()

def auto_reply(chat_id, message_id, user_name, original_text):
    now = datetime.now()
    is_night = now.hour >= 22 or now.hour < 8
    delay = 300 if is_night else 600
    
    print(f"⏳ Жду {delay} сек...")
    time.sleep(delay)
    
    key = (chat_id, message_id)
    if not timers.get(key, False):
        return
    
    if is_night:
        reply = "🤖 Б.А.С.И.К.: Создатель спит, ждите до утра. 🌙"
    else:
        reply = "🤖 Б.А.С.И.К.: Создатель вне сети, подождите. ☀️"
    
    bot.send_message(chat_id, reply, reply_to_message_id=message_id)
    timers.pop(key, None)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.from_user.id == bot.get_me().id:
        return
    
    text = message.text.lower() if message.text else ""
    is_triggered = contains_cot_variant(text) or is_owner_mentioned(text)
    
    if is_triggered and message.from_user.id != YOUR_USER_ID:
        key = (message.chat.id, message.message_id)
        timers[key] = True
        
        threading.Thread(
            target=auto_reply,
            args=(message.chat.id, message.message_id, message.from_user.username, message.text),
            daemon=True
        ).start()
        print(f"⏰ Таймер запущен")
    
    if message.from_user.id == YOUR_USER_ID:
        keys = [k for k in timers.keys() if k[0] == message.chat.id]
        for k in keys:
            timers[k] = False
            timers.pop(k, None)
        if keys:
            print(f"🗑️ Отменено {len(keys)} таймеров")

print("🤖 БОТ ЗАПУЩЕН (упрощённая версия)")
bot.infinity_polling()
