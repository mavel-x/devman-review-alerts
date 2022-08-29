import argparse
import sys

from environs import Env
from telegram import Bot

from old_lesson import Lesson

FAILED_MESSAGE = 'По уроку {lesson_url} есть новые улучшения.'
PASSED_MESSAGE = 'Урок {lesson_url} сдан!'


def main():
    env = Env()
    env.read_env()

    argparser = argparse.ArgumentParser(description='Check if Devman has reviewed your code.')
    argparser.add_argument(
        'lesson_number',
        help='The number of the lesson you are expecting revisions for.'
    )
    argparser.add_argument(
        'attempt',
        type=int,
        help='The number of your current submission attempt.'
    )
    args = argparser.parse_args()

    token = env('TG_TOKEN')
    tg_user_id = env.int('TG_USER_ID')
    bot = Bot(token=token)

    user_cookies = {
        'csrftoken': env('CSRF_TOKEN'),
        'sessionid': env('SESSION_ID'),
    }

    lesson = Lesson(user_cookies=user_cookies, number=args.lesson_number, attempts=args.attempt)
    lesson.check_review_status()
    if not lesson.checked:
        print('Review still pending.')
        return
    lesson.set_url_from_crontab()
    if lesson.failed:
        bot.send_message(
            chat_id=tg_user_id,
            text=FAILED_MESSAGE.format(lesson_url=lesson.url),
            disable_web_page_preview=True,
        )
    else:
        bot.send_message(
            chat_id=tg_user_id,
            text=PASSED_MESSAGE.format(lesson_url=lesson.url),
            disable_web_page_preview=True,
        )
    lesson.remove_cronjob()


if __name__ == '__main__':
    main()
