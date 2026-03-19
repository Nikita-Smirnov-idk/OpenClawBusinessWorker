#!/usr/bin/env python3
"""Проверка критических отклонений бизнес-метрик."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from logging_utils import get_logger
from sheets_reader import fetch_all, fetch_range, parse_date

PROJECT_ROOT = Path(__file__).resolve().parent.parent
logger = get_logger("alerts_checker")


def load_thresholds():
    """Загружает пороги из config/thresholds.json."""
    path = PROJECT_ROOT / "config" / "thresholds.json"
    logger.debug("Loading thresholds from %s", path)
    with open(path, "r") as f:
        return json.load(f)


def check_alerts():
    """Проверяет все критические отклонения."""
    thresholds = load_thresholds()
    lookback = thresholds.get("lookback_days", 7)
    rows = fetch_range(lookback)
    alerts = []
    logger.info("Checking alerts for lookback_days=%d rows=%d", lookback, len(rows))

    if not rows:
        logger.warning("No data rows for alerts check")
        return {"status": "ok", "alerts": [], "message": "Нет данных для проверки"}

    # Данные за сегодня (последняя запись)
    today = datetime.now().date()
    today_row = None
    for r in rows:
        if parse_date(r.get("date", "")) == today:
            today_row = r
            break

    if today_row is None and rows:
        today_row = rows[-1]
        logger.info("No row for current date, using latest row instead")

    # Средние за период (исключая сегодня)
    hist_rows = [r for r in rows if r != today_row] if today_row else rows
    if not hist_rows:
        hist_rows = rows

    # 1. Падение выручки
    avg_revenue = sum(r["revenue"] for r in hist_rows) / len(hist_rows)
    if today_row and avg_revenue > 0:
        revenue_change = (today_row["revenue"] - avg_revenue) / avg_revenue * 100
        threshold = thresholds.get("revenue_drop_pct", 20)
        if revenue_change < -threshold:
            alerts.append({
                "type": "revenue_drop",
                "severity": "critical",
                "message": f"Выручка сегодня {today_row['revenue']:,.0f} ₽ — падение на {abs(revenue_change):.1f}% относительно среднего ({avg_revenue:,.0f} ₽) за {lookback} дней",
                "current": today_row["revenue"],
                "average": round(avg_revenue),
                "change_pct": round(revenue_change, 1),
            })
            logger.warning("Revenue drop alert triggered: change_pct=%.1f threshold=%s", revenue_change, -threshold)

    # 2. Конверсия ниже порога
    if today_row:
        conv_min = thresholds.get("conversion_min_pct", 15)
        today_conv = today_row.get("conversion", 0)
        avg_conv = sum(r["conversion"] for r in hist_rows) / len(hist_rows) if hist_rows else 0
        if today_conv < conv_min:
            alerts.append({
                "type": "conversion_low",
                "severity": "critical",
                "message": f"Конверсия сегодня {today_conv:.1f}% — ниже минимального порога ({conv_min}%). Среднее за {lookback} дней: {avg_conv:.1f}%",
                "current": today_conv,
                "threshold": conv_min,
                "average": round(avg_conv, 1),
            })
            logger.warning("Conversion alert triggered: current=%.1f threshold=%.1f", today_conv, conv_min)

    # 3. Падение допродаж
    avg_upsells = sum(r["upsells"] for r in hist_rows) / len(hist_rows) if hist_rows else 0
    if today_row and avg_upsells > 0:
        upsells_change = (today_row["upsells"] - avg_upsells) / avg_upsells * 100
        threshold = thresholds.get("upsells_drop_pct", 25)
        if upsells_change < -threshold:
            alerts.append({
                "type": "upsells_drop",
                "severity": "warning",
                "message": f"Допродажи сегодня {int(today_row['upsells'])} шт — падение на {abs(upsells_change):.1f}% относительно среднего ({avg_upsells:.1f} шт)",
                "current": int(today_row["upsells"]),
                "average": round(avg_upsells, 1),
                "change_pct": round(upsells_change, 1),
            })
            logger.warning("Upsells alert triggered: change_pct=%.1f threshold=%s", upsells_change, -threshold)

    # 4. Отставание от плана
    plan = today_row.get("plan", 0) if today_row else 0
    if plan > 0:
        all_rows = fetch_all()
        current_month_revenue = sum(
            r["revenue"] for r in all_rows
            if parse_date(r.get("date", "")) and parse_date(r["date"]).month == today.month and parse_date(r["date"]).year == today.year
        )
        day_of_month = today.day
        expected_pct = day_of_month / 30 * 100
        actual_pct = current_month_revenue / plan * 100
        behind = expected_pct - actual_pct
        threshold = thresholds.get("plan_behind_pct", 15)
        if behind > threshold:
            alerts.append({
                "type": "plan_behind",
                "severity": "warning",
                "message": f"Отставание от плана: выполнено {actual_pct:.1f}% при ожидаемых {expected_pct:.1f}% (отставание {behind:.1f}%)",
                "plan": round(plan),
                "current_revenue": round(current_month_revenue),
                "actual_pct": round(actual_pct, 1),
                "expected_pct": round(expected_pct, 1),
                "behind_pct": round(behind, 1),
            })
            logger.warning("Plan-behind alert triggered: behind_pct=%.1f threshold=%.1f", behind, threshold)

    logger.info("Alerts check complete: alerts_count=%d", len(alerts))
    return {
        "status": "ok",
        "alerts_count": len(alerts),
        "alerts": alerts,
        "checked_at": datetime.now().isoformat(),
    }


def main():
    try:
        logger.info("Running alerts checker")
        result = check_alerts()
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        logger.error("alerts_checker failed: %s", e)
        logger.debug("alerts_checker traceback", exc_info=True)
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
