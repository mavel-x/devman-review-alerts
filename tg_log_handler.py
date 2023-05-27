import logging

from telegram import Bot


class TGLogHandler(logging.Handler):

    def __init__(self, tg_bot: Bot, tg_user: int):
        self.tg_bot = tg_bot
        self.tg_user = tg_user
        super().__init__()

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.tg_user, text=log_entry)
