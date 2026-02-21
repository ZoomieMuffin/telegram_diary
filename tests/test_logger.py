import logging

import pytest

from src.logger import setup_logger


@pytest.fixture(autouse=True)
def clean_handlers():
    """テスト間でロガーのハンドラをリセットする。"""
    yield
    logger = logging.getLogger("telegram_diary")
    logger.handlers.clear()


class TestSetupLogger:
    def test_returns_logger(self, tmp_path):
        logger = setup_logger(logs_dir=tmp_path)
        assert isinstance(logger, logging.Logger)

    def test_creates_log_file(self, tmp_path):
        logger = setup_logger(logs_dir=tmp_path)
        logger.info("test message")
        log_files = list(tmp_path.glob("*.log"))
        assert len(log_files) == 1

    def test_info_written_to_file(self, tmp_path):
        logger = setup_logger(logs_dir=tmp_path)
        logger.info("hello info")
        content = next(tmp_path.glob("*.log")).read_text()
        assert "hello info" in content

    def test_error_written_to_file(self, tmp_path):
        logger = setup_logger(logs_dir=tmp_path)
        logger.error("something went wrong")
        content = next(tmp_path.glob("*.log")).read_text()
        assert "something went wrong" in content

    def test_log_filename_is_date(self, tmp_path):
        setup_logger(logs_dir=tmp_path)
        log_files = list(tmp_path.glob("*.log"))
        assert len(log_files) == 1
        # ファイル名が YYYY-MM-DD.log 形式
        import re
        assert re.match(r"\d{4}-\d{2}-\d{2}\.log", log_files[0].name)

    def test_creates_logs_dir_if_missing(self, tmp_path):
        logs_dir = tmp_path / "new_logs"
        setup_logger(logs_dir=logs_dir)
        assert logs_dir.exists()

    def test_level_is_info(self, tmp_path):
        logger = setup_logger(logs_dir=tmp_path)
        assert logger.level == logging.INFO
