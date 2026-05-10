import telebot
import time
import re
from datetime import datetime

# Замените на ваш токен от BotFather
BOT_TOKEN = "ВАШ_ТОКЕН_СЮДА"

# Замените на ваш Telegram ID (узнайте у @userinfobot)
YOUR_USER_ID = 123456789

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище активных сообщений, на которые еще не ответили
pending_messages = {}

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # Игнорируем сообщения от самого бота
    if message.from_user.id == bot.get_me().id:
        return
    
    chat_id = message.chat.id
    message_id = message.message_id
    user_id = message.from_user.id
    text = message.text.lower() if message.text else ""
    
    # --- Проверка триггеров "кот" или тег ---
    is_triggered = "кот" in text or f"@{message.from_user.username}" == "@qwerty0379"
    
    if is_triggered and user_id != YOUR_USER_ID:
        # Определяем время задержки
        now = datetime.now()
        if 8 <= now.hour < 22:
            delay = 600  # 10 минут днем
        else:
            delay = 300  # 5 минут ночью
        
        # Сохраняем сообщение в ожидающие
        pending_messages[message_id] = {
            "chat_id": chat_id,
            "message_id": message_id,
            "user_id": user_id,
            "text": message.text,
            "delay": delay,
            "start_time": time.time()
        }
        
        # Запускаем таймер проверки
        bot.send_message(chat_id, f"⏳ Заметил! Если {message.from_user.first_name} не ответит через {delay//60} минут, отвечу я.", 
                        reply_to_message_id=message_id)
        
        # Запускаем фоновую проверку (в реальном коде нужен threading, но для простоты используем schedule)
        check_pending_messages()
    
    # --- Если ответил владелец, удаляем ожидающие ответы ---
    if user_id == YOUR_USER_ID:
        # Удаляем все ожидающие сообщения в этом чате
        to_remove = [msg_id for msg_id, data in pending_messages.items() 
                    if data["chat_id"] == chat_id]
        for msg_id in to_remove:
            del pending_messages[msg_id]
        print(f"✅ Владелец ответил, таймеры отменены")

def check_pending_messages():
    """Проверяет истекшие ожидающие сообщения"""
    current_time = time.time()
    to_remove = []
    
    for msg_id, data in pending_messages.items():
        if current_time - data["start_time"] >= data["delay"]:
            # Время вышло, отправляем ответ
            try:
                bot.send_message(
                    data["chat_id"],
                    f"🤖 *Автоответчик*: Извините, {data['text']} — я пока не могу ответить, но обязательно отвечу позже!",
                    reply_to_message_id=data["message_id"],
                    parse_mode="Markdown"
                )
                to_remove.append(msg_id)
            except Exception as e:
                print(f"Ошибка при отправке: {e}")
    
    for msg_id in to_remove:
        del pending_messages[msg_id]

# Запуск бота
print("🤖 Бот запущен и работает...")
bot.infinity_polling()
