#!/usr/bin/env python3
"""Shared logging setup for business worker scripts."""

import logging
import os
import sys

def _resolve_level(default_level):
    level_name = os.getenv("BUSINESS_WORKER_LOG_LEVEL", os.getenv("LOG_LEVEL", default_level)).upper()
    return getattr(logging, level_name, logging.INFO)


def _resolve_format():
    return os.getenv(
        "BUSINESS_WORKER_LOG_FORMAT",
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def get_logger(name, default_level="INFO"):
    logger_name = f"business_worker.{name}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(_resolve_level(default_level))
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(_resolve_format()))
        logger.addHandler(handler)

    return logger
