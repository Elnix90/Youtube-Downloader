import logging
import os
from typing import Any

from CONSTANTS import LOGS_DIR, LOGS_CONSOLE_GLOBALLY,LOGGING_LEVEL


from colorama import Fore, Style, init as colorama_init
colorama_init(autoreset=True)

# Colored formatter
class ColoredFormatter(logging.Formatter):
    COLORS: dict[str, str] = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }

    def format(self, record: Any) -> str:  # pyright: ignore[reportImplicitOverride, reportAny, reportExplicitAny]
        color = self.COLORS.get(record.levelname, '')  # pyright: ignore[reportAny]
        reset = Style.RESET_ALL

        message = super().format(record)  # pyright: ignore[reportAny]
        return f"{color}{message}{reset}"


def setup_logger(name: str, to_console: bool = False) -> logging.Logger:
    if LOGS_CONSOLE_GLOBALLY:
        to_console = True

    logger = logging.getLogger(name)
    logger.setLevel(LOGGING_LEVEL)

    if not logger.handlers:
        os.makedirs(LOGS_DIR, exist_ok=True)

        # File formatter (no colors)
        file_formatter = logging.Formatter(
            fmt='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # File handler
        log_path = os.path.join(LOGS_DIR, f"{name}.log")
        fh = logging.FileHandler(log_path, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(file_formatter)
        logger.addHandler(fh)

        # Console handler (with colors)
        if to_console:
            console_formatter = ColoredFormatter(
                fmt='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(console_formatter)
            logger.addHandler(ch)

    return logger
