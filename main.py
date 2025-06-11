import logging

from telegram import Update
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler
from get_token import BOT_TOKEN
from hashlib import sha256
from database import CyrilDB

CyrilDB = CyrilDB('db/cyril.db')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TIMEZONE, GROUP_NAME, PASSWORD, CONFIRM = range(4)
RESPONSE = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id_tg = update.effective_chat.id
    if not CyrilDB.chat_exists(1, chat_id_tg):
        await context.bot.send_message(chat_id=chat_id_tg,
                                       text="вы тут новенький, ну я вас в списочек записал, давайте теперь /group оформим",
                                       reply_to_message_id=update.message.id)
        CyrilDB.add_chat(1, chat_id_tg)
    else:
        await context.bot.send_message(chat_id=chat_id_tg,
                                       text="kys, я вас уже знаю, смотрите команды в меню",
                                       reply_to_message_id=update.message.id)


async def group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинаем добавление группы"""
    chat_id_tg = update.effective_chat.id
    if not CyrilDB.chat_exists(1, chat_id_tg):
        await context.bot.send_message(chat_id=chat_id_tg,
                                       text="вы вообще КТО? /start оформите мне",
                                       reply_to_message_id=update.message.id)
        return

    chat_id = CyrilDB.get_chat_id(1, chat_id_tg)
    if not CyrilDB.chat_has_group(chat_id):
        await update.message.reply_text(
            "какой ваш часовой пояс по Гринвичу? (напр +7)\n/cancel чтобы отменить",
            reply_to_message_id=update.message.id
        )
        return TIMEZONE
    else:
        group_id = CyrilDB.get_group_id(chat_id)
        name = CyrilDB.get_group_name(group_id)
        await context.bot.send_message(chat_id=chat_id_tg,
                                       text="этот чат принадлежит группе ID {0}: \"{1}\"".format(group_id, name),
                                       reply_to_message_id=update.message.id)


async def timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace('+', '')
    if text == "/cancel":
        await update.message.reply_text(
            "ладно, потом посмотрим",
            reply_to_message_id=update.message.id
        )
        return ConversationHandler.END
    try:
        int(text)
    except ValueError:
        await update.message.reply_text(
            "правильно введите, например +7 или там -2",
            reply_to_message_id=update.message.id
        )
        return TIMEZONE

    tz = int(text)
    context.user_data["timezone"] = tz
    await update.message.reply_text(
        "услышал тебя родной, как назовём группу?",
        reply_to_message_id=update.message.id
    )
    return GROUP_NAME


async def group_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    context.user_data["name"] = name
    await update.message.reply_text(
        "ок, теперь надо придумать пароль/кодовое слово, чтобы другой чат мог подключиться к группе",
        reply_to_message_id=update.message.id
    )

    return PASSWORD


async def group_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    name = context.user_data["name"]
    tz = context.user_data["timezone"]
    if text == "/cancel":
        await update.message.reply_text(
            "ладно, отменяю, потом посмотрим",
            reply_to_message_id=update.message.id
        )
        return ConversationHandler.END
    else:
        context.user_data["pword"] = text
        await update.message.reply_text(
            "по итогу будет группа \"{0}\", временная зона {1} пароль \'{2}\'\nДелаем? (да/нет)".format(name, tz,
                                                                                                         text),
            reply_to_message_id=update.message.id
        )
        return CONFIRM


async def group_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "/cancel" or text == "нет":
        await update.message.reply_text(
            "ладно, отменил, можете попробовать ещё раз",
            reply_to_message_id=update.message.id
        )
        return ConversationHandler.END
    else:
        name = context.user_data["name"]
        tz = context.user_data["timezone"]
        pword = context.user_data["pword"]
        passw = sha256(pword.encode()).hexdigest()
        group_id = CyrilDB.add_group(tz, name, passw)
        chat_id = CyrilDB.get_chat_id(1,update.effective_chat.id)
        CyrilDB.link_chat(group_id,chat_id)
        await update.message.reply_text(
            "всё, теперь ваш чат в группе {0}: \"{1}\"\n"
            "чтобы подключить другой чат, напишите в нём /link {0} {2}\n"
            "рекомендую закрепить это сообщение а то мало ли потеряется".format(
                group_id, name, pword),
            reply_to_message_id=update.message.id
        )
        return ConversationHandler.END

async def link(update: Update,context: ContextTypes.DEFAULT_TYPE):
    chat_id_tg = update.effective_chat.id
    if not CyrilDB.chat_exists(1, chat_id_tg):
        await context.bot.send_message(chat_id=chat_id_tg,
                                       text="вы вообще КТО? /start оформите мне",
                                       reply_to_message_id=update.message.id)
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "чего-то не хватает, пишите по формату /link [id] [пароль]",
            reply_to_message_id=update.message.id
        )
        return
    group_id = context.args.pop(0)
    passw = ''.join(context.args)
    pword = sha256(passw.encode()).hexdigest()
    if not CyrilDB.group_exists(group_id):
        await update.message.reply_text(
            "у меня в списочке нету такой группы",
            reply_to_message_id=update.message.id
        )
        return
    elif not CyrilDB.group_password(group_id,pword):
        name = CyrilDB.get_group_name(group_id)
        await update.message.reply_text(
            "группа \"{0}\", но пароль не тот".format(name),
            reply_to_message_id=update.message.id
        )
        return
    else:
        chat_id = CyrilDB.get_chat_id(1,chat_id_tg)
        CyrilDB.link_chat(group_id,chat_id)
        name = CyrilDB.get_group_name(group_id)
        await update.message.reply_text(
            "теперь ваш чат в группе {0}: \"{1}\"".format(group_id,name),
            reply_to_message_id=update.message.id
        )

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id_tg = update.effective_chat.id
    if not CyrilDB.chat_exists(1, chat_id_tg):
        await context.bot.send_message(chat_id=chat_id_tg,
                                       text="вы вообще КТО? /start оформите мне",
                                       reply_to_message_id=update.message.id)
        return

    chat_id = CyrilDB.get_chat_id(1, chat_id_tg)
    if CyrilDB.chat_has_group(chat_id):
        group_id = CyrilDB.get_group_id(chat_id)
        name = CyrilDB.get_group_name(group_id)
        context.user_data["group_id"] = group_id
        await update.message.reply_text(
            "вы сейчас в группе {0}: \"{1}\"\nоткрепляемся? (да/нет)\n/cancel чтобы отменить".format(group_id,
                                                                                                     name),
            reply_to_message_id=update.message.id
        )
        return RESPONSE
    else:
        await update.message.reply_text(
            "этот чат и так не в группе",
            reply_to_message_id=update.message.id
        )

async def response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text == "/cancel" or text == "нет":
        await update.message.reply_text(
            "ладно, остаёмся в группе",
            reply_to_message_id=update.message.id
        )
    elif text == "да":
        group_id = context.user_data["group_id"]
        chat_id = CyrilDB.get_chat_id(1, update.effective_chat.id)
        CyrilDB.unlink_chat(chat_id)
        await update.message.reply_text(
            "теперь у чата нет группы",
            reply_to_message_id=update.message.id
        )
        if not CyrilDB.group_has_chats(group_id):
            CyrilDB.remove_group(group_id)
    else:
        await update.message.reply_text(
            "я вас не понимаю, скажите по-простому да/нет\n/cancel чтобы отменить",
            reply_to_message_id=update.message.id
        )
        return RESPONSE
    return ConversationHandler.END

async def important(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "используйте /share В ОТВЕТ на важное сообщение, чтобы я знал, что пересылать",
            reply_to_message_id=update.message.id
        )
        return
    elif not update.message.reply_to_message.text:
        await update.message.reply_text(
            "не могу прочитать, что тут написано",
            reply_to_message_id=update.message.reply_to_message.id
        )
        return

    user_id = update.message.from_user.name
    information = update.message.reply_to_message.text
    text = "пересланное сообщение от {0}:\n{1}".format(user_id, information)

    chat_id = CyrilDB.get_chat_id(1, update.effective_chat.id)
    group_id = CyrilDB.get_group_id(chat_id)
    chats = CyrilDB.group_chats(group_id)
    current_chat = update.effective_chat.id
    for chat in chats:
        chat_id_in_messenger = chat[2]
        if not chat_id_in_messenger == current_chat:
            await context.bot.send_message(chat_id_in_messenger, text)

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id_tg = update.effective_chat.id
    if not CyrilDB.chat_exists(1, chat_id_tg):
        await context.bot.send_message(chat_id=chat_id_tg,
                                       text="вы тут новенькие, ну я вас в списочек записал",
                                       reply_to_message_id=update.message.id)
        CyrilDB.add_chat(1, chat_id_tg)
    chat_id = CyrilDB.get_chat_id(1, update.effective_chat.id)
    CyrilDB.add_message(chat_id, update.message.id, update.message.text)
    print("запись из чата ID {0} : {1} \"{2}\"".format(chat_id, update.message.id, update.message.text))

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "пон, в следующий раз значит",
        reply_to_message_id=update.message.id
    )

    return ConversationHandler.END

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler("start", start)

    group_handler = ConversationHandler(
        entry_points=[CommandHandler("group", group)],
        states={
            TIMEZONE: [MessageHandler(filters.TEXT, timezone)],
            GROUP_NAME: [MessageHandler(filters.TEXT, group_name)],
            PASSWORD: [MessageHandler(filters.TEXT,group_password)],
            CONFIRM: [MessageHandler(filters.TEXT,group_confirm)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    remove_handler = ConversationHandler(
        entry_points=[CommandHandler("remove", remove)],
        states={
            RESPONSE: [MessageHandler(filters.TEXT, response)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    link_handler = CommandHandler("link", link)

    important_handler = CommandHandler("share", important)

    message_handler = MessageHandler(filters.TEXT, message)

    application.add_handler(start_handler)
    application.add_handler(group_handler)
    application.add_handler(link_handler)
    application.add_handler(remove_handler)
    application.add_handler(important_handler)
    application.add_handler(message_handler)

    application.run_polling()
