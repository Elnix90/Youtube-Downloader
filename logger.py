import logging
import os
from typing import Any, cast

from CONSTANTS import LOGS_DIR, LOGS_CONSOLE_GLOBALLY, LOGGING_LEVEL_CONSOLE, LOGGING_LEVEL_LOGFILES

from colorama import Fore, Style, init as colorama_init
colorama_init(autoreset=True)





# ─────────────────────────────
# Custom log level: VERBOSE
# ─────────────────────────────
VERBOSE: int = 5
logging.addLevelName(VERBOSE, "VERBOSE")


class CustomLogger(logging.Logger):
    def verbose(self, msg: str, *args: Any, **kwargs: Any) -> None:  # pyright: ignore[reportAny, reportExplicitAny]
        if self.isEnabledFor(VERBOSE):
            self._log(VERBOSE, msg, args, **kwargs)  # pyright: ignore[reportAny]


logging.setLoggerClass(CustomLogger)




# ─────────────────────────────
# Colored formatter
# ─────────────────────────────
class ColoredFormatter(logging.Formatter):
    COLORS: dict[str, str] = {
        "VERBOSE": Fore.LIGHTBLACK_EX,
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record: logging.LogRecord) -> str:  # pyright: ignore[reportImplicitOverride]
        color: str = self.COLORS.get(record.levelname, "")
        reset: str = Style.RESET_ALL
        message: str = super().format(record)
        return f"{color}{message}{reset}"






# ─────────────────────────────
# Setup logger
# ─────────────────────────────
def setup_logger(name: str, to_console: bool = False) -> CustomLogger:
    if LOGS_CONSOLE_GLOBALLY:
        to_console = True

    logger: CustomLogger = cast(CustomLogger, logging.getLogger(name))
    logger.setLevel(level=VERBOSE)

    if not logger.handlers:
        os.makedirs(LOGS_DIR, exist_ok=True)

        # File formatter (plain text, no colors)
        file_formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # File handler
        log_path: str = os.path.join(LOGS_DIR, f"{name}.log")
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
