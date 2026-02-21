from unittest.mock import call, patch

import pytest

from src.retry import with_retry


class TestWithRetry:
    def test_success_on_first_attempt(self):
        result = with_retry(lambda: "ok")
        assert result == "ok"

    def test_no_sleep_on_first_attempt_success(self):
        with patch("src.retry.time.sleep") as mock_sleep:
            with_retry(lambda: "ok")
        mock_sleep.assert_not_called()

    def test_retries_until_success(self):
        attempts = {"n": 0}

        def flaky():
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise ValueError("not yet")
            return "ok"

        with patch("src.retry.time.sleep"):
            result = with_retry(flaky, max_attempts=3)
        assert result == "ok"
        assert attempts["n"] == 3

    def test_raises_after_max_attempts(self):
        def always_fails():
            raise ValueError("always fails")

        with patch("src.retry.time.sleep"):
            with pytest.raises(ValueError, match="always fails"):
                with_retry(always_fails, max_attempts=3)

    def test_exponential_backoff_delays(self):
        def always_fails():
            raise ValueError("fail")

        with patch("src.retry.time.sleep") as mock_sleep:
            with pytest.raises(ValueError):
                with_retry(always_fails, max_attempts=3, base_delay=1.0, backoff=2.0)

        assert mock_sleep.call_args_list == [call(1.0), call(2.0)]

    def test_custom_backoff(self):
        def always_fails():
            raise ValueError("fail")

        with patch("src.retry.time.sleep") as mock_sleep:
            with pytest.raises(ValueError):
                with_retry(always_fails, max_attempts=4, base_delay=0.5, backoff=3.0)

        assert mock_sleep.call_args_list == [call(0.5), call(1.5), call(4.5)]

    def test_max_attempts_one_no_retry(self):
        attempts = {"n": 0}

        def flaky():
            attempts["n"] += 1
            raise ValueError("fail")

        with patch("src.retry.time.sleep"):
            with pytest.raises(ValueError):
                with_retry(flaky, max_attempts=1)
        assert attempts["n"] == 1
