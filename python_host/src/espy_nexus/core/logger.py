import json
import logging
import logging.config
import os
from pathlib import Path

import dotenv

_LOG_DIR_ENV_VAR = "ESPY_NEXUS_LOG_DIR"
_LOG_DIR_DEFAULT = "logs"

logger = logging.getLogger(__name__)


def setup_global_logging(config_path: str = "logging_config.json") -> None:
    """
    Configures the global logging system.

    Requires a .env file with ESPY_NEXUS_LOG_DIR and a logging_config.json file.
    Raises FileNotFoundError if either is missing.
    """
    dotenv.load_dotenv()

    log_dir = os.getenv(_LOG_DIR_ENV_VAR, _LOG_DIR_DEFAULT).strip() or _LOG_DIR_DEFAULT
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(
            f"Logging config file not found: '{config_file}'. "
            "Make sure the file exists before calling setup_global_logging()."
        )

    with config_file.open("r", encoding="utf-8") as f:
        config = json.load(f)

    logging.config.dictConfig(config)
    logger.info("Logging configuration loaded from '%s'.", config_file)
