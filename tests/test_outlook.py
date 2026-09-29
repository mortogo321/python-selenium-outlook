"""Unit tests for outlook.py (browser fully mocked — no real Chrome needed)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from selenium.common.exceptions import TimeoutException

import outlook


def test_get_chrome_options_headless_by_default() -> None:
    options = outlook.get_chrome_options()
    args = options.arguments
    assert "--headless=new" in args
    assert "--window-size=1920,1080" in args
    assert any(a.startswith("user-agent=") for a in args)


def test_get_chrome_options_headed() -> None:
    options = outlook.get_chrome_options(headless=False)
    assert "--headless=new" not in options.arguments


def test_get_chrome_options_drops_insecure_flags() -> None:
    options = outlook.get_chrome_options()
    args = options.arguments
    assert "--disable-web-security" not in args
    assert "--allow-running-insecure-content" not in args
    assert "--disable-blink-features" not in args  # bare flag without value


def test_get_chrome_options_user_agent_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OUTLOOK_USER_AGENT", "TestAgent/1.0")
    options = outlook.get_chrome_options()
    assert "user-agent=TestAgent/1.0" in options.arguments


def test_get_credentials_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OUTLOOK_EMAIL", "user@outlook.com")
    monkeypatch.setenv("OUTLOOK_PASSWORD", "s3cret")
    assert outlook.get_credentials() == ("user@outlook.com", "s3cret")


def test_get_credentials_empty_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OUTLOOK_EMAIL", "")
    monkeypatch.setenv("OUTLOOK_PASSWORD", "")
    with (
        patch("outlook.input", return_value=""),
        patch("outlook.getpass.getpass", return_value=""),
    ):
        with pytest.raises(ValueError):
            outlook.get_credentials()


def test_get_credentials_prompts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OUTLOOK_EMAIL", raising=False)
    monkeypatch.delenv("OUTLOOK_PASSWORD", raising=False)
    with (
        patch("outlook.input", return_value="prompted@outlook.com"),
        patch("outlook.getpass.getpass", return_value="prompted-pw"),
    ):
        assert outlook.get_credentials() == ("prompted@outlook.com", "prompted-pw")


def test_human_delay_uses_random_window() -> None:
    with (
        patch("outlook.random.uniform", return_value=1.23) as mock_uniform,
        patch("outlook.time.sleep") as mock_sleep,
    ):
        outlook.human_delay()
        mock_uniform.assert_called_once_with(0.5, 2.5)
        mock_sleep.assert_called_once_with(1.23)


def _mock_wait(*until_returns: Any, side_effect: Any = None) -> MagicMock:
    wait = MagicMock()
    if side_effect is not None:
        wait.until.side_effect = side_effect
    else:
        wait.until.side_effect = list(until_returns)
    return wait


def test_login_submits_form() -> None:
    driver = MagicMock()
    email_field, next_btn, pw_field, sign_in_btn = (
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
    )
    with patch(
        "outlook.WebDriverWait",
        return_value=_mock_wait(email_field, next_btn, pw_field, sign_in_btn),
    ):
        with patch("outlook.human_delay"):
            outlook.login(driver, "user@outlook.com", "pw", timeout=5)
    driver.get.assert_called_once_with(outlook.LOGIN_URL)
    email_field.send_keys.assert_called_once_with("user@outlook.com")
    next_btn.click.assert_called_once_with()
    pw_field.send_keys.assert_called_once_with("pw")
    sign_in_btn.click.assert_called_once_with()


def test_dismiss_stay_signed_in_clicks_yes() -> None:
    driver = MagicMock()
    yes_btn = MagicMock()
    with patch("outlook.WebDriverWait", return_value=_mock_wait(MagicMock(), yes_btn)):
        assert outlook.dismiss_stay_signed_in(driver, timeout=5) is True
    yes_btn.click.assert_called_once_with()


def test_dismiss_stay_signed_in_absent() -> None:
    driver = MagicMock()
    with patch(
        "outlook.WebDriverWait", return_value=_mock_wait(side_effect=TimeoutException())
    ):
        assert outlook.dismiss_stay_signed_in(driver, timeout=5) is False


def test_open_inbox_success() -> None:
    driver = MagicMock()
    link = MagicMock()
    with patch("outlook.WebDriverWait", return_value=_mock_wait(link)):
        assert outlook.open_inbox(driver, timeout=5) is True
    link.click.assert_called_once_with()


def test_open_inbox_timeout() -> None:
    driver = MagicMock()
    with patch(
        "outlook.WebDriverWait", return_value=_mock_wait(side_effect=TimeoutException())
    ):
        assert outlook.open_inbox(driver, timeout=5) is False


def test_list_inbox_subjects() -> None:
    driver = MagicMock()
    mail_list = MagicMock()
    titles = [MagicMock(text="Hello"), MagicMock(text="World")]
    mail_list.find_elements.return_value = titles
    with patch("outlook.WebDriverWait", return_value=_mock_wait(mail_list)):
        assert outlook.list_inbox_subjects(driver, timeout=5) == ["Hello", "World"]
    mail_list.find_elements.assert_called_once()


def test_list_inbox_subjects_timeout_returns_empty() -> None:
    driver = MagicMock()
    with patch(
        "outlook.WebDriverWait", return_value=_mock_wait(side_effect=TimeoutException())
    ):
        assert outlook.list_inbox_subjects(driver, timeout=5) == []


def test_run_full_flow_quits_driver() -> None:
    driver = MagicMock()
    with (
        patch("outlook.create_driver", return_value=driver),
        patch("outlook.login") as mock_login,
        patch("outlook.dismiss_stay_signed_in", return_value=True),
        patch("outlook.open_inbox", return_value=True),
        patch("outlook.list_inbox_subjects", return_value=["A"]) as mock_list,
    ):
        assert outlook.run("u", "p", headless=True, timeout=5) == ["A"]
        mock_login.assert_called_once_with(driver, "u", "p", timeout=5)
        mock_list.assert_called_once_with(driver, timeout=5)
    driver.quit.assert_called_once_with()


def test_run_quits_driver_on_error() -> None:
    driver = MagicMock()
    with (
        patch("outlook.create_driver", return_value=driver),
        patch("outlook.login", side_effect=RuntimeError("boom")),
    ):
        with pytest.raises(RuntimeError):
            outlook.run("u", "p")
    driver.quit.assert_called_once_with()


def test_headless_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OUTLOOK_HEADLESS", "0")
    assert outlook._headless_from_env() is False
    monkeypatch.setenv("OUTLOOK_HEADLESS", "false")
    assert outlook._headless_from_env() is False
    monkeypatch.setenv("OUTLOOK_HEADLESS", "1")
    assert outlook._headless_from_env() is True


def test_main_success() -> None:
    with (
        patch("outlook.get_credentials", return_value=("u", "p")),
        patch("outlook.run", return_value=["A"]),
    ):
        assert outlook.main() == 0


def test_main_run_error_returns_1() -> None:
    with (
        patch("outlook.get_credentials", return_value=("u", "p")),
        patch("outlook.run", side_effect=RuntimeError("boom")),
    ):
        assert outlook.main() == 1


def test_main_empty_credentials_returns_2() -> None:
    with patch("outlook.get_credentials", side_effect=ValueError("empty")):
        assert outlook.main() == 2
