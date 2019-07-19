import telegram
from telegram.ext import CommandHandler, Updater
from telegram.ext import MessageHandler, Filters

import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

telegram_token = "663475549:AAGmhBZvahLT96Y3U9C2Mk6vsehqNB6Sr4E"

# tg_bot = telegram.Bot(token=telegram_token)
updater = Updater(token=telegram_token, use_context=True)
print(updater.bot.getMe())


def start(update, context):
    print(f"starting in chat {update.message.chat_id}")
    context.bot.send_message(chat_id=update.message.chat_id, text="I am a bot, huzzah")


print("up")


def echo(update, context):
    print(update.message.chat_id)
    context.bot.send_message(chat_id=update.message.chat_id, text=update.message.text)


echo_handler = MessageHandler(Filters.text, echo)
updater.dispatcher.add_handler(echo_handler)

start_handler = CommandHandler('start', start)
updater.dispatcher.add_handler(start_handler)
updater.start_polling()
print("polling?")

# print(f"logged into TG as {tg_bot.get_me()}")