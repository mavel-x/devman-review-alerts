import logging
from urllib.parse import urldefrag

from environs import Env
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, Updater

from new_devman_alert import create_cronjob


def start(update: Update, context: CallbackContext):
    if update.effective_user.id != context.bot_data['allowed_sender']:
        update.effective_chat.send_message(';,;')
        return

    message_text = 'Готов уведомлять.'
    update.effective_chat.send_message(message_text)


def create_alert(update: Update, context: CallbackContext):
    user_message = update.message.text
    if 'dvmn.org/modules' in user_message:
        devman_token = context.bot_data['devman_token']
        url = urldefrag(user_message).url
        create_cronjob(url, devman_token)
        message_text = 'Уведомление создано.'
    else:
        message_text = 'Это не похоже на URL урока.'

    update.effective_chat.send_message(message_text)


def main():
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')

    env = Env()
    env.read_env()
    tg_token = env('TG_TOKEN')
    allowed_sender_id = env.int('TG_ALLOWED_SENDER')
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data.update({
        'allowed_sender': allowed_sender_id,
        'devman_token': env('DEVMAN_TOKEN'),
    })

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.entity('url') & Filters.chat(allowed_sender_id),
                                          create_alert))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()

