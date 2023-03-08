"""Module contains homework checking telegram bot description."""
import json.decoder
import logging
import os
import sys
import time
import typing as ty
from http import HTTPStatus
from logging import StreamHandler

import requests
import telegram
from dotenv import load_dotenv

from exception import (DoesntSendMessagesException, EmptyHomeworkException,
                       EndpointReachingException, GeneralProgramException,
                       NoEnvValueException, RequestFailedException,
                       UnexpectedAPIAnswerException,
                       UnexpectedAPIAnswerStatusException,
                       WrongHomeworkStatusException,
                       WrongHomeworkStructureException, WrongTokenException)

load_dotenv()

PRACTICUM_TOKEN: ty.Optional[str] = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: ty.Optional[str] = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: ty.Optional[str] = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


class ErrorTokenList:
    """Contain token error texts."""

    NO_PRACTICUM_TOKEN_ANSWER = 'PRACTICUM_TOKEN has not been found in env'
    NO_TELEGRAM_TOKEN_ANSWER = 'TELEGRAM_TOKEN has not been found in env'
    NO_TELEGRAM_CHAT_ID_TOKEN_ANSWER = (
        'TELEGRAM_CHAT_ID has not been found in env'
    )
    WRONG_TELEGRAM_TOKEN = 'TELEGRAM_TOKEN is wrong'


def init_logger() -> logging.Logger:
    """Initialize logger with handler."""
    handler: logging.StreamHandler = StreamHandler(sys.stdout)
    formatter: logging.Formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s',
    )
    handler.setFormatter(formatter)

    logger: logging.Logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger


logger = init_logger()


def check_tokens() -> None:
    """Check if tokens for a module loaded successfully."""
    if not PRACTICUM_TOKEN:
        raise NoEnvValueException(
            ErrorTokenList.NO_PRACTICUM_TOKEN_ANSWER,
        )
    if not TELEGRAM_TOKEN:
        raise NoEnvValueException(
            ErrorTokenList.NO_TELEGRAM_TOKEN_ANSWER,
        )
    if not TELEGRAM_CHAT_ID:
        raise NoEnvValueException(
            ErrorTokenList.NO_TELEGRAM_CHAT_ID_TOKEN_ANSWER,
        )
    try:
        telegram_token_status: int = requests.get(
            f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMdsasde',
        ).status_code
    except requests.RequestException as error:
        raise RequestFailedException(
            f'Something went wrong with Telegram API request: {error}',
        )
    if telegram_token_status == HTTPStatus.UNAUTHORIZED:
        raise WrongTokenException(
            ErrorTokenList.WRONG_TELEGRAM_TOKEN,
        )


def send_message(bot: telegram.Bot, message: str) -> None:
    """Sends message to a defined chat using a telegram bot."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logger.debug(
            f'Bot has sent a message: "{message}" '
            f'in telegram chat #{TELEGRAM_CHAT_ID}',
        )
    except Exception as error:
        logger.error(error)
        raise DoesntSendMessagesException(
            f'Bot has not sent a message: "{message[:20]}..." '
            f'in telegram chat #{TELEGRAM_CHAT_ID}. Error: {error}',
        )


def get_api_answer(timestamp: int) -> ty.Dict[str, ty.Any]:
    """Retrieve an information from Yandex API."""
    payload = {'from_date': timestamp}
    try:
        response: requests.Response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params=payload,
        )
        if response.status_code != HTTPStatus.OK:
            raise UnexpectedAPIAnswerStatusException(
                f'An API answer status code does not equal 200. '
                f'Status code: {response.status_code}',
            )
        response = response.json()
    except requests.RequestException as error:
        raise RequestFailedException(
            f'Something went wrong with Yandex API request: {error}',
        )
    except json.decoder.JSONDecodeError as error:
        raise EndpointReachingException(
            f'Endpoint: "{ENDPOINT}" could not be reached. Error: {error}',
        )
    return response


def check_response(response: ty.Dict) -> None:
    """Check if a Yandex API response is correct."""
    if not isinstance(response, dict):
        raise TypeError(
            'Yandex API answer value under homeworks key is not a list '
            'or answer value is not a dict',
        )
    if 'code' in response:
        raise UnexpectedAPIAnswerException(
            f'Unexpected yandex API answer. Code: "{response["code"]}"',
        )
    if 'homeworks' not in response:
        raise UnexpectedAPIAnswerException(
            f'Unexpected yandex API answer. No homeworks key: {response}',
        )
    if 'current_date' not in response:
        raise UnexpectedAPIAnswerException(
            f'Unexpected yandex API answer. No current_date key: {response}',
        )
    if not isinstance(response['homeworks'], list):
        raise TypeError(
            'Yandex API answer value under homeworks key is not a list '
            'or answer value is not a dict',
        )
    if not response['homeworks']:
        raise EmptyHomeworkException()


def parse_status(homework: ty.Dict[str, ty.Any]) -> str:
    """Check if a homework status was changed."""
    if 'homework_name' not in homework:
        raise WrongHomeworkStructureException(
            f'No "homework_name" in homework: "{homework}"',
        )
    if 'status' not in homework:
        raise WrongHomeworkStructureException(
            f'No "status" in homework: "{homework}"',
        )
    homework_name: list = homework['homework_name']
    if homework['status'] not in HOMEWORK_VERDICTS:
        raise WrongHomeworkStatusException(
            f'Unknown homework status: "{homework["status"]}"',
        )
    verdict: str = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def add_in_error_list_and_send(
    bot: telegram.Bot,
    error: Exception,
    error_list: ty.List[str],
):
    """Adds an error to list of errors if it is not in.

    Sends an error message to a telegram chat using a bot.
    """
    str_error = str(error)
    if str_error not in error_list:
        error_list.append(str_error)
        send_message(bot, str_error)


def main() -> None:
    """Main bot processing logic."""
    try:
        check_tokens()
    except (
            NoEnvValueException,
            WrongTokenException,
    ) as error:
        logger.critical(error)
        exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    error_list: ty.List[str] = []

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            message = parse_status(response['homeworks'][0])
            send_message(bot, message)
            error_list = []
            timestamp = int(time.time()) + 1

        except (
                UnexpectedAPIAnswerException,
                UnexpectedAPIAnswerStatusException,
                WrongHomeworkStatusException,
                WrongHomeworkStructureException,
                RequestFailedException,
                EndpointReachingException,
                TypeError,
        ) as error:
            logger.error(error)
            add_in_error_list_and_send(bot, error, error_list)

        except EmptyHomeworkException:
            logger.debug('No updates')

        except Exception as error:
            logger.critical(f'Сбой в работе программы: {error}')
            raise GeneralProgramException(f'Сбой в работе программы: {error}')

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
