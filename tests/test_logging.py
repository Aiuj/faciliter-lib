import os
import logging
from pathlib import Path

from core_lib import setup_logging, get_module_logger, get_last_logging_config

def test_setup_logging_basic(tmp_path: Path):
    log_file = tmp_path / "test.log"
    logger = setup_logging(level="DEBUG", file_logging=True, file_path=str(log_file), force=True)
    logger.debug("debug message")
    logger.info("info message")

    # Ensure config captured
    cfg = get_last_logging_config()
    assert cfg["file_logging"] is True
    assert cfg["file_path"].endswith("test.log")

    # Flush handlers
    for h in logging.getLogger().handlers:
        try:
            h.flush()
        except Exception:
            pass

    assert log_file.exists(), "Log file should be created when file_logging enabled"
    content = log_file.read_text(encoding="utf-8")
    assert "info message" in content


def test_get_module_logger_does_not_initialize_again():
    # Calling get_module_logger should not reconfigure handlers
    before = len(logging.getLogger().handlers)
    _ = get_module_logger()
    after = len(logging.getLogger().handlers)
    assert after == before
