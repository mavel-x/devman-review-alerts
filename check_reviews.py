import logging
import random
import time

import requests
import telegram
from environs import Env

from bot_messages import FAIL_MESSAGE, PASS_MESSAGE, START_MESSAGES, STOP_MESSAGE
from tg_log_handler import TGLogHandler

logger = logging.getLogger(__name__)

REVIEWS_URL = 'https://dvmn.org/api/long_polling/'
CHECK_INTERVAL_MINUTES = 10


def format_alert_message(reviews: list) -> str:
    alerts = []
    for review in reviews:
        lesson_url = review['lesson_url']
        if review['is_negative']:
            alerts.append(FAIL_MESSAGE.format(lesson_url=lesson_url))
        else:
            alerts.append(PASS_MESSAGE.format(lesson_url=lesson_url))
    return '\n\n'.join(alerts)


def check_once(devman_token: str, bot: telegram.Bot, tg_user: int, timestamp: int | None):
    headers = {'Authorization': f'Token {devman_token}'}
    params = {'timestamp': timestamp}
    response = requests.get(REVIEWS_URL, headers=headers, params=params)
    response.raise_for_status()
    review = response.json()

    if review['status'] == 'timeout':
        timestamp = review['timestamp_to_request']
    else:
        timestamp = review['last_attempt_timestamp']
        reviews = review['new_attempts']
        alert_message = format_alert_message(reviews)
        bot.send_message(chat_id=tg_user, text=alert_message, disable_web_page_preview=True)
    return timestamp


def check_forever(devman_token: str, bot: telegram.Bot, tg_user: int):
    timestamp = None
    while True:
        try:
            timestamp = check_once(devman_token, bot, tg_user, timestamp)
            time.sleep(60 * CHECK_INTERVAL_MINUTES)
        except requests.exceptions.ReadTimeout as error:
            logger.warning(f'Обработана ошибка:\n'
                           f'{error}.')
        except requests.exceptions.ConnectionError as error:
            logger.warning(f'Обработана ошибка:\n'
                           f'{error}.\n'
                           f'Жду 30 с и продолжаю проверять.')
            time.sleep(30)
        except Exception as error:
            logger.error(f'Бот упал с ошибкой:\n'
                         f'{error}.')
            raise


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(filename)s: %(message)s')

    env = Env()
    env.read_env()
    tg_token = env.str('TG_TOKEN')
    devman_token = env.str('DEVMAN_TOKEN')
    tg_user = env.int('TG_USER_ID')
    bot = telegram.Bot(tg_token)

    logger.setLevel(logging.WARNING)
    logger.addHandler(TGLogHandler(bot, tg_user))

    start_message = random.choice(START_MESSAGES)
    bot.send_message(chat_id=tg_user, text=start_message, parse_mode='HTML')

    try:
        check_forever(devman_token, bot, tg_user)
    finally:
        bot.send_message(chat_id=tg_user, text=STOP_MESSAGE)


if __name__ == "__main__":
    main()
