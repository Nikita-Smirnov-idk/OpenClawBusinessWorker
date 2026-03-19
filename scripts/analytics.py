#!/usr/bin/env python3
"""Аналитика бизнес-метрик: конверсия, допродажи, прогноз, сводка."""

import json
import sys
from datetime import datetime, timedelta

from sheets_reader import fetch_all, fetch_range, parse_date


def calc_conversion(days=7):
    """Расчёт конверсии за N дней."""
    rows = fetch_range(days)
    if not rows:
        return {"status": "ok", "message": f"Нет данных за последние {days} дней"}

    total_leads = sum(r["leads"] for r in rows)
    total_sales = sum(r["sales"] for r in rows)
    conversion = (total_sales / total_leads * 100) if total_leads > 0 else 0

    # Сравнение с предыдущим периодом
    end = datetime.now().date() - timedelta(days=days)
    start = end - timedelta(days=days - 1)
    all_rows = fetch_all()
    prev_rows = [r for r in all_rows if parse_date(r.get("date", "")) and start <= parse_date(r["date"]) <= end]

    prev_conversion = None
    if prev_rows:
        prev_leads = sum(r["leads"] for r in prev_rows)
        prev_sales = sum(r["sales"] for r in prev_rows)
        prev_conversion = (prev_sales / prev_leads * 100) if prev_leads > 0 else 0

    return {
        "status": "ok",
        "days": days,
        "total_leads": total_leads,
        "total_sales": total_sales,
        "conversion_pct": round(conversion, 1),
        "prev_period_conversion_pct": round(prev_conversion, 1) if prev_conversion is not None else None,
        "change_pct": round(conversion - prev_conversion, 1) if prev_conversion is not None else None,
    }


def calc_upsells(days=7):
    """Расчёт допродаж за N дней."""
    rows = fetch_range(days)
    if not rows:
        return {"status": "ok", "message": f"Нет данных за последние {days} дней"}

    total_upsells = sum(r["upsells"] for r in rows)
    avg_daily = total_upsells / len(rows) if rows else 0

    # Сравнение с предыдущим периодом
    end = datetime.now().date() - timedelta(days=days)
    start = end - timedelta(days=days - 1)
    all_rows = fetch_all()
    prev_rows = [r for r in all_rows if parse_date(r.get("date", "")) and start <= parse_date(r["date"]) <= end]

    prev_total = None
    if prev_rows:
        prev_total = sum(r["upsells"] for r in prev_rows)

    change_pct = None
    if prev_total is not None and prev_total > 0:
        change_pct = round((total_upsells - prev_total) / prev_total * 100, 1)

    return {
        "status": "ok",
        "days": days,
        "total_upsells": int(total_upsells),
        "avg_daily": round(avg_daily, 1),
        "prev_period_total": int(prev_total) if prev_total is not None else None,
        "change_pct": change_pct,
    }


def calc_forecast(days=3):
    """Прогноз продаж на N дней (линейный тренд + среднее)."""
    lookback = 14
    rows = fetch_range(lookback)
    if len(rows) < 3:
        return {"status": "ok", "message": "Недостаточно данных для прогноза (нужно минимум 3 дня)"}

    revenues = [r["revenue"] for r in rows]
    n = len(revenues)

    # Линейная регрессия: y = a + b*x
    x_mean = (n - 1) / 2
    y_mean = sum(revenues) / n
    numerator = sum((i - x_mean) * (revenues[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    b = numerator / denominator if denominator != 0 else 0
    a = y_mean - b * x_mean

    # Прогноз на следующие days дней
    forecast = []
    today = datetime.now().date()
    for d in range(1, days + 1):
        x = n - 1 + d
        predicted = max(a + b * x, 0)
        forecast_date = today + timedelta(days=d)
        forecast.append({
            "date": forecast_date.strftime("%d.%m.%Y"),
            "predicted_revenue": round(predicted),
        })

    total_forecast = sum(f["predicted_revenue"] for f in forecast)
    avg_recent = y_mean

    # Проверяем план
    plan = rows[-1].get("plan", 0) if rows else 0
    today_day = today.day
    days_in_month = 30
    days_left = days_in_month - today_day
    current_month_revenue = sum(r["revenue"] for r in rows if parse_date(r["date"]).month == today.month)
    projected_month = current_month_revenue + total_forecast + avg_recent * max(0, days_left - days)

    return {
        "status": "ok",
        "forecast_days": days,
        "based_on_days": n,
        "trend_daily": round(b, 0),
        "avg_daily_revenue": round(avg_recent),
        "forecast": forecast,
        "total_forecast": round(total_forecast),
        "monthly_plan": round(plan),
        "current_month_revenue": round(current_month_revenue),
        "projected_month_total": round(projected_month),
    }


def calc_summary():
    """Общая сводка по метрикам за последние 7 дней."""
    rows = fetch_range(7)
    if not rows:
        return {"status": "ok", "message": "Нет данных за последние 7 дней"}

    total_revenue = sum(r["revenue"] for r in rows)
    total_sales = sum(r["sales"] for r in rows)
    total_leads = sum(r["leads"] for r in rows)
    total_upsells = sum(r["upsells"] for r in rows)
    conversion = (total_sales / total_leads * 100) if total_leads > 0 else 0
    avg_check = (total_revenue / total_sales) if total_sales > 0 else 0

    plan = rows[-1].get("plan", 0) if rows else 0
    today = datetime.now().date()
    all_rows = fetch_all()
    current_month_revenue = sum(
        r["revenue"] for r in all_rows
        if parse_date(r.get("date", "")) and parse_date(r["date"]).month == today.month and parse_date(r["date"]).year == today.year
    )
    plan_pct = (current_month_revenue / plan * 100) if plan > 0 else 0

    dates = [parse_date(r["date"]) for r in rows if parse_date(r.get("date", ""))]
    date_from = min(dates).strftime("%d.%m") if dates else "?"
    date_to = max(dates).strftime("%d.%m.%Y") if dates else "?"

    return {
        "status": "ok",
        "period": f"{date_from} – {date_to}",
        "total_revenue": round(total_revenue),
        "total_sales": int(total_sales),
        "total_leads": int(total_leads),
        "conversion_pct": round(conversion, 1),
        "total_upsells": int(total_upsells),
        "avg_check": round(avg_check),
        "monthly_plan": round(plan),
        "current_month_revenue": round(current_month_revenue),
        "plan_completion_pct": round(plan_pct, 1),
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Usage: analytics.py [conversion|upsells|forecast|summary] [--days N]"}, ensure_ascii=False))
        sys.exit(1)

    command = sys.argv[1].lower()
    days = 7
    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            days = int(sys.argv[idx + 1])

    try:
        if command == "conversion":
            result = calc_conversion(days)
        elif command == "upsells":
            result = calc_upsells(days)
        elif command == "forecast":
            result = calc_forecast(days)
        elif command == "summary":
            result = calc_summary()
        else:
            result = {"status": "error", "message": f"Unknown command: {command}"}

        print(json.dumps(result, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
