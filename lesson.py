import os
import re
import sys
from typing import Optional

import requests
from crontab import CronTab

CHECK_REVIEW_SCRIPT = 'check_review_status.py'
REVIEWS_URL = 'https://dvmn.org/reviews/lesson/{lesson_number}/'
CRON_COMMAND = f'{sys.executable} {os.getcwd()}/{CHECK_REVIEW_SCRIPT}'
CHECK_INTERVAL = 20  # in minutes


class Lesson:
    def __init__(self, *, user_cookies: dict, url: Optional[str] = None,
                 number: Optional[int] = None, attempts: Optional[int] = None):
        self.user_cookies = user_cookies
        self.url = url
        self.number = number
        self.attempts = attempts
        self.checked = False
        self.failed = None

        if self.url is None and self.number is None:
            raise AttributeError('A Lesson must have either a URL or a number.')

    def __fetch_html(self):
        response = requests.get(self.url, cookies=self.user_cookies)
        response.raise_for_status()
        return response.text

    @staticmethod
    def __find_number_on_page(page_html):
        search_pattern = r'reviews/lesson/\d\d?'
        match = re.search(search_pattern, page_html)
        if not match:
            return
        return match.group().split('/')[-1]

    def __set_number_by_url(self):
        html = self.__fetch_html()
        self.number = self.__find_number_on_page(html)

    def __fetch_reviews(self):
        if self.number is None:
            self.__set_number_by_url()
        url = REVIEWS_URL.format(lesson_number=self.number)
        response = requests.get(url, cookies=self.user_cookies)
        response.raise_for_status()
        return response.json()

    def __evaluate_reviews(self, reviews):
        if len(reviews) < self.attempts:
            return
        self.checked = True
        failed = reviews[-1]['is_negative']
        self.failed = failed

    def __set_attempt_number(self):
        reviews = self.__fetch_reviews()
        self.attempts = len(reviews) + 1

    def check_review_status(self):
        reviews = self.__fetch_reviews()
        self.__evaluate_reviews(reviews)

    def set_url_from_crontab(self):
        user_crontab = CronTab(user=True)
        job = next(user_crontab.find_command(f'{CHECK_REVIEW_SCRIPT} {self.number}'))
        self.url = job.comment

    def create_cronjob(self):
        self.__set_attempt_number()
        self.__set_number_by_url()
        with CronTab(user=True) as user_crontab:
            job = user_crontab.new(
                command=f"{CRON_COMMAND} {self.number} {self.attempts}",
                comment=self.url
            )
            job.setall(f'*/{CHECK_INTERVAL} 7-23 * * *')

    def remove_cronjob(self):
        with CronTab(user=True) as user_crontab:
            job = next(user_crontab.find_comment(self.url))
            user_crontab.remove(job)
