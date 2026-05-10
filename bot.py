import telebot
import time
import threading
import re
import json
import os
from datetime import datetime, timedelta
import schedule
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8721233798:AAFCqgy_TqwJ6snKMph20ea9jhwoLRo417Y"
YOUR_USER_ID = 5603035274
CHAT_ID = -1002462732273  # ЗАМЕНИТЕ на ID вашей группы!
# ====================

bot = telebot.TeleBot(BOT_TOKEN)
timers = {}

# Файл для хранения дней рождений
BIRTHDAYS_FILE = "birthdays.json"

def load_birthdays():
    if os.path.exists(BIRTHDAYS_FILE):
        with open(BIRTHDAYS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_birthdays(birthdays):
    with open(BIRTHDAYS_FILE, "w", encoding="utf-8") as f:
        json.dump(birthdays, f, ensure_ascii=False, indent=2)

birthdays = load_birthdays()

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
    if is_night:
        return "🤖 *Б.А.С.И.К.*: В данный момент мой создатель предположительно спит, прошу вас подождать до утра.\n\n🌙 Спокойной ночи!"
    else:
        return "🤖 *Б.А.С.И.К.*: В данный момент мой создатель находится вне сети, прошу вас подождать.\n\n☀️ Хорошего дня!"

def auto_reply(chat_id, message_id, user_name, original_text):
    now = datetime.now()
    is_night = now.hour >= 23 or now.hour < 8
    delay = 300 if is_night else 600
    
    print(f"⏳ Таймер: жду {delay} секунд...")
    time.sleep(delay)
    
    key = (chat_id, message_id)
    if not timers.get(key, False):
        return
    
    reply_text = get_reply_message(is_night)
    try:
        bot.send_message(chat_id, reply_text, reply_to_message_id=message_id, parse_mode="Markdown")
        print(f"✅ Автоответ отправлен")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    timers.pop(key, None)

# ===== ФУНКЦИИ ДЛЯ ДНЕЙ РОЖДЕНИЙ =====
def check_birthdays():
    """Проверяет, есть ли сегодня день рождения у кого-то"""
    today = datetime.now().strftime("%d.%m")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d.%m")
    
    for username, data in birthdays.items():
        if data["date"] == today:
            name = data.get("name", username)
            try:
                bot.send_message(
                    CHAT_ID,
                    f"🎉 *С ДНЁМ РОЖДЕНИЯ!* 🎉\n\n"
                    f"Поздравляем {name}! 🎂\n"
                    f"Желаем счастья, здоровья и успехов! 🥳\n\n"
                    f"@{username}",
                    parse_mode="Markdown"
                )
                print(f"✅ Отправлено поздравление для @{username}")
            except Exception as e:
                print(f"❌ Ошибка отправки поздравления: {e}")
        
        # Проверка на завтрашний день рождения (уведомление за 8 часов)
        if data["date"] == tomorrow:
            name = data.get("name", username)
            try:
                bot.send_message(
                    YOUR_USER_ID,
                    f"🎂 *Напоминание о дне рождения!*\n\n"
                    f"Завтра день рождения у {name} (@{username})!\n"
                    f"Не забудьте поздравить! 🎉",
                    parse_mode="Markdown"
                )
                print(f"📨 Отправлено уведомление о завтрашнем дне рождения @{username}")
            except Exception as e:
                print(f"❌ Ошибка отправки уведомления: {e}")

def morning_greeting():
    try:
        bot.send_message(CHAT_ID, "🌅 *Б.А.С.И.К.*: Доброе утро! Желаю всем продуктивного дня! ☀️", parse_mode="Markdown")
        print("✅ Отправлено утреннее приветствие")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def night_greeting():
    try:
        bot.send_message(CHAT_ID, "🌙 *Б.А.С.И.К.*: Спокойной ночи! Приятных снов и до завтра! 😴", parse_mode="Markdown")
        print("✅ Отправлено вечернее приветствие")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def run_scheduler():
    schedule.every().day.at("08:00").do(morning_greeting)
    schedule.every().day.at("23:59").do(night_greeting)
    schedule.every().day.at("09:00").do(check_birthdays)
    
    print("📅 Планировщик запущен")
    while True:
        schedule.run_pending()
        time.sleep(30)

# ===== КНОПКИ В ЛС =====
def main_menu_keyboard():
    """Главное меню с кнопками"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    btn_add = InlineKeyboardButton("➕ Добавить день рождения", callback_data="add_birthday")
    btn_list = InlineKeyboardButton("📋 Список дней рождений", callback_data="list_birthdays")
    btn_remove = InlineKeyboardButton("❌ Удалить день рождения", callback_data="remove_birthday")
    keyboard.add(btn_add, btn_list, btn_remove)
    return keyboard

def cancel_keyboard():
    """Кнопка отмены"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return keyboard

# Обработка callback-запросов от кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.from_user.id != YOUR_USER_ID:
        bot.answer_callback_query(call.id, "❌ У вас нет прав для этого действия", show_alert=True)
        return
    
    if call.data == "add_birthday":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, 
            "📝 *Введите данные в формате:*\n\n"
            "`15.05 @username Имя`\n\n"
            "Пример: `15.05 @ivan Иван Петров`\n\n"
            "Нажмите 'Отмена' чтобы вернуться в меню",
            parse_mode="Markdown",
            reply_markup=cancel_keyboard())
        bot.register_next_step_handler(msg, process_add_birthday)
    
    elif call.data == "list_birthdays":
        bot.answer_callback_query(call.id)
        if not birthdays:
            bot.send_message(call.message.chat.id, "📭 Список дней рождений пуст", reply_markup=main_menu_keyboard())
        else:
            text = "🎂 *Список дней рождений:*\n\n"
            for username, data in birthdays.items():
                text += f"📅 {data['date']} → @{username} ({data['name']})\n"
            bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    
    elif call.data == "remove_birthday":
        if not birthdays:
            bot.answer_callback_query(call.id, "Список пуст", show_alert=True)
            bot.send_message(call.message.chat.id, "📭 Нет дней рождений для удаления", reply_markup=main_menu_keyboard())
            return
        
        bot.answer_callback_query(call.id)
        keyboard = InlineKeyboardMarkup(row_width=1)
        for username, data in birthdays.items():
            btn = InlineKeyboardButton(f"❌ {data['date']} {data['name']} (@{username})", callback_data=f"del_{username}")
            keyboard.add(btn)
        keyboard.add(InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu"))
        bot.send_message(call.message.chat.id, "👤 *Выберите кого удалить:*", parse_mode="Markdown", reply_markup=keyboard)
    
    elif call.data.startswith("del_"):
        username = call.data[4:]
        if username in birthdays:
            del birthdays[username]
            save_birthdays(birthdays)
            bot.answer_callback_query(call.id, f"✅ Удалён @{username}", show_alert=True)
            bot.edit_message_text(f"✅ Удалён @{username}", call.message.chat.id, call.message.message_id, reply_markup=main_menu_keyboard())
        else:
            bot.answer_callback_query(call.id, "❌ Не найден")
    
    elif call.data == "back_to_menu":
        bot.answer_callback_query(call.id)
        bot.edit_message_text("🏠 *Главное меню*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    
    elif call.data == "cancel":
        bot.answer_callback_query(call.id)
        bot.edit_message_text("🏠 *Действие отменено*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=main_menu_keyboard())

def process_add_birthday(message):
    if message.text == "/start" or (message.text and message.text.lower() == "отмена"):
        bot.send_message(message.chat.id, "❌ Добавление отменено", reply_markup=main_menu_keyboard())
        return
    
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            bot.send_message(message.chat.id, "❌ Неверный формат. Пример: `15.05 @ivan Иван`", parse_mode="Markdown", reply_markup=main_menu_keyboard())
            return
        
        date = parts[0]
        username = parts[1].replace('@', '')
        name = parts[2]
        
        try:
            datetime.strptime(date, "%d.%m")
        except:
            bot.send_message(message.chat.id, "❌ Неверный формат даты. Используйте ДД.ММ", reply_markup=main_menu_keyboard())
            return
        
        birthdays[username] = {"date": date, "name": name}
        save_birthdays(birthdays)
        
        bot.send_message(message.chat.id, f"✅ Добавлен день рождения:\n📅 {date}\n👤 @{username}\n🎂 {name}", reply_markup=main_menu_keyboard())
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}", reply_markup=main_menu_keyboard())

@bot.message_handler(commands=['start'])
def start_cmd(message):
    if message.chat.type == 'private':
        bot.send_message(message.chat.id, 
            "🎂 *Бот-помощник с напоминанием о днях рождения!*\n\n"
            "Нажмите на кнопки ниже для управления днями рождения:\n\n"
            "• **Добавить** — добавить день рождения\n"
            "• **Список** — посмотреть все даты\n"
            "• **Удалить** — удалить день рождения\n\n"
            "🎉 В день рождения в 09:00 бот отправит поздравление в группу!\n"
            "📨 За 8 часов бот пришлёт вам уведомление в ЛС.",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard())

# ===== ОСНОВНОЙ ОБРАБОТЧИК =====
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.from_user.id == bot.get_me().id:
        return
    
    # Игнорируем команды (обработаны выше)
    if message.text and message.text.startswith('/'):
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
        print(f"⏰ Таймер для @{user_name} [{trigger_type}]")
    
    if user_id == YOUR_USER_ID:
        keys_to_remove = [k for k in timers.keys() if k[0] == chat_id]
        for key in keys_to_remove:
            timers[key] = False
            timers.pop(key, None)
        if keys_to_remove:
            print(f"🗑️ Отменено {len(keys_to_remove)} таймеров")

# ===== ЗАПУСК =====
print("=" * 60)
print("🤖 БОТ ЗАПУЩЕН (С КНОПКАМИ И УВЕДОМЛЕНИЯМИ)")
print("=" * 60)
print(f"📌 Ваш ID: {YOUR_USER_ID}")
print(f"📌 ID группы: {CHAT_ID}")
print("📋 ФУНКЦИИ:")
print("   • 'кот' или @qwerty0379 -> автоответ через 10/5 мин")
print("   • Ночной режим: 23:00 - 08:00 (ожидание 5 мин)")
print("   • Ежедневно: 08:00 - утреннее приветствие")
print("   • Ежедневно: 23:59 - вечернее приветствие")
print("   • Ежедневно: 09:00 - проверка дней рождений")
print("   • Уведомление в ЛС за 8 часов до дня рождения")
print("   • Кнопки в ЛС вместо команд")
print("=" * 60)

# Запускаем планировщик
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

# Запускаем бота
bot.infinity_polling()
