import argparse
import sys
from inspect import getsourcefile
from pathlib import Path
from urllib.parse import urldefrag

import requests
from crontab import CronTab
from environs import Env

current_file = Path(getsourcefile(lambda: 0))
source_dir = Path.resolve(current_file).parent
CHECK_REVIEW_SCRIPT = 'check_review_status.py'
CRON_COMMAND = f'{sys.executable} {source_dir}/{CHECK_REVIEW_SCRIPT}'
REVIEWS_URL = 'https://dvmn.org/reviews/lesson/{lesson_number}/'
CHECK_MINUTE_INTERVAL = 20


def get_last_review_timestamp(devman_token):
    url = 'https://dvmn.org/api/user_reviews/'
    headers = {'Authorization': f'Token {devman_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['results'][0]['timestamp']


def create_cronjob(url, devman_token, timestamp=None):
    if timestamp is None:
        timestamp = get_last_review_timestamp(devman_token)
    with CronTab(user=True) as user_crontab:
        job = user_crontab.new(
            command=f'{CRON_COMMAND} {timestamp}',
            comment=url,
        )
        job.minute.every(CHECK_MINUTE_INTERVAL)
        job.hour.during(7, 23)


def main():
    env = Env()
    env.read_env()
    devman_token = env('DEVMAN_TOKEN')

    argparser = argparse.ArgumentParser(description='Create a new cronjob to check if Devman has reviewed your code.')
    argparser.add_argument(
        'lesson_url',
        help='The URL of the lesson you are expecting revisions for.'
    )
    args = argparser.parse_args()
    url = urldefrag(args.lesson_url).url

    create_cronjob(url, devman_token)


if __name__ == "__main__":
    main()
