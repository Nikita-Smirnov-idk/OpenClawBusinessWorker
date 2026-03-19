#!/usr/bin/env python3
"""Заполняет Google Sheets тестовыми данными за последние 14 дней."""

import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def main():
    creds_path = PROJECT_ROOT / os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "credentials/service_account.json")
    creds = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
    client = gspread.authorize(creds)

    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
    worksheet_name = os.getenv("GOOGLE_SHEETS_WORKSHEET_NAME", "Лист1")
    spreadsheet = client.open_by_key(spreadsheet_id)
    ws = spreadsheet.worksheet(worksheet_name)

    # Заголовки
    headers = ["Дата", "Выручка", "Лиды", "Продажи", "Конверсия (%)", "Допродажи (шт)", "Средний чек", "План продаж"]

    today = datetime.now().date()
    rows = [headers]
    plan = 2000000

    for i in range(14, -1, -1):
        date = today - timedelta(days=i)
        leads = random.randint(35, 60)
        sales = random.randint(8, 18)
        conversion = round(sales / leads * 100, 1)
        revenue = sales * random.randint(10000, 16000)
        upsells = random.randint(1, 7)
        avg_check = round(revenue / sales) if sales > 0 else 0

        rows.append([
            date.strftime("%d.%m.%Y"),
            revenue,
            leads,
            sales,
            conversion,
            upsells,
            avg_check,
            plan,
        ])

    ws.clear()
    ws.update(values=rows, range_name=f"A1:H{len(rows)}")
    print(f"Записано {len(rows) - 1} строк с данными за {rows[1][0]} – {rows[-1][0]}")


if __name__ == "__main__":
    main()
