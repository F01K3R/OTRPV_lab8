import os
import re
import smtplib
import dns.resolver
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Загрузка переменных окружения
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.yandex.ru")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "stud0000228785@study.utmn.ru")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "jeoloazzadkgbtwq")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7546505291:AAFW1kbn24eQrhvxFKCv5j29JzvWtosxN-g")

# Словарь для хранения состояний пользователей
user_states = {}

# Проверка синтаксиса email
def validate_email_format(email):
    pattern = r"^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

# Проверка домена email через MX-записи
def validate_email_domain(email):
    try:
        domain = email.split('@')[1]
        mx_records = dns.resolver.resolve(domain, 'MX')
        return bool(mx_records)
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return False

# Проверка email
def validate_email(email):
    return validate_email_format(email) and validate_email_domain(email)

# Обработчик команды /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {"email": None, "message": None}
    await update.message.reply_text("Hi! Please, send your email, where you want to send message:")

# Обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_states:
        await update.message.reply_text("To start send /start.")
        return

    if not user_states[user_id]["email"]:
        email = update.message.text
        if validate_email(email):
            user_states[user_id]["email"] = email
            await update.message.reply_text("Great! Now you can send your message:")
        else:
            await update.message.reply_text("Please, check your email.")
    elif not user_states[user_id]["message"]:
        user_states[user_id]["message"] = update.message.text
        email = user_states[user_id]["email"]
        message = user_states[user_id]["message"]

        try:
            send_email(email, message)
            await update.message.reply_text(f"Message send to {email}!")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

        user_states.pop(user_id, None)

# Функция отправки email через SMTP
def send_email(recipient_email, message_text):
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = recipient_email
    msg["Subject"] = "Telegram Bot Message"
    msg.attach(MIMEText(message_text, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, recipient_email, msg.as_string())

# Основной код приложения
if __name__ == "__main__":
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token":
        raise ValueError("Your bot token is not define. Install it as .env.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()
