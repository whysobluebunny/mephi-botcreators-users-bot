# mephi-botcreators-users-bot

## Запуск через Docker

1. Создайте файл `.env` по образцу `.env.example` и укажите действительный `BOT_TOKEN`.
2. Соберите образ:

   ```bash
   docker build -t mephi-bot .
   ```

3. Запустите контейнер:

   ```bash
   docker run --rm --env-file .env mephi-bot
   ```

   Бот стартует и будет отвечать на команду `/start`.

## Запуск через docker-compose (опционально)

Вместо ручного `build`/`run` можно использовать docker-compose:

```bash
docker compose up --build
```

Сервис `bot` возьмёт переменные из `.env` и будет перезапускаться автоматически.
