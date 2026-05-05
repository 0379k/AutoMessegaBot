import telebot
import time
import threading
import re
import pytz
from datetime import datetime


# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8721233798:AAFCqgy_TqwJ6snKMph20ea9jhwoLRo417Y"
YOUR_USER_ID = 5603035274
# ====================

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилища
timers = {}
pending_forward = {}

# Регулярка для вариаций "кот"
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
    if message.entities:
        for entity in message.entities:
            if entity.type == 'mention':
                mention = message.text[entity.offset:entity.offset + entity.length]
                if mention.lower() == '@qwerty0379':
                    return True
    return False

def get_reply_message(is_night):
    """Возвращает разные сообщения в зависимости от времени суток (МСК)"""
    if is_night:
        return "🤖 *Б.А.С.И.К.*: В данный момент мой создатель предположительно спит, прошу вас подождать до утра.\n\n🌙 Спокойной ночи!"
    else:
        return "🤖 *Б.А.С.И.К.*: В данный момент мой создатель находится вне сети, прошу вас подождать.\n\n☀️ Хорошего дня!"

def forward_to_owner(chat_id, message_id, user_name, user_id, original_text, chat_title):
    """Пересылает сообщение владельцу в личку"""
    try:
        # Экранируем спецсимволы в тексте
        safe_text = original_text.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')
        
        forward_text = (
            f"📨 *Вам не ответили на сообщение!*\n\n"
            f"👤 *От:* @{user_name}\n"
            f"💬 *Текст:* {safe_text}\n"
            f"📅 *Время:* {datetime.now(pytz.timezone('Europe/Moscow')).strftime('%d.%m.%Y %H:%M:%S')} МСК\n"
            f"🏠 *Группа:* {chat_title}"
        )
        bot.send_message(YOUR_USER_ID, forward_text, parse_mode="Markdown")
        bot.forward_message(YOUR_USER_ID, chat_id, message_id)
        print(f"📨 Переслано сообщение {message_id} от @{user_name}")
        return True
    except Exception as e:
        print(f"❌ Ошибка пересылки: {e}")
        # Пробуем отправить без форматирования
        try:
            bot.send_message(YOUR_USER_ID, f"Вам не ответили!\nОт: @{user_name}\nТекст: {original_text}\nГруппа: {chat_title}")
            bot.forward_message(YOUR_USER_ID, chat_id, message_id)
        except:
            pass
        return False

def auto_reply(chat_id, message_id, user_name, user_id, original_text, chat_title):
    """Функция, которая срабатывает ЧЕРЕЗ ЗАДЕРЖКУ"""
    # Определяем время по МСК
    msk_tz = pytz.timezone('Europe/Moscow')
    now_msk = datetime.now(msk_tz)
    is_night = now_msk.hour >= 22 or now_msk.hour < 8
    
    if is_night:
        delay = 300  # 5 минут
        period = "ночь (5 мин)"
    else:
        delay = 600  # 10 минут
        period = "день (10 мин)"
    
    print(f"⏳ Таймер запущен: жду {delay} секунд ({period} по МСК)...")
    
    # Ждем
    time.sleep(delay)
    
    # Проверяем, не отменили ли таймер
    key = (chat_id, message_id)
    if timers.get(key, False) is False:
        print(f"⏸️ Таймер отменен (владелец ответил)")
        return
    
    # Отправляем автоответ в чат (только одна фраза, без дублирования!)
    reply_text = get_reply_message(is_night)
    try:
        bot.send_message(
            chat_id,
            reply_text,
            reply_to_message_id=message_id,
            parse_mode="Markdown"
        )
        print(f"✅ Автоответ отправлен для сообщения {message_id}")
    except Exception as e:
        print(f"❌ Ошибка автоответа: {e}")
        # Пробуем без форматирования
        try:
            bot.send_message(chat_id, reply_text.replace('*', ''), reply_to_message_id=message_id)
        except:
            pass
    
    # Пересылаем сообщение владельцу
    forward_to_owner(chat_id, message_id, user_name, user_id, original_text, chat_title)
    
    # Удаляем таймер
    timers.pop(key, None)

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
    chat_title = message.chat.title or "личный чат"
    
    # Проверка триггеров
    is_cot = contains_cot_variant(text)
    is_mention = is_owner_mentioned(text) or is_owner_mentioned_in_message(message)
    is_triggered = is_cot or is_mention
    
    # Если триггер сработал И это не владелец
    if is_triggered and user_id != YOUR_USER_ID:
        # Создаем таймер (НЕ отправляем ответ сразу!)
        key = (chat_id, message_id)
        timers[key] = True
        
        # Запускаем поток с задержкой
        timer_thread = threading.Thread(
            target=auto_reply,
            args=(chat_id, message_id, user_name, user_id, message.text, chat_title),
            daemon=True
        )
        timer_thread.start()
        
        trigger_type = "кот" if is_cot else "упоминание"
        print(f"⏰ СОЗДАН ТАЙМЕР для @{user_name} [{trigger_type}]: {message.text[:50]}")
    
    # Если ответил ВЫ — отменяем ВСЕ таймеры в этом чате
    if user_id == YOUR_USER_ID:
        keys_to_remove = [k for k in timers.keys() if k[0] == chat_id]
        for key in keys_to_remove:
            timers[key] = False
            timers.pop(key, None)
        if keys_to_remove:
            print(f"🗑️ Отменено {len(keys_to_remove)} таймеров (ответил владелец)")

print("=" * 60)
print("🤖 БОТ ЗАПУЩЕН (НОВАЯ ВЕРСИЯ С ТАЙМЕРОМ)")
print("=" * 60)
print(f"📌 Ваш ID: {YOUR_USER_ID}")
print("📋 Триггеры: кот-вариации, @qwerty0379, reply на ваши сообщения")
print("⏰ По МСК: День (8-22): 10 минут | Ночь (22-8): 5 минут")
print("=" * 60)

bot.infinity_polling()
