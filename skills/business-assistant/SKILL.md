---
name: business-assistant
description: "Анализ бизнес-метрик из Google Sheets: выручка, лиды, продажи, конверсия, допродажи, прогноз. Использовать при запросах о показателях, метриках, аналитике, алертах."
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["python3"]
---

# Бизнес-ассистент

Навык для анализа бизнес-метрик: выручка, лиды, продажи, конверсия, допродажи, средний чек, выполнение плана.

## Когда использовать

Активируется на запросы:
- Показатели, метрики, сводка, статистика
- Конверсия, продажи, выручка, лиды
- Допродажи, средний чек
- Прогноз, план
- Алерты, отклонения, проблемы

## Команды

### Чтение данных из Google Sheets
```bash
python3 scripts/sheets_reader.py today        # данные за сегодня
python3 scripts/sheets_reader.py range 7      # данные за последние 7 дней
python3 scripts/sheets_reader.py all           # все данные
```

### Аналитика
```bash
python3 scripts/analytics.py conversion --days 7   # конверсия за 7 дней
python3 scripts/analytics.py upsells --days 7      # допродажи за 7 дней
python3 scripts/analytics.py forecast --days 3     # прогноз на 3 дня
python3 scripts/analytics.py summary               # общая сводка
```

### Проверка алертов
```bash
python3 scripts/alerts_checker.py              # проверка критических отклонений
```

## Маппинг запросов → скрипты

| Ключевые слова | Скрипт |
|----------------|--------|
| сегодня, показатели, данные | `python3 scripts/sheets_reader.py today` |
| за N дней, неделя, период | `python3 scripts/sheets_reader.py range N` |
| конверсия | `python3 scripts/analytics.py conversion --days N` |
| допродажи | `python3 scripts/analytics.py upsells --days N` |
| прогноз | `python3 scripts/analytics.py forecast --days N` |
| сводка, итоги, summary | `python3 scripts/analytics.py summary` |
| алерты, проблемы, отклонения | `python3 scripts/alerts_checker.py` |

## Формат ответа

- Отвечай на русском языке
- Используй ₽ для денежных сумм, % для процентов
- Разделяй тысячи пробелами (150 000 ₽)
- Давай бизнес-вывод, не просто числа
- Если есть отклонения — предложи рекомендацию
