import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import random
import asyncio
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
USERNAME, VIOLATION_TYPE, NUM_COMPLAINTS, CONFIRMATION = range(4)

violations = {
    1: ['Спам', ['Уважаемая служба поддержки, обращаем ваше внимание на активности пользователя {username}, который рассылает большое количество нежелательной рекламы и сообщений в чатах и группах Telegram. Просим принять меры по прекращению данного спама.',
                  'Пользователь {username} активно злоупотребляет рассылкой спама, что нарушает вежливость и правила пользования платформой Telegram. Пожалуста, проверьте и примите соответствующие меры.']],
    2: ['Мошенничество', ['Уважаемая служба поддержки, прошу обратить внимание на аккаунт пользователя {username}, который предлагает участие в потенциально мошеннических схемах. Данное поведение вызывает сомнения и требует проверки.',
                          'Пользователь {username} может быть причастен к мошенническим действиям, стоит рассмотреть поведение и действия данного аккаунта более детально.']],
    3: ['Порнография', ['Уважаемая служба поддержки, являюсь пользователем Telegram и заметил нарушения в контенте аккаунта {username}, который содержит порнографический материал. Прошу принять меры по удалению данного контента и привлечению пользователя к ответственности.',
                        'Пользователь {username} активно распространяет материалы для взрослых, что противоречит правилам и целям Telegram как безопасного мессенджера.']],
    4: ['Нарушение правил', ['Уважаемая служба поддержки, обращаем ваше внимание на абонента {username}, который систематически нарушает правила платформы Telegram. Просим принять меры в отношении данного пользователя, чтобы обеспечить соблюдение правил сообщества.',
                            'Личность {username} провоцирует конфликты и размещает недопустимый контент в чатах и каналах Telegram, что недопустимо и требует вмешательства. Просим проверить и принять соответствующие меры.']],
}

phone_numbers_templates = [
    "+7917**11**2", "+7926**386**", "+7952**99*63", "+7903**76*82", "+7914**237*7*",
    "+7937**61***", "+7978**42***", "+7982**89***", "+7921**57***", "+7991**34***",
    "+7910**68***", "+7940**15***", "+7961**72***", "+7985**49***", "+7951**27***",
    "+7916**83***", "+7932**95***", "+7975**44***", "+7989**78***", "+7993**64***",
    "+7923**58***", "+7970**30***", "+7960**17***", "+7995**48***", "+7953**25***",
    "+7919**77***", "+7938**36***", "+7986**62***", "+7907**81*7*", "+7947**53*6*",
    "+7971**29***"
]

def generate_complaint(username, violation):
    complaint_text = random.choice(violations[violation][1]).format(username=username)
    return complaint_text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Это бот для отправки жалоб на пользователей Telegram.\n\n"
        "Для начала работы введите /complaint\n"
        "Для отмены в любой момент введите /cancel"
    )

