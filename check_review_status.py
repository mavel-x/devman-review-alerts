import argparse

import requests
from crontab import CronTab
from environs import Env
from telegram import Bot


FAILED_MESSAGE = 'По уроку {lesson_url} есть новые улучшения.'
PASSED_MESSAGE = 'Урок {lesson_url} сдан!'


def fetch_new_reviews(timestamp, devman_token):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {'Authorization': f'Token {devman_token}'}
    params = {'timestamp': timestamp}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    response_body = response.json()
    if response_body['status'] == 'timeout':
        return None
    else:
        return response_body['new_attempts']


def remove_cronjob(url):
    with CronTab(user=True) as user_crontab:
        try:
            job = next(user_crontab.find_comment(url))
            user_crontab.remove(job)
        except StopIteration:
            return


def process_reviews(reviews) -> str:
    alerts = []
    for review in reviews:
        lesson_url = review['lesson_url']
        if review['is_negative']:
            alerts.append(
                FAILED_MESSAGE.format(lesson_url=lesson_url)
            )
        else:
            alerts.append(
                PASSED_MESSAGE.format(lesson_url=lesson_url)
            )
        remove_cronjob(lesson_url)
    return '\n\n'.join(alerts)


def main():
    env = Env()
    env.read_env()
    tg_token = env('TG_TOKEN')
    tg_user_id = env.int('TG_USER_ID')
    devman_token = env('DEVMAN_TOKEN')

    argparser = argparse.ArgumentParser(description='Check if Devman has reviewed your code.')
    argparser.add_argument(
        'timestamp',
        type=float,
        help='Timestamp of last review.'
    )
    args = argparser.parse_args()
    timestamp = args.timestamp

    reviews = fetch_new_reviews(timestamp, devman_token)
    if reviews is None:
        print('Review still pending.')
        return

    alert_message = process_reviews(reviews)

    bot = Bot(token=tg_token)
    bot.send_message(
        chat_id=tg_user_id,
        text=alert_message,
        disable_web_page_preview=True,
    )


if __name__ == '__main__':
    main()
