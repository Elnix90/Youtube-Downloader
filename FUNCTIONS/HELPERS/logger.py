"""
Loger module, handles all logs for the entire project,
adds a custom logs level: VERBOSE, at priority 5
to logs very low impact things
"""

import logging
from pathlib import Path
from typing import Any, cast, override

from colorama import Fore, Style
from colorama import init as colorama_init

from CONSTANTS import (
    LOGGING_LEVEL_CONSOLE,
    LOGGING_LEVEL_LOGFILES,
    LOGS_CONSOLE_GLOBALLY,
    LOGS_DIR,
)

colorama_init(autoreset=True)


# ─────────────────────────────
# Custom log level: VERBOSE
# ─────────────────────────────
VERBOSE: int = 5
logging.addLevelName(VERBOSE, "VERBOSE")


class CustomLogger(logging.Logger):
    """Custom logger to allow the verbose level to be added safely"""

    def verbose(
        self,
        msg: str,
        *args: Any,  # pyright: ignore[reportAny, reportExplicitAny]
        **kwargs: Any,  # pyright: ignore[reportAny, reportExplicitAny]
    ) -> None:
        """
        Vebose level of logging, behaves like any log level,
        but have a priority of 5
        """
        if self.isEnabledFor(VERBOSE):
            self._log(
                VERBOSE, msg, args, **kwargs  # pyright: ignore[reportAny]
            )


logging.setLoggerClass(CustomLogger)


# ─────────────────────────────
# Colored formatter
# ─────────────────────────────
class ColoredFormatter(logging.Formatter):
    """
    Colored formatter from colorama
    """

    COLORS: dict[str, str] = {
        "VERBOSE": Fore.LIGHTBLACK_EX,
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    @override
    def format(self, record: logging.LogRecord) -> str:
        color: str = self.COLORS.get(record.levelname, "")
        reset: str = Style.RESET_ALL
        message: str = super().format(record)
        return f"{color}{message}{reset}"


# ─────────────────────────────
# Setup logger
# ─────────────────────────────
def setup_logger(name: str, to_console: bool = False) -> CustomLogger:
    """
    Creates the logger object that will be used to summon logs
    """
    if LOGS_CONSOLE_GLOBALLY:
        to_console = True

    logger: CustomLogger = cast(CustomLogger, logging.getLogger(name))
    logger.setLevel(level=VERBOSE)

    if not logger.handlers:
        LOGS_DIR.mkdir(exist_ok=True)

        # File formatter (plain text, no colors)
        file_formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File handler
        log_path: Path = Path(LOGS_DIR / name).with_suffix(".log")
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(LOGGING_LEVEL_LOGFILES)
        fh.setFormatter(file_formatter)
        logger.addHandler(fh)

        # Console handler (with colors)
        if to_console:
            console_formatter = ColoredFormatter(
                fmt="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            ch = logging.StreamHandler()
            ch.setLevel(LOGGING_LEVEL_CONSOLE)
            ch.setFormatter(console_formatter)
            logger.addHandler(ch)

    return logger
