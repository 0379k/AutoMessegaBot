import telebot
import time
import threading
import re
from datetime import datetime
from openai import OpenAI
import os

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8721233798:AAFCqgy_TqwJ6snKMph20ea9jhwoLRo417Y"
YOUR_USER_ID = 5603035274
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
# ====================

bot = telebot.TeleBot(BOT_TOKEN)

# Дальше остальной код без изменений...

# Инициализация клиента OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": "https://t.me/B_A_S_I_K_bot",
        "X-Title": "B.A.S.I.K. Assistant",
    }
)

# Хранилища
timers = {}
chat_histories = {}

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
    return False

def get_reply_message(is_night):
    if is_night:
        return "🤖 *Б.А.С.И.К.*: В данный момент мой создатель предположительно спит, прошу вас подождать до утра.\n\n🌙 Спокойной ночи!"
    else:
        return "🤖 *Б.А.С.И.К.*: В данный момент мой создатель находится вне сети, прошу вас подождать.\n\n☀️ Хорошего дня!"

def get_ai_response(chat_id, user_question):
    """Отправляет запрос к OpenRouter API с контекстом чата"""
    try:
        # Исправляем кодировку для русского языка
        user_question = user_question.encode('utf-8').decode('utf-8')
        
        # Получаем историю чата
        history = chat_histories.get(chat_id, [])
        
        # Формируем сообщения для API
        messages = []
        
        # Системный промпт
        messages.append({
            "role": "system",
            "content": (
                "Ты — Басик, умный и дружелюбный помощник в Telegram-чате. "
                "Отвечай на вопросы пользователей вежливо и по делу. "
                "Используй контекст диалога, если он есть. "
                "Если не знаешь ответа — честно скажи об этом. "
                "Отвечай на русском языке."
            )
        })
        
        # Добавляем историю (последние 5 сообщений)
        for msg in history[-5:]:
            messages.append(msg)
        
        # Добавляем текущий вопрос
        messages.append({
            "role": "user",
            "content": user_question
        })
        
        # Запрос к OpenRouter
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            extra_body={
                "provider": "free"
            }
        )
        
        answer = response.choices[0].message.content
        return answer
        
    except Exception as e:
        print(f"❌ Ошибка при запросе к нейросети: {e}")
        return "Извините, нейросеть временно недоступна. Попробуйте позже!"

def auto_reply(chat_id, message_id, user_name, original_text):
    """Автоответчик для триггеров 'кот' и @qwerty0379"""
    now = datetime.now()
    is_night = now.hour >= 22 or now.hour < 8
    delay = 300 if is_night else 600
    
    period = "ночь (5 мин)" if is_night else "день (10 мин)"
    print(f"⏳ Таймер: жду {delay} секунд ({period})...")
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
        print(f"❌ Ошибка автоответа: {e}")
    
    timers.pop(key, None)

def forward_to_owner(chat_id, message_id, user_name, original_text, chat_title):
    """Пересылает сообщение владельцу в личку"""
    try:
        forward_text = (
            f"📨 Вам не ответили на сообщение!\n\n"
            f"👤 От: @{user_name}\n"
            f"💬 Текст: {original_text}\n"
            f"📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"🏠 Группа: {chat_title}"
        )
        bot.send_message(YOUR_USER_ID, forward_text)
        bot.forward_message(YOUR_USER_ID, chat_id, message_id)
        print(f"📨 Переслано сообщение {message_id}")
    except Exception as e:
        print(f"❌ Ошибка пересылки: {e}")

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
    
    # === ОБРАБОТКА НЕЙРОСЕТИ (БАСИК) ===
    # Паттерн: "Басик, вопрос", "басик вопрос", "БАСИК вопрос" и т.д.
    basik_pattern = r'^басик[,\s]+(.*)$'
    basik_match = re.search(basik_pattern, text, re.IGNORECASE)
    
    if basik_match and user_id != YOUR_USER_ID:
        question = basik_match.group(1).strip()
        if question:
            # Сохраняем вопрос в историю
            if chat_id not in chat_histories:
                chat_histories[chat_id] = []
            chat_histories[chat_id].append({"role": "user", "content": question})
            
            # Показываем, что бот печатает
            bot.send_chat_action(chat_id, "typing")
            
            # Получаем ответ от нейросети
            ai_response = get_ai_response(chat_id, question)
            
            # Сохраняем ответ в историю
            chat_histories[chat_id].append({"role": "assistant", "content": ai_response})
            
            # Ограничиваем историю 10 сообщениями
            if len(chat_histories[chat_id]) > 10:
                chat_histories[chat_id] = chat_histories[chat_id][-10:]
            
            # Отправляем ответ (разбиваем, если слишком длинный)
            if len(ai_response) > 4000:
                for i in range(0, len(ai_response), 4000):
                    bot.reply_to(message, ai_response[i:i+4000])
            else:
                bot.reply_to(message, f"🤖 *Басик:* {ai_response}", parse_mode="Markdown")
            
            print(f"🧠 Нейросеть ответила @{user_name} на: {question[:50]}")
            return
    
    # === АВТООТВЕТ НА "КОТ" И УПОМИНАНИЯ ===
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
        print(f"⏰ СОЗДАН ТАЙМЕР для @{user_name} [{trigger_type}]: {message.text[:50]}")
    
    # Если ответил ВЫ — отменяем таймеры
    if user_id == YOUR_USER_ID:
        keys_to_remove = [k for k in timers.keys() if k[0] == chat_id]
        for key in keys_to_remove:
            timers[key] = False
            timers.pop(key, None)
        if keys_to_remove:
            print(f"🗑️ Отменено {len(keys_to_remove)} таймеров")
    
    # Сохраняем сообщение в историю для контекста (кроме команд)
    if not text.startswith('/') and not basik_match:
        if chat_id not in chat_histories:
            chat_histories[chat_id] = []
        chat_histories[chat_id].append({
            "role": "user",
            "content": f"{user_name}: {message.text}"
        })
        if len(chat_histories[chat_id]) > 10:
            chat_histories[chat_id] = chat_histories[chat_id][-10:]

print("=" * 60)
print("🤖 БОТ ЗАПУЩЕН (ВЕРСИЯ С НЕЙРОСЕТЬЮ)")
print("=" * 60)
print(f"📌 Ваш ID: {YOUR_USER_ID}")
print("📋 ФУНКЦИИ:")
print("   • 'кот' или @qwerty0379 -> автоответ через 10/5 мин")
print("   • 'Басик, вопрос' -> мгновенный ответ нейросети")
print("   • Нейросеть помнит последние 10 сообщений в чате")
print("=" * 60)

bot.infinity_polling()
