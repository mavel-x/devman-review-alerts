import logging
import random
import time

import requests
from environs import Env
from telegram import Bot

logger = logging.getLogger(__name__)

FAIL_MESSAGE = 'По уроку {lesson_url} есть новые улучшения.'
PASS_MESSAGE = 'Урок {lesson_url} сдан!'
START_MESSAGES = (
    'Готов уведомлять.',
    "Проверяю состояние проверок.",
    'Спрашиваю "А скоро проверят?"',
    "Потерпи немножко, почти проверили.",
    "Осталось ждать: <code>0 минут</code>",
    ("Она: Опять о шлюхах своих думает.\n"
     "Он: Улучшения мои улучшения..."),
)
STOP_MESSAGE = ('Скрипт проверки проверок остановлен. Перезапустите скрипт, '
                'чтобы восстановить течение судьбы, или живите дальше '
                'в проклятом мире, который сами и создали.')

check_interval_minutes = 10


class TGLogHandler(logging.Handler):

    def __init__(self, tg_bot: Bot, tg_user: int):
        self.tg_bot = tg_bot
        self.tg_user = tg_user
        super().__init__()

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.tg_user, text=log_entry)


def format_alert_message(reviews: list) -> str:
    alerts = []
    for review in reviews:
        lesson_url = review['lesson_url']
        if review['is_negative']:
            alerts.append(FAIL_MESSAGE.format(lesson_url=lesson_url))
        else:
            alerts.append(PASS_MESSAGE.format(lesson_url=lesson_url))
    return '\n\n'.join(alerts)


def check_reviews(devman_token, bot, tg_user):
    timestamp = None
    url = 'https://dvmn.org/api/long_polling/'
    headers = {'Authorization': f'Token {devman_token}'}
    while True:
        params = {'timestamp': timestamp}
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            review = response.json()
        except requests.exceptions.ReadTimeout as error:
            logger.warning(f'Обработана ошибка:\n{error}.')
            continue
        except requests.exceptions.ConnectionError as error:
            logger.warning(f'Обработана ошибка:\n{error}.\nЖду 30 с и продолжаю проверять.')
            time.sleep(30)
            continue
        except Exception as error:
            logger.error(f'Бот упал с ошибкой:\n{error}.')
            raise

        if review['status'] == 'timeout':
            timestamp = review['timestamp_to_request']
        else:
            timestamp = review['last_attempt_timestamp']
            reviews = review['new_attempts']
            alert_message = format_alert_message(reviews)
            bot.send_message(chat_id=tg_user, text=alert_message, disable_web_page_preview=True)
        time.sleep(60 * check_interval_minutes)


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(filename)s: %(message)s')

    env = Env()
    env.read_env()
    tg_token = env('TG_TOKEN')
    devman_token = env('DEVMAN_TOKEN')
    tg_user = env('TG_USER_ID')
    bot = Bot(tg_token)

    logger.setLevel(logging.WARNING)
    logger.addHandler(TGLogHandler(bot, tg_user))

    start_message = random.choice(START_MESSAGES)

    bot.send_message(chat_id=tg_user, text=start_message, parse_mode='HTML')
    try:
        check_reviews(devman_token, bot, tg_user)
    finally:
        bot.send_message(chat_id=tg_user, text=STOP_MESSAGE)


if __name__ == "__main__":
    main()
