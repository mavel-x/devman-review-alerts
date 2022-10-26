import logging
import random
import time

import requests
from environs import Env
from telegram import Bot

FAIL_MESSAGE = 'По уроку {lesson_url} есть новые улучшения.'
PASS_MESSAGE = 'Урок {lesson_url} сдан!'
START_MESSAGES = (
    'Готов уведомлять.',
    "Проверяю состояние проверок.",
    'Спрашиваю "А скоро проверят?"',
    "Потерпи немножко, почти проверили.",
    "Осталось ждать: `0 минут`",
    ("Она: Опять о шлюхах своих думает.\n"
     "Он: Улучшения мои улучшения..."),
)
STOP_MESSAGE = ('Скрипт проверки проверок остановлен. Перезапустите скрипт, '
                'чтобы восстановить течение судьбы, или живите дальше '
                'в проклятом мире, который сами и создали.')


def fetch_new_reviews(devman_token, timestamp):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {'Authorization': f'Token {devman_token}'}
    params = {'timestamp': timestamp}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def process_reviews(reviews: list) -> str:
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
    while True:
        try:
            response_body = fetch_new_reviews(devman_token, timestamp)
        except requests.exceptions.ReadTimeout:
            continue
        except requests.exceptions.ConnectionError:
            time.sleep(30)
            continue

        if response_body['status'] == 'timeout':
            timestamp = response_body['timestamp_to_request']
        else:
            timestamp = response_body['last_attempt_timestamp']
            alert = process_reviews(response_body['new_attempts'])
            bot.send_message(chat_id=tg_user, text=alert, disable_web_page_preview=True)


def main():
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s: %(message)s')

    env = Env()
    env.read_env()
    tg_token = env('TG_TOKEN')
    devman_token = env('DEVMAN_TOKEN')
    tg_user = env('TG_USER_ID')

    bot = Bot(tg_token)

    bot.send_message(chat_id=tg_user, text=random.choice(START_MESSAGES), parse_mode='MarkdownV2')
    try:
        check_reviews(devman_token, bot, tg_user)
    finally:
        bot.send_message(chat_id=tg_user, text=STOP_MESSAGE)


if __name__ == "__main__":
    main()