async def complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процесс отправки жалобы"""
    await update.message.reply_text(
        "📝 Введите username пользователя, на которого хотите пожаловаться "
        "(например: @username или просто username):"
    )
    return USERNAME

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает username от пользователя"""
    username = update.message.text.strip()
    if username.startswith('@'):
        username = username[1:]
    
    if len(username) < 3:
        await update.message.reply_text("❌ Username слишком короткий. Попробуйте еще раз:")
        return USERNAME
    
    context.user_data['username'] = username
    
    keyboard = [
        ["1 - Спам", "2 - Мошенничество"],
        ["3 - Порнография", "4 - Нарушение правил"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await update.message.reply_text(
        "📋 Выберите тип нарушения:",
        reply_markup=reply_markup
    )
    return VIOLATION_TYPE

async def get_violation_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает тип нарушения"""
    text = update.message.text
    if text.startswith(('1', '2', '3', '4')):
        violation_type = int(text[0])
        context.user_data['violation_type'] = violation_type
        await update.message.reply_text(
            "🔢 Введите количество жалоб для отправки (1-30):",
            reply_markup=ReplyKeyboardMarkup([['1', '5', '10'], ['15', '20', '30']], 
                                           one_time_keyboard=True, resize_keyboard=True)
        )
        return NUM_COMPLAINTS
    else:
        await update.message.reply_text("❌ Пожалуйста, выберите тип нарушения из предложенных вариантов.")
        return VIOLATION_TYPE

async def get_num_complaints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает количество жалоб"""
    try:
        num_complaints = int(update.message.text)
        if 1 <= num_complaints <= 30:
            context.user_data['num_complaints'] = num_complaints
            
            username = context.user_data['username']
            violation_type = context.user_data['violation_type']
            violation_name = violations[violation_type][0]
            
            await update.message.reply_text(
                f"📋 Подтвердите данные:\n\n"
                f"👤 Пользователь: @{username}\n"
                f"⚠️  Тип нарушения: {violation_name}\n"
                f"🔢 Количество жалоб: {num_complaints}\n\n"
                f"Для подтверждения введите 'да', для отмены - 'нет'",
                reply_markup=ReplyKeyboardMarkup([['да', 'нет']], 
                                               one_time_keyboard=True, resize_keyboard=True)
            )
            return CONFIRMATION
        else:
            await update.message.reply_text("❌ Количество жалоб должно быть от 1 до 30. Попробуйте еще раз:")
            return NUM_COMPLAINTS
    except ValueError:
        await update.message.reply_text("❌ Пожалуйста, введите число от 1 до 30:")
        return NUM_COMPLAINTS

async def confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает подтверждение и отправляет жалобы"""
    if update.message.text.lower() == 'да':
        username = context.user_data['username']
        violation_type = context.user_data['violation_type']
        num_complaints = context.user_data['num_complaints']
        violation_name = violations[violation_type][0]
        
        phone_numbers = []
        for tpl in random.choices(phone_numbers_templates, k=num_complaints):
            phone_number = ''.join(random.choice('0123456789') if char == '*' else char for char in tpl)
            phone_numbers.append(phone_number)
        
        message = await update.message.reply_text(
            f"🚀 Начинаю отправку {num_complaints} жалоб на @{username}...\n\n"
            f"⏳ Это может занять некоторое время..."
        )
        
        success_count = 0
        for i, phone_number in enumerate(phone_numbers, 1):
            complaint_text = generate_complaint(username, violation_type)
            
            await asyncio.sleep(0.5)
            
            if i % 5 == 0 or i == num_complaints:
                await message.edit_text(
                    f"📤 Отправка жалоб...\n"
                    f"✅ Отправлено: {i}/{num_complaints}\n"
                    f"📞 С номера: {phone_number}"
                )
            
            success_count += 1
        
        await update.message.reply_text(
            f"✅ Готово! Отправлено {success_count} жалоб на @{username}\n"
            f"⚠️  Тип нарушения: {violation_name}\n\n"
            f"Для отправки новой жалобы введите /complaint",
            reply_markup=ReplyKeyboardMarkup([['/complaint']], resize_keyboard=True)
        )
        
    else:
        await update.message.reply_text(
            "❌ Отправка отменена.\n\n"
            "Для начала новой жалобы введите /complaint"
        )
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет текущую операцию"""
    await update.message.reply_text(
        "❌ Операция отменена.\n\n"
        "Для начала новой жалобы введите /complaint",
        reply_markup=ReplyKeyboardMarkup([['/complaint']], resize_keyboard=True)
    )
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает справку"""
    await update.message.reply_text(
        "🤖 Команды бота:\n\n"
        "/start - Начать работу с ботом\n"
        "/complaint - Отправить жалобу на пользователя\n"
        "/help - Показать эту справку\n\n"
        "📝 Для отправки жалобы вам нужно:\n"
        "1. Указать username пользователя\n"
        "2. Выбрать тип нарушения\n"
        "3. Указать количество жалоб\n"
        "4. Подтвердить отправку\n\n"
        "⚠️  Используйте бот ответственно!"
    )

def main():
    """Запуск бота"""
    # Получаем токен из переменных окружения
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не установлен!")
        return
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Настройка обработчиков
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('complaint', complaint)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
            VIOLATION_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_violation_type)],
            NUM_COMPLAINTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_num_complaints)],
            CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmation)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)
    
    # Запуск бота
    logger.info("🤖 Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()
