# OpenClaw Business Worker

AI бизнес-ассистент на базе OpenClaw + Google Sheets + Telegram.

Получает запросы через Telegram-бота, анализирует бизнес-метрики из Google Sheets, формирует выводы на русском языке и отправляет уведомления о критических отклонениях.

## Архитектура

```
Telegram  ←→  OpenClaw Gateway  ←→  Агент (SOUL.md + skills/)  ←→  Python-скрипты  ←→  Google Sheets
```

- **OpenClaw** — оркестратор. Принимает сообщения из Telegram, передаёт агенту, агент вызывает скрипты через exec tool и формирует ответ.
- **Google Sheets** — простая база данных с ежедневными бизнес-показателями.
- **Telegram-бот** — интерфейс пользователя: команды, свободные запросы, уведомления.
- **Эта директория** — OpenClaw workspace (дополнительный агент `business`).

## Структура проекта

```
├── AGENTS.md                        # Правила поведения агента
├── SOUL.md                          # System prompt (персона, формат ответов)
├── TOOLS.md                         # Гайд по инструментам для агента
├── scripts/
│   ├── sheets_reader.py             # Чтение данных из Google Sheets
│   ├── analytics.py                 # Конверсия, допродажи, прогноз, сводка
│   ├── alerts_checker.py            # Проверка критических отклонений
│   ├── seed_data.py                 # Заполнение таблицы тестовыми данными
│   └── requirements.txt             # Python-зависимости
├── skills/
│   └── business-assistant/SKILL.md  # Навык бизнес-аналитики
├── config/
│   ├── thresholds.json              # Пороги алертов
│   └── sheets_structure.md          # Описание структуры таблицы
├── credentials/                     # (gitignored) Service Account key
├── .env                             # Переменные окружения
└── .env.example
```

## Быстрый старт

### 1. Клонируйте репозиторий и установите зависимости

```bash
git clone <repo-url> && cd OpenClawBusinessWorker
pip install -r scripts/requirements.txt
```

### 2. Создайте Service Account для Google Sheets

1. Откройте [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте проект (или выберите существующий)
3. Включите **Google Sheets API** и **Google Drive API**
4. Перейдите в **IAM & Admin → Service Accounts** → создайте аккаунт
5. Создайте JSON-ключ и сохраните его как `credentials/service_account.json`

### 3. Создайте Google Sheets таблицу

Создайте таблицу со следующими колонками (подробнее — `config/sheets_structure.md`):

| Дата       | Выручка | Лиды | Продажи | Конверсия (%) | Допродажи (шт) | Средний чек | План продаж |
|------------|---------|------|---------|---------------|-----------------|-------------|-------------|
| 19.03.2026 | 150000  | 45   | 12      | 26.7          | 4               | 12500       | 2000000     |

Предоставьте Service Account доступ к таблице: **Поделиться → email из JSON-ключа → Редактор**.

Заполните тестовыми данными:
```bash
python3 scripts/seed_data.py
```

### 4. Настройте переменные окружения

```bash
cp .env.example .env
```

Заполните `.env`:
```
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials/service_account.json
GOOGLE_SHEETS_SPREADSHEET_ID=<ID таблицы из URL>
GOOGLE_SHEETS_WORKSHEET_NAME=Лист1
TELEGRAM_BOT_TOKEN=<токен от @BotFather>
```

ID таблицы — это часть URL: `https://docs.google.com/spreadsheets/d/<ВОТ_ЭТОТ_ID>/edit`

### 5. Создайте Telegram-бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`, задайте имя и username
3. Скопируйте полученный токен в `.env` (`TELEGRAM_BOT_TOKEN`)

### 6. Подключите workspace к OpenClaw

Добавьте агента `business` в `.openclaw/openclaw.json`:

```json5
{
  "agents": {
    "list": [
      {
        "id": "business",
        "workspace": "/полный/путь/к/OpenClawBusinessWorker",
        "model": {
          "primary": "openai-codex/gpt-5.4"
        }
      }
    ]
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "botToken": "${TELEGRAM_BOT_TOKEN}",
      "dmPolicy": "pairing"
    }
  },
  "cron": {
    "enabled": true
  }
}
```

### 7. Запустите gateway

```bash
openclaw gateway
```

При первом запуске напишите боту в Telegram — OpenClaw попросит пройти pairing.

## Проверка работоспособности

Перед запуском gateway можно проверить скрипты локально:

```bash
# Данные за сегодня
python3 scripts/sheets_reader.py today

# Данные за 7 дней
python3 scripts/sheets_reader.py range 7

# Сводка по метрикам
python3 scripts/analytics.py summary

# Конверсия за 7 дней
python3 scripts/analytics.py conversion --days 7

# Допродажи за 14 дней
python3 scripts/analytics.py upsells --days 14

# Прогноз на 3 дня
python3 scripts/analytics.py forecast --days 3

# Проверка алертов
python3 scripts/alerts_checker.py
```

Все скрипты возвращают JSON с полем `"status": "ok"` или `"status": "error"`.

## Команды Telegram-бота

| Команда          | Что делает                                                   |
|------------------|--------------------------------------------------------------|
| `/help`          | Список команд и примеры запросов                             |
| `/summary`       | Полная сводка: выручка, продажи, конверсия, план             |
| `/alerts`        | Проверка критических отклонений                              |
| Свободный текст  | Любой вопрос на естественном языке                           |

Примеры свободных запросов:
- «покажи показатели за сегодня»
- «какая конверсия за последние 7 дней»
- «дай прогноз продаж на 3 дня»
- «сколько допродаж было за неделю»
- «есть ли критические отклонения»

## Аналитика

| Метрика                     | Метод расчёта                                             |
|-----------------------------|-----------------------------------------------------------|
| Конверсия                   | `продажи / лиды × 100%` за период + сравнение с прошлым   |
| Допродажи                   | Сумма за период + сравнение с предыдущим                   |
| Прогноз продаж              | Линейная регрессия по данным за последние 14 дней          |
| Критические отклонения      | Сравнение текущих значений с порогами из `thresholds.json` |
| Выполнение плана            | `выручка за месяц / план × 100%`                          |

## Настройка порогов алертов

Файл `config/thresholds.json`:

| Параметр             | Значение | Описание                 |
|----------------------|----------|--------------------------|
| `revenue_drop_pct`   | 20       | Падение выручки, %       |
| `conversion_min_pct` | 15       | Минимальная конверсия, % |
| `upsells_drop_pct`   | 25       | Падение допродаж, %      |
| `plan_behind_pct`    | 15       | Отставание от плана, %   |
| `lookback_days`      | 7        | Период сравнения, дни    |

## Автоматические уведомления (cron)

Ежедневная проверка алертов в 09:00 МСК:

```bash
openclaw cron add \
  --name "daily-alerts" \
  --cron "0 9 * * *" \
  --tz "Europe/Moscow" \
  --session isolated \
  --announce \
  --message "Запусти alerts_checker.py. Если есть алерты — сформируй бизнес-выводы. Если нет — напиши что всё в норме." \
  --channel telegram \
  --to "<chat id>"
```

Chat id можно спросить у самого бота и ввести только цифры