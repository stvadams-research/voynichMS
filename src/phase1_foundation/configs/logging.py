import logging

from rich.logging import RichHandler


def setup_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """
    Configure logging for the Voynich Foundation project.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to a log file. If provided, logs will be written to this file
                  in addition to the console.
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")

    handlers: list[logging.Handler] = [
        RichHandler(rich_tracebacks=True, markup=True)
    ]

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        handlers.append(file_handler)

    logging.basicConfig(
        level=numeric_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=handlers,
    )

    # Set third-party loggers to WARNING to avoid noise
    logging.getLogger("alembic").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
