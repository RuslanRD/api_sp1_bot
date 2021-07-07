import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests

from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL = os.getenv('URL')

bot = Bot(TELEGRAM_TOKEN)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('main.log', maxBytes=50000000, backupCount=5)
logger.addHandler(handler)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = None
    try:
        if homework_status is None or homework_name is None:
            return 'invalid server response'
        if homework_status == 'reviewing':
            verdict = 'Работа взята на ревью.'
        elif homework_status == 'rejected':
            verdict = 'К сожалению, в работе нашлись ошибки.'
        else:
            verdict = 'Ревьюеру всё понравилось, работа зачтена!'
    except Exception as error:
        logging.error(error, exc_info=True)
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homeworks(current_timestamp):
    url = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
    }
    payload = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            url,
            headers=headers,
            params=payload
        )
    except requests.exceptions.RequestException as error:
        logging.error(f'Fatal error: {error}')
    try:
        return homework_statuses.json()
    except ValueError as error:
        logging.error(f'No JSON object could de decoded: {error}')
    except TypeError as error:
        logging.error(f'Invalid json {error}')


def send_message(message):
    return bot.send_message(CHAT_ID, message)


def main():
    current_timestamp = int(time.time())

    while True:
        try:
            homeworks = get_homeworks(current_timestamp)
            if len(homeworks['homeworks']) > 0:
                last_homework = homeworks['homeworks'][0]
                message = parse_homework_status(last_homework)
                send_message(message)
                time.sleep(5 * 60)
        except Exception as e:
            print(f'Бот упал с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
