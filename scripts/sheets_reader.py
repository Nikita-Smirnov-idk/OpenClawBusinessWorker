#!/usr/bin/env python3
"""Чтение данных из Google Sheets."""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Загружаем .env относительно корня проекта
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

COLUMN_MAP = {
    "Дата": "date",
    "Выручка": "revenue",
    "Лиды": "leads",
    "Продажи": "sales",
    "Конверсия (%)": "conversion",
    "Допродажи (шт)": "upsells",
    "Средний чек": "avg_check",
    "План продаж": "plan",
}


def get_client():
    creds_path = PROJECT_ROOT / os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "credentials/service_account.json")
    creds = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
    return gspread.authorize(creds)


def get_worksheet():
    client = get_client()
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    worksheet_name = os.getenv("GOOGLE_SHEETS_WORKSHEET_NAME", "Лист1")
    spreadsheet = client.open_by_key(spreadsheet_id)
    return spreadsheet.worksheet(worksheet_name)


def parse_date(date_str):
    """Парсит дату в формате DD.MM.YYYY."""
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_number(value):
    """Парсит число, убирая пробелы и заменяя запятую на точку."""
    if not value:
        return 0.0
    cleaned = str(value).replace(" ", "").replace("\u00a0", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def row_to_dict(headers, row):
    """Конвертирует строку таблицы в словарь с английскими ключами."""
    result = {}
    for i, header in enumerate(headers):
        key = COLUMN_MAP.get(header.strip(), header.strip())
        val = row[i] if i < len(row) else ""
        if key == "date":
            result[key] = val.strip() if val else ""
        else:
            result[key] = parse_number(val)
    return result


def fetch_all():
    """Загружает все данные из таблицы."""
    ws = get_worksheet()
    records = ws.get_all_values()
    if len(records) < 2:
        return []
    headers = records[0]
    rows = []
    for row in records[1:]:
        if not row or not row[0].strip():
            continue
        rows.append(row_to_dict(headers, row))
    return rows


def fetch_today():
    """Возвращает данные за сегодня."""
    today = datetime.now().date()
    rows = fetch_all()
    for r in rows:
        if parse_date(r.get("date", "")) == today:
            return r
    return None


def fetch_range(days):
    """Возвращает данные за последние N дней."""
    end = datetime.now().date()
    start = end - timedelta(days=days - 1)
    rows = fetch_all()
    return [r for r in rows if parse_date(r.get("date", "")) and start <= parse_date(r["date"]) <= end]


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Usage: sheets_reader.py [today|range N|all]"}, ensure_ascii=False))
        sys.exit(1)

    command = sys.argv[1].lower()

    try:
        if command == "today":
            data = fetch_today()
            if data is None:
                print(json.dumps({"status": "ok", "message": "Нет данных за сегодня", "data": None}, ensure_ascii=False))
            else:
                print(json.dumps({"status": "ok", "data": data}, ensure_ascii=False))

        elif command == "range":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            data = fetch_range(days)
            print(json.dumps({"status": "ok", "days": days, "count": len(data), "data": data}, ensure_ascii=False))

        elif command == "all":
            data = fetch_all()
            print(json.dumps({"status": "ok", "count": len(data), "data": data}, ensure_ascii=False))

        else:
            print(json.dumps({"status": "error", "message": f"Unknown command: {command}"}, ensure_ascii=False))
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
