import telebot
import time
import threading
import re
from datetime import datetime

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8721233798:AAFCqgy_TqwJ6snKMph20ea9jhwoLRo417Y"
YOUR_USER_ID = 5603035274
# ====================

bot = telebot.TeleBot(BOT_TOKEN)

# Словарь для хранения активных таймеров
timers = {}

# Регулярка для вариаций слова "кот"
COT_VARIANTS = re.compile(
    r'(?:'
    r'кот|котик|котейка|котище|котишко|котёнок|котенок|'
    r'котэ|коте|коть|котикей|котан|котич|котяра|котюня|'
    r'котакбас|котофей|котопес|котоматрица|котополитен|'
    r'котя|котёныш|котяшка|котопёс|котишко|коточка|'
    r'котобой|котовод|котоша|котосыч|котобаза|'
    r'cat|cats|kitty|kitten|cattie|catto|'
    r'мурзик|барсик|васька|рыжик|пушистик|хвостатый'
    r')',
    re.IGNORECASE
)

def contains_cot_variant(text):
    """Проверяет, содержит ли текст вариацию слова 'кот'"""
    return bool(COT_VARIANTS.search(text))

def is_owner_mentioned(text):
    """Проверяет упоминание @qwerty0379"""
    return '@qwerty0379' in text.lower()

def is_owner_mentioned_in_message(message):
    """Проверяет упоминание владельца через reply"""
    if message.text and '@qwerty0379' in message.text.lower():
        return True
    if message.reply_to_message and message.reply_to_message.from_user.id == YOUR_USER_ID:
        return True
    return False

def get_reply_message(is_night):
    """Возвращает сообщение для автоответа в зависимости от времени суток"""
    if is_night:
        return "🤖 *Б.А.С.И.К.*: В данный момент мой создатель предположительно спит, прошу вас подождать до утра.\n\n🌙 Спокойной ночи!"
    else:
        return "🤖 *Б.А.С.И.К.*: В данный момент мой создатель находится вне сети, прошу вас подождать.\n\n☀️ Хорошего дня!"

def auto_reply(chat_id, message_id, user_name, original_text):
    """Функция автоответа, запускается через задержку"""
    now = datetime.now()
    is_night = now.hour >= 22 or now.hour < 8
    delay = 300 if is_night else 600  # 5 мин ночью, 10 мин днём
    
    period = "ночь (5 мин)" if is_night else "день (10 мин)"
    print(f"⏳ Таймер: жду {delay} секунд ({period})...")
    time.sleep(delay)
    
    key = (chat_id, message_id)
    if not timers.get(key, False):
        print(f"⏸️ Таймер отменен (владелец ответил)")
        return
    
    reply_text = get_reply_message(is_night)
    try:
        bot.send_message(chat_id, reply_text, reply_to_message_id=message_id, parse_mode="Markdown")
        print(f"✅ Автоответ отправлен для сообщения {message_id}")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
    
    timers.pop(key, None)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Игнорируем сообщения от самого бота
    if message.from_user.id == bot.get_me().id:
        return
    
    chat_id = message.chat.id
    message_id = message.message_id
    user_id = message.from_user.id
    user_name = message.from_user.username or message.from_user.first_name
    text = message.text.lower() if message.text else ""
    
    # Проверяем триггеры
    is_cot = contains_cot_variant(text)
    is_mention = is_owner_mentioned(text) or is_owner_mentioned_in_message(message)
    is_triggered = is_cot or is_mention
    
    # Если триггер сработал и это не владелец
    if is_triggered and user_id != YOUR_USER_ID:
        key = (chat_id, message_id)
        timers[key] = True
        
        timer_thread = threading.Thread(
            target=auto_reply,
            args=(chat_id, message_id, user_name, message.text),
            daemon=True
        )
        timer_thread.start()
        
        trigger_type = "кот" if is_cot else "упоминание"
        print(f"⏰ СОЗДАН ТАЙМЕР для @{user_name} [{trigger_type}]: {message.text[:50]}")
    
    # Если ответил ВЫ — отменяем все таймеры в этом чате
    if user_id == YOUR_USER_ID:
        keys_to_remove = [k for k in timers.keys() if k[0] == chat_id]
        for key in keys_to_remove:
            timers[key] = False
            timers.pop(key, None)
        if keys_to_remove:
            print(f"🗑️ Отменено {len(keys_to_remove)} таймеров")

print("=" * 60)
print("🤖 БОТ-АВТООТВЕТЧИК ЗАПУЩЕН")
print("=" * 60)
print(f"📌 Ваш ID: {YOUR_USER_ID}")
print("📋 ФУНКЦИИ:")
print("   • 'кот' или @qwerty0379 -> автоответ через 10/5 мин")
print("   • Вы отвечаете -> таймер отменяется")
print("=" * 60)

bot.infinity_polling()
