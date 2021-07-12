import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
from requests.exceptions import RequestException

from telegram import Bot

PRAKTIKUM_TOKEN = os.environ.get('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

bot = Bot(TELEGRAM_TOKEN)
PATH = '~/main.log'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    filemode='w'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    os.path.expanduser(PATH),
    maxBytes=50000000,
    backupCount=5,
)
logger.addHandler(handler)

HOMEWORK_STATUSES = {
    'reviewing': 'Работа взята на ревью.',
    'rejected': 'К сожалению, в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, работа зачтена!'
}

URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {
    'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
}

REPEAT_TIME = 5 * 60
SLEEP_TIME = 5


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = None
    try:
        if homework_status is None or homework_name is None:
            return 'invalid server response'
        if homework_status in HOMEWORK_STATUSES:
            verdict = HOMEWORK_STATUSES[homework_status]
    except Exception as error:
        logging.error(error, exc_info=True)
    else:
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    try:
        payload = {'from_date': current_timestamp}
    except TypeError as error:
        logging.error(f'Invalid date: {error}')
    try:
        homework_statuses = requests.get(
            URL,
            headers=HEADERS,
            params=payload
        )
    except requests.exceptions.RequestException as error:
        logging.error(f'Fatal error: {error}')
        raise RequestException('failed request. Check url, headers or params')
    homework_json = homework_statuses.json()
    if 'code' in homework_json:
        raise Exception(f'Fatal error: {homework_json["code"]}')
    try:
        return homework_json
    except ValueError as error:
        logging.error(f'No JSON object could de decoded: {error}')
    except TypeError as error:
        logging.error(f'Invalid json {error}')


def send_message(message):
    try:
        return bot.send_message(CHAT_ID, message)
    except SystemExit as error:
        logging.error(f'Invalid error: {error}')


def main():
    current_timestamp = int(time.time())

    while True:
        try:
            homeworks = get_homeworks(current_timestamp)
            if len(homeworks['homeworks']) > 0:
                last_homework = homeworks['homeworks'][0]
                message = parse_homework_status(last_homework)
                send_message(message)
                time.sleep(REPEAT_TIME)
        except Exception as e:
            logging.error(f'Бот упал с ошибкой: {e}')
            time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    main()
