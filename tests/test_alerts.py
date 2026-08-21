from urllib.error import URLError
from unittest.mock import MagicMock, patch

import pytest

from src.dqo.alerts import (
    AlertEvent,
    AlertRouter,
    ConsoleAlertChannel,
    FileAlertChannel,
    WebhookAlertChannel,
)
from src.dqo.models import CheckResult, CheckStatus, RunSummary, Severity
from datetime import datetime, timezone


def _failed_summary() -> RunSummary:
    return RunSummary(
        contract_name="orders",
        contract_version="1.0",
        run_id="run-alert-1",
        started_at=datetime(2026, 7, 14, 10, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 7, 14, 10, 1, tzinfo=timezone.utc),
        results=(
            CheckResult(
                contract_name="orders",
                check_type="nulls",
                status=CheckStatus.FAILED,
                message="missing order_total",
                severity=Severity.CRITICAL,
            ),
        ),
    )


def test_alert_router_writes_console_and_file(tmp_path, capsys) -> None:
    alert_file = tmp_path / "alerts.jsonl"
    router = AlertRouter([ConsoleAlertChannel(), FileAlertChannel(alert_file)])
    events = router.route(_failed_summary())

    assert len(events) == 1
    captured = capsys.readouterr()
    assert "CRITICAL" in captured.out
    assert alert_file.read_text(encoding="utf-8").strip()


def test_webhook_alert_channel_posts_json_payload() -> None:
    channel = WebhookAlertChannel("https://example.test/hook")
    event = AlertEvent(
        contract_name="orders",
        run_id="run-alert-1",
        check_type="nulls",
        severity=Severity.CRITICAL,
        message="missing order_total",
    )

    with patch("src.dqo.alerts.request.urlopen") as urlopen:
        urlopen.return_value.__enter__ = MagicMock(return_value=MagicMock())
        urlopen.return_value.__exit__ = MagicMock(return_value=False)
        channel.send(event)

    request_obj = urlopen.call_args.args[0]
    assert request_obj.full_url == "https://example.test/hook"
    assert request_obj.headers["Content-type"] == "application/json"
    assert b'"contract_name": "orders"' in request_obj.data
    assert b'"check_type": "nulls"' in request_obj.data
    assert b'"severity": "critical"' in request_obj.data


def test_webhook_alert_channel_raises_on_delivery_failure() -> None:
    channel = WebhookAlertChannel("https://example.test/hook")
    event = AlertEvent(
        contract_name="orders",
        run_id="run-alert-1",
        check_type="nulls",
        severity=Severity.CRITICAL,
        message="missing order_total",
    )

    with patch("src.dqo.alerts.request.urlopen", side_effect=URLError("network down")):
        with pytest.raises(RuntimeError, match="webhook delivery failed"):
            channel.send(event)


def test_alert_router_delivers_failed_checks_to_webhook() -> None:
    router = AlertRouter([WebhookAlertChannel("https://example.test/hook")])

    with patch("src.dqo.alerts.request.urlopen") as urlopen:
        urlopen.return_value.__enter__ = MagicMock(return_value=MagicMock())
        urlopen.return_value.__exit__ = MagicMock(return_value=False)
        events = router.route(_failed_summary())

    assert len(events) == 1
    assert urlopen.call_count == 1
    request_obj = urlopen.call_args.args[0]
    assert b"missing order_total" in request_obj.data


def test_alert_router_skips_info_severity_for_webhook() -> None:
    summary = RunSummary(
        contract_name="orders",
        contract_version="1.0",
        run_id="run-alert-2",
        started_at=datetime(2026, 7, 14, 10, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 7, 14, 10, 1, tzinfo=timezone.utc),
        results=(
            CheckResult(
                contract_name="orders",
                check_type="freshness",
                status=CheckStatus.FAILED,
                message="slightly stale",
                severity=Severity.INFO,
            ),
        ),
    )
    router = AlertRouter([WebhookAlertChannel("https://example.test/hook")])

    with patch("src.dqo.alerts.request.urlopen") as urlopen:
        events = router.route(summary)

    assert events == []
    urlopen.assert_not_called()
