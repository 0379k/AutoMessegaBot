import telebot
import time
import threading
import re
from datetime import datetime
import schedule

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8721233798:AAFCqgy_TqwJ6snKMph20ea9jhwoLRo417Y"
YOUR_USER_ID = 5603035274
CHAT_ID = -1001234567890  # ЗАМЕНИТЕ на ID вашей группы!
# ====================

bot = telebot.TeleBot(BOT_TOKEN)
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
    return bool(COT_VARIANTS.search(text))

def is_owner_mentioned(text):
    return '@qwerty0379' in text.lower()

def is_owner_mentioned_in_message(message):
    if message.text and '@qwerty0379' in message.text.lower():
        return True
    if message.reply_to_message and message.reply_to_message.from_user.id == YOUR_USER_ID:
        return True
    return False

def get_reply_message(is_night):
    """Возвращает сообщение для автоответа (ночь с 23:00 до 08:00)"""
    if is_night:
        return "🤖 *Б.А.С.И.К.*: В данный момент мой создатель предположительно спит, прошу вас подождать до утра.\n\n🌙 Спокойной ночи!"
    else:
        return "🤖 *Б.А.С.И.К.*: В данный момент мой создатель находится вне сети, прошу вас подождать.\n\n☀️ Хорошего дня!"

def auto_reply(chat_id, message_id, user_name, original_text):
    """Автоответчик"""
    now = datetime.now()
    # Ночь с 23:00 до 08:00
    is_night = now.hour >= 23 or now.hour < 8
    delay = 300 if is_night else 600  # 5 мин ночью, 10 мин днём
    
    print(f"⏳ Таймер: жду {delay} секунд...")
    time.sleep(delay)
    
    key = (chat_id, message_id)
    if not timers.get(key, False):
        print(f"⏸️ Таймер отменен")
        return
    
    reply_text = get_reply_message(is_night)
    try:
        bot.send_message(chat_id, reply_text, reply_to_message_id=message_id, parse_mode="Markdown")
        print(f"✅ Автоответ отправлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    timers.pop(key, None)

# ===== ФУНКЦИИ ДЛЯ ЕЖЕДНЕВНЫХ УВЕДОМЛЕНИЙ =====
def morning_greeting():
    """Отправляет утреннее приветствие в 08:00"""
    try:
        bot.send_message(CHAT_ID, "🌅 *Б.А.С.И.К.*: Доброе утро! Желаю всем продуктивного дня! ☀️", parse_mode="Markdown")
        print("✅ Отправлено утреннее приветствие")
    except Exception as e:
        print(f"❌ Ошибка утреннего приветствия: {e}")

def night_greeting():
    """Отправляет вечернее приветствие в 23:59"""
    try:
        bot.send_message(CHAT_ID, "🌙 *Б.А.С.И.К.*: Спокойной ночи! Приятных снов и до завтра! 😴", parse_mode="Markdown")
        print("✅ Отправлено вечернее приветствие")
    except Exception as e:
        print(f"❌ Ошибка вечернего приветствия: {e}")

def run_scheduler():
    """Запускает планировщик в отдельном потоке"""
    # Настройка расписания
    schedule.every().day.at("08:00").do(morning_greeting)
    schedule.every().day.at("23:59").do(night_greeting)
    
    print("📅 Планировщик запущен: утренние и вечерние приветствия активны")
    
    while True:
        schedule.run_pending()
        time.sleep(30)  # Проверяем каждые 30 секунд

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Игнорируем сообщения от бота
    if message.from_user.id == bot.get_me().id:
        return
    
    chat_id = message.chat.id
    message_id = message.message_id
    user_id = message.from_user.id
    user_name = message.from_user.username or message.from_user.first_name
    text = message.text.lower() if message.text else ""
    
    # Проверка триггеров
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
        print(f"⏰ СОЗДАН ТАЙМЕР для @{user_name} [{trigger_type}]")
    
    # Если ответил ВЫ — отменяем таймеры
    if user_id == YOUR_USER_ID:
        keys_to_remove = [k for k in timers.keys() if k[0] == chat_id]
        for key in keys_to_remove:
            timers[key] = False
            timers.pop(key, None)
        if keys_to_remove:
            print(f"🗑️ Отменено {len(keys_to_remove)} таймеров")

# ===== ЗАПУСК =====
print("=" * 60)
print("🤖 БОТ-АВТООТВЕТЧИК ЗАПУЩЕН")
print("=" * 60)
print(f"📌 Ваш ID: {YOUR_USER_ID}")
print(f"📌 ID группы: {CHAT_ID}")
print("📋 ФУНКЦИИ:")
print("   • 'кот' или @qwerty0379 -> автоответ через 10/5 мин")
print("   • Ночной режим: 23:00 - 08:00 (ожидание 5 мин)")
print("   • Дневной режим: 08:00 - 23:00 (ожидание 10 мин)")
print("   • Ежедневно: 08:00 - утреннее приветствие")
print("   • Ежедневно: 23:59 - вечернее приветствие")
print("=" * 60)

# Запускаем планировщик в фоновом потоке
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

# Запускаем бота
bot.infinity_polling()
