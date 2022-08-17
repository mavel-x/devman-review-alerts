import argparse
from urllib.parse import urldefrag

from environs import Env

from lesson import Lesson


if __name__ == "__main__":
    env = Env()
    env.read_env()

    user_cookies = {
        'csrftoken': env('CSRF_TOKEN'),
        'sessionid': env('SESSION_ID'),
    }

    argparser = argparse.ArgumentParser(description='Create a new cronjob to check if Devman has reviewed your code.')
    argparser.add_argument(
        'lesson_url',
        help='The URL of the lesson you are expecting revisions for.'
    )
    args = argparser.parse_args()

    url = urldefrag(args.lesson_url).url

    lesson = Lesson(user_cookies=user_cookies, url=url)
    lesson.create_cronjob()
