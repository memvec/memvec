import json
import logging
import sys
from logging.config import dictConfig
from typing import Any, Dict

from app.core.config import settings


class ExtraAwareFormatter(logging.Formatter):
    STANDARD_ATTRS = {
        'name', 'msg', 'args', 'levelname', 'levelno',
        'pathname', 'filename', 'module', 'exc_info',
        'exc_text', 'stack_info', 'lineno', 'funcName',
        'created', 'msecs', 'relativeCreated',
        'thread', 'threadName', 'processName', 'process',
    }

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: str = '%',
        *,
        include_extra: bool = False,
    ) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)

        if not self.include_extra:
            return base

        extra = {
            k: v
            for k, v in record.__dict__.items()
            if k not in self.STANDARD_ATTRS
        }

        if not extra:
            return base

        return f'{base} | extra={json.dumps(extra, default=str)}'


class JsonFormatter(logging.Formatter):
    STANDARD_ATTRS = ExtraAwareFormatter.STANDARD_ATTRS

    def __init__(self, *, include_extra: bool = False) -> None:
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        data: Dict[str, Any] = {
            'ts': self.formatTime(record, '%Y-%m-%dT%H:%M:%S'),
            'level': record.levelname,
            'logger': record.name,
            'msg': record.getMessage(),
            'module': record.module,
            'line': record.lineno,
        }

        if record.exc_info:
            # This includes stack trace text in JSON logs.
            data['exc_info'] = self.formatException(record.exc_info)

        if self.include_extra:
            extra = {
                k: v
                for k, v in record.__dict__.items()
                if k not in self.STANDARD_ATTRS
            }
            if extra:
                data['extra'] = extra

        return json.dumps(data, default=str)


def setup_logging() -> None:
    log_level = settings.LOG_LEVEL.upper()

    # Decide when to include extras:
    # - You can key this off ENV, DEBUG flag, or log level.
    # Here: include extras only when log level is DEBUG.
    include_extra = log_level == 'INFO'

    if settings.LOG_FORMAT == 'json':
        formatter = {
            '()': 'app.core.logging_config.JsonFormatter',
            'include_extra': include_extra,
        }
    else:
        formatter = {
            '()': 'app.core.logging_config.ExtraAwareFormatter',
            'format': '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            'include_extra': include_extra,
        }

    handlers = {
        'default': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': sys.stdout,
        }
    }

    loggers = {
        '': {  # root logger
            'handlers': ['default'],
            'level': log_level,
        },
        'uvicorn.error': {
            'level': log_level,
        },
        'uvicorn.access': {
            'level': log_level,
        },
    }

    if not settings.LOG_SQLALCHEMY:
        loggers['sqlalchemy.engine'] = {'level': 'WARNING'}

    dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': formatter,
        },
        'handlers': handlers,
        'loggers': loggers,
    })
