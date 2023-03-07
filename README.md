# Yandex Practicum homework telegram bot

## Description
The telegram bot provides a status of the last homework has been sended for reviewing.

## Requirements
Python 3.9
Python-telegram-bot 13.7
Python-dotenv 0.19

## Startup

Preparations consist of running venv:
```
python3 -m venv venv
```
...and installing req using bash:
```
pip install -r requirements.txt
```

Write a command below to start the bot:

```bash
python3 homework.py
```

When the bot has started it will send you a message in bash like this:

```
2023-01-01 07:30:30,705 [DEBUG] No updates
```

Thats mean the bot is working correctly.

## Errors and how-to handle

If some issues will appear it will print you an error text in bash.

Token issues:
- **"PRACTICUM_TOKEN has not been found in env"** : Program can't find a practicum API token in .env.
- **"TELEGRAM_TOKEN has not been found in env"** :  Program can't find a telegram bot API token in .env.
- **"TELEGRAM_CHAT_ID has not been found in env"** :  Program can't find a telegram chat id token in .env.
- **"TELEGRAM_TOKEN is wrong"** : Program can't get access to telegram bot API. Probably mistake in token string.

Sending a message to chat:
- **"Bot has not sent a message: ..."** : Program can't send a message in chat. Probably wrong TELEGRAM_CHAT_ID.

Yandex API issues:
- **"Something went wrong with Yandex API request: {error}"** : Something went wrong with Yandex API. Look through Yandex API docs.
- **"An API answer status code does not equal 200"** : Yandex API does answer in unexpected way with a status code differs from 200.

Yandex API response issues:
- **"Unexpected yandex API answer. Code: ..."** : Yandex API consider something happened and throw an error with certain code.
- **"Yandex API answer value under homeworks key is not list..."** : Yandex API response type is not appropriate.
- **"Unexpected yandex API answer. No homeworks key: ..."** : No homeworks key inside.
- **"Unexpected yandex API answer. No current_time key: ..."** : No current_time key inside.

Homework status:
- **"No 'homework_name' in homework:"** : Yandex API answer doesn't contain 'homework_name' key in answer.
- **"Unknown homework status: ..."** : Yandex API provide unexpected homework status.
