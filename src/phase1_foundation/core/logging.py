import json
import logging
import sys
from pathlib import Path
from typing import Any

from phase1_foundation.runs.manager import RunManager


class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings.
    Includes contextual metadata like run_id.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineNo": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        # Add contextual metadata from RunManager
        try:
            run = RunManager.get_current_run()
            log_record["run_id"] = str(run.run_id)
        except (RuntimeError, AttributeError):
            log_record["run_id"] = None

        # Add any extra fields
        if hasattr(record, "extra_fields"):
            log_record.update(record.extra_fields)

        return json.dumps(log_record)

def setup_logging(level: int = logging.INFO, log_file: str | Path | None = None, json_format: bool = False):
    """
    Standardized logging configuration for the Voynich MS project.
    
    Args:
        level: Logging level (default INFO)
        log_file: Optional path to a log file
        json_format: Whether to use JSON formatting (default False)
    """
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if json_format:
        console_handler.setFormatter(JsonFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))

    handlers = [console_handler]

    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        if json_format:
            file_handler.setFormatter(JsonFormatter())
        handlers.append(file_handler)

    # Check for active run to auto-log to run directory (always use JSON for execution.log)
    try:
        run = RunManager.get_current_run()
        run_log = Path("runs") / str(run.run_id) / "execution.jsonl"
        run_log.parent.mkdir(parents=True, exist_ok=True)
        run_handler = logging.FileHandler(run_log)
        run_handler.setFormatter(JsonFormatter())
        handlers.append(run_handler)
    except (RuntimeError, AttributeError):
        pass

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    for handler in handlers:
        root_logger.addHandler(handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)
