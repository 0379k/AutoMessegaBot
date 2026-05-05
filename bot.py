import telebot
import time
import threading
import re
from datetime import datetime

# ===== НАСТРОЙКИ (ЗАМЕНИТЕ НА СВОИ) =====
BOT_TOKEN = "8721233798:AAFCqgy_TqwJ6snKMph20ea9jhwoLRo417Y"  # Ваш токен
YOUR_USER_ID = 5603035274  # Ваш Telegram ID (узнайте у @userinfobot)
# ========================================

bot = telebot.TeleBot(BOT_TOKEN)

# Словарь для хранения таймеров: ключ = (chat_id, message_id)
timers = {}

# Словарь для хранения информации о сообщениях для пересылки
pending_forward = {}

# ===== РАСШИРЕННЫЙ СПИСОК ВАРИАЦИЙ СЛОВА "КОТ" =====
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
    """Проверяет, содержит ли текст любую вариацию слова "кот" """
    if COT_VARIANTS.search(text):
        return True
    return False

def is_owner_mentioned(text):
    """Проверяет, упомянут ли в тексте владелец с тегом @qwerty0379"""
    return '@qwerty0379' in text.lower()

def is_owner_mentioned_in_message(message):
    """Проверяет, есть ли упоминание владельца в сообщении"""
    if message.text and '@qwerty0379' in message.text.lower():
        return True
    
    if message.reply_to_message:
        if message.reply_to_message.from_user.id == YOUR_USER_ID:
            return True
    
    if message.entities:
        for entity in message.entities:
            if entity.type == 'mention':
                mention = message.text[entity.offset:entity.offset + entity.length]
                if mention.lower() == '@qwerty0379':
                    return True
    
    return False

def get_reply_message(is_night):
    """Возвращает разные сообщения в зависимости от времени суток"""
    if is_night:
        return "🤖 *Б.А.С.И.К.*: В данный момент мой создатель предположительно спит, прошу вас подождать до утра чтобы он вам смог ответить! 🌙"
    else:
        return "🤖 *Б.А.С.И.К.*: В данный момент мой создатель находится вне сети, прошу вас подождать чтобы дождаться ответа! ☀️"

def forward_to_owner(chat_id, message_id, user_name, user_id, original_text, chat_title):
    """Пересылает сообщение владельцу в личку"""
    try:
        forward_text = (
            f"📨 *Вам пришло новое сообщение!*\n\n"
            f"👤 *От:* @{user_name} (ID: {user_id})\n"
            f"💬 *Текст:* {original_text}\n"
            f"📅 *Время:* {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"🏠 *Группа:* {chat_title}\n\n"
            f"⚠️ *Статус:* Вы не ответили на это сообщение"
        )
        
        bot.send_message(YOUR_USER_ID, forward_text, parse_mode="Markdown")
        
        try:
            bot.forward_message(YOUR_USER_ID, chat_id, message_id)
        except:
            pass
        
        print(f"📨 Переслано сообщение {message_id} от @{user_name} владельцу")
        return True
    except Exception as e:
        print(f"❌ Ошибка при пересылке: {e}")
        return False

def auto_reply(chat_id, message_id, user_name, user_id, original_text, is_night, chat_title):
    """Функция, которая срабатывает через задержку"""
    time.sleep(0.5)
    
    key = (chat_id, message_id)
    if timers.get(key, False) is False:
        return
    
    forward_key = (chat_id, message_id)
    if forward_key in pending_forward and pending_forward[forward_key]:
        timers.pop(key, None)
        return
    
    reply_text = get_reply_message(is_night)
    
    try:
        bot.send_message(
            chat_id,
            f"{reply_text}\n\n📝 *Ваше сообщение:* {original_text[:100]}...",
            reply_to_message_id=message_id,
            parse_mode="Markdown"
        )
        time_period = "ночь" if is_night else "день"
        print(f"✅ Автоответ отправлен для сообщения {message_id} ({time_period})")
    except Exception as e:
        print(f"❌ Ошибка при отправке автоответа: {e}")
    
    forward_to_owner(chat_id, message_id, user_name, user_id, original_text, chat_title)
    pending_forward[forward_key] = True
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
    
    chat_title = message.chat.title or "личный чат"
    
    # Проверка триггеров
    is_owner_triggered = is_owner_mentioned_in_message(message)
    is_cot_triggered = contains_cot_variant(text)
    is_triggered = is_cot_triggered or is_owner_triggered or is_owner_mentioned(text)
    
    if is_triggered and user_id != YOUR_USER_ID:
        now = datetime.now()
        is_night = now.hour >= 22 or now.hour < 8
        
        if is_night:
            delay = 300
            period = "ночь (5 мин)"
        else:
            delay = 600
            period = "день (10 мин)"
        
        key = (chat_id, message_id)
        timers[key] = True
        
        forward_key = (chat_id, message_id)
        if forward_key not in pending_forward:
            pending_forward[forward_key] = False
        
        timer_thread = threading.Thread(
            target=auto_reply,
            args=(chat_id, message_id, user_name, user_id, message.text, is_night, chat_title),
            daemon=True
        )
        timer_thread.start()
        
        trigger_type = "кот-вариация" if is_cot_triggered else "упоминание владельца" if is_owner_triggered else "@qwerty0379"
        print(f"⏰ Запущен таймер ({period}) для @{user_name} [{trigger_type}]: {message.text[:50]}")
    
    # Если ответил ВЫ — отменяем таймеры
    if user_id == YOUR_USER_ID:
        cancelled = 0
        keys_to_remove = [k for k in timers.keys() if k[0] == chat_id]
        for key in keys_to_remove:
            timers[key] = False
            timers.pop(key, None)
            cancelled += 1
        
        if cancelled > 0:
            print(f"🗑️ Отменено {cancelled} таймеров, так как ответил владелец")

@bot.message_handler(commands=['status'])
def status_command(message):
    if message.from_user.id == YOUR_USER_ID:
        active_count = len(timers)
        forwarded_count = sum(1 for v in pending_forward.values() if v)
        
        status_text = (
            f"📊 *Статистика бота:*\n\n"
            f"⏰ Активных таймеров: {active_count}\n"
            f"📨 Переслано сообщений: {forwarded_count}\n"
            f"👥 Мониторится групп: {len(set(k[0] for k in timers))}"
        )
        bot.reply_to(message, status_text, parse_mode="Markdown")

@bot.message_handler(commands=['clean'])
def clean_command(message):
    if message.from_user.id == YOUR_USER_ID:
        old_count = len(pending_forward)
        pending_forward.clear()
        bot.reply_to(message, f"🧹 Очищено {old_count} записей о пересланных сообщениях")

# ===== ЗАПУСК БОТА =====
print("=" * 60)
print("🤖 БОТ ЗАПУЩЕН И РАБОТАЕТ")
print("=" * 60)
print(f"📌 Ваш ID: {YOUR_USER_ID}")
print(f"🔑 Токен: {BOT_TOKEN[:20]}...")
print("\n📋 АКТИВНЫЕ ТРИГГЕРЫ:")
print("   • Все вариации слова 'кот'")
print("   • Прямые упоминания @qwerty0379")
print("   • Ответы (reply) на ваши сообщения")
print("\n🚀 Бот готов к работе!\n")

bot.infinity_polling()