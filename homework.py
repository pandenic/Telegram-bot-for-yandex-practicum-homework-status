"""Module contains homework checking telegram bot description."""
import os
import sys
import logging
import requests
import json.decoder
import typing as ty

import telegram
import time

from logging import StreamHandler
from dotenv import load_dotenv
from exception import (
    DoesntSendMessagesException,
    GeneralProgramException,
    NoEnvValueException,
    UnexpectedAPIAnswerException,
    UnexpectedAPIAnswerStatusException,
    WrongTokenException,
    WrongHomeworkStatusException,
    WrongAPIAnswerStructureException,
    WrongHomeworkStructureException,
    RequestFailedException,
)

load_dotenv()

PRACTICUM_TOKEN: ty.Optional[str] = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: ty.Optional[str] = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: ty.Optional[str] = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD: ty.Final[int] = 600
ENDPOINT: ty.Final[str] = (
    'https://practicum.yandex.ru/api/user_api/homework_statuses/'
)
HEADERS: ty.Dict[str, str] = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS: ty.Dict[str, str] = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}

ERROR_TOKEN_LIST: ty.Dict[str, str] = {
    'no_practicum_token_answer':
        'PRACTICUM_TOKEN has not been found in env',
    'no_telegram_token_answer':
        'TELEGRAM_TOKEN has not been found in env',
    'no_telegram_chat_id_token_answer':
        'TELEGRAM_CHAT_ID has not been found in env',
    'wrong_telegram_token':
        'TELEGRAM_TOKEN is wrong',
}

handler: logging.StreamHandler = StreamHandler(sys.stdout)
formatter: logging.Formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s',
)
handler.setFormatter(formatter)

logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


def check_tokens() -> None:
    """Check if tokens for a module loaded successfully."""
    if not PRACTICUM_TOKEN:
        raise NoEnvValueException(
            ERROR_TOKEN_LIST['no_practicum_token_answer'],
        )
    if not TELEGRAM_TOKEN:
        raise NoEnvValueException(ERROR_TOKEN_LIST['no_telegram_token_answer'])
    if not TELEGRAM_CHAT_ID:
        raise NoEnvValueException(
            ERROR_TOKEN_LIST['no_telegram_chat_id_token_answer'],
        )
    telegram_token_status: int = requests.get(
        f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe',
    ).status_code
    if telegram_token_status == 401:
        raise WrongTokenException(ERROR_TOKEN_LIST['wrong_telegram_token'])


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
    payload: ty.Dict[str, int] = {'from_date': timestamp}
    try:
        response: requests.Response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params=payload,
        )
    except requests.RequestException as error:
        raise RequestFailedException(
            f'Something went wrong with Yandex API request: {error}',
        )
    if response.status_code != 200:
        raise UnexpectedAPIAnswerStatusException(
            'An API answer status code does not equal 200',
        )
    return response.json()


def check_response(response: ty.Dict) -> None:
    """Check if a Yandex API response is correct."""
    answer_keys: tuple = ('homeworks', 'current_date')
    if 'code' in response:
        raise UnexpectedAPIAnswerException(
            f'Unexpected yandex API answer. Code: "{response["code"]}"',
        )
    if not isinstance(response, dict):
        raise TypeError(
            'Yandex API answer value under homeworks key is not list '
            'or answer value is not dict',
        )
    if 'homeworks' not in response:
        raise UnexpectedAPIAnswerException(
            f'Unexpected yandex API answer. No homeworks key: {response}',
        )
    if not isinstance(response['homeworks'], list):
        raise TypeError(
            'Yandex API answer value under homeworks key is not list '
            'or answer value is not dict',
        )
    if answer_keys != tuple(response.keys()):
        raise WrongAPIAnswerStructureException(
            'Yandex API answer does not meet requirements',
        )


def parse_status(homework: ty.Dict[str, ty.Any]) -> str:
    """Check if a homework status was changed."""
    if 'homework_name' not in homework:
        raise WrongHomeworkStructureException(
            f'No "homework_name" in homework: "{homework}"',
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
    str_error: str = str(error)
    if str_error not in error_list:
        error_list.append(str_error)
        send_message(bot, str_error)


def main():
    """Main bot processing logic."""
    try:
        check_tokens()
    except NoEnvValueException as error:
        logger.critical(error)
        exit()
    except WrongTokenException as error:
        logger.critical(error)
        exit()

    bot: telegram.Bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp: int = int(time.time())
    error_list: ty.List = []

    while True:
        try:
            response: ty.Dict[str, ty.Any] = get_api_answer(timestamp)
            check_response(response)
            if response['homeworks']:
                message: str = parse_status(response['homeworks'][0])
                send_message(bot, message)
                error_list = []
            else:
                logger.debug('No updates')
        except json.decoder.JSONDecodeError as error:
            logger.error(f'Endpoint: "{ENDPOINT}" could not be reached')
            add_in_error_list_and_send(bot, error, error_list)

        except WrongAPIAnswerStructureException as error:
            logger.error('API answer does not meet requirements')
            add_in_error_list_and_send(bot, error, error_list)

        except UnexpectedAPIAnswerException as error:
            logger.error(error)
            add_in_error_list_and_send(bot, error, error_list)

        except TypeError as error:
            logger.error(error)
            add_in_error_list_and_send(bot, error, error_list)

        except UnexpectedAPIAnswerStatusException as error:
            logger.error(error)
            add_in_error_list_and_send(bot, error, error_list)

        except WrongHomeworkStatusException as error:
            logger.error(error)
            add_in_error_list_and_send(bot, error, error_list)

        except WrongHomeworkStructureException as error:
            logger.error(error)
            add_in_error_list_and_send(bot, error, error_list)

        except RequestFailedException as error:
            logger.error(error)
            add_in_error_list_and_send(bot, error, error_list)

        except Exception as error:
            logger.critical(f'Сбой в работе программы: {error}')
            raise GeneralProgramException(f'Сбой в работе программы: {error}')

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
