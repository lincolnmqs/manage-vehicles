import logging
import sys


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG":    "\033[36m",    # ciano
        "INFO":     "\033[32m",    # verde
        "WARNING":  "\033[33m",    # amarelo
        "ERROR":    "\033[31m",    # vermelho
        "CRITICAL": "\033[1;31m",  # vermelho negrito
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        record = logging.makeLogRecord(record.__dict__)
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(level: str = "INFO") -> None:
    use_colors = sys.stdout.isatty()
    formatter_class = ColoredFormatter if use_colors else logging.Formatter

    formatter = formatter_class(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)

    # Silencia logs verbosos de bibliotecas externas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
