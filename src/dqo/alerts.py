"""Alert routing for failed quality checks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib import error, request

from src.dqo.models import CheckResult, RunSummary, Severity


@dataclass(frozen=True)
class AlertEvent:
    contract_name: str
    run_id: str
    check_type: str
    severity: Severity
    message: str


class AlertChannel(Protocol):
    def send(self, event: AlertEvent) -> None: ...


class ConsoleAlertChannel:
    def send(self, event: AlertEvent) -> None:
        print(
            f"[{event.severity.value.upper()}] {event.contract_name} "
            f"{event.check_type}: {event.message}"
        )


class FileAlertChannel:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, event: AlertEvent) -> None:
        payload = {
            "contract_name": event.contract_name,
            "run_id": event.run_id,
            "check_type": event.check_type,
            "severity": event.severity.value,
            "message": event.message,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")


class WebhookAlertChannel:
    def __init__(self, url: str) -> None:
        self.url = url

    def send(self, event: AlertEvent) -> None:
        payload = json.dumps(
            {
                "contract_name": event.contract_name,
                "run_id": event.run_id,
                "check_type": event.check_type,
                "severity": event.severity.value,
                "message": event.message,
            }
        ).encode("utf-8")
        http_request = request.Request(
            self.url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=5):
                return
        except error.URLError as exc:
            raise RuntimeError(f"webhook delivery failed: {exc}") from exc


class AlertRouter:
    def __init__(self, channels: list[AlertChannel]) -> None:
        self.channels = channels

    def route(self, summary: RunSummary) -> list[AlertEvent]:
        events: list[AlertEvent] = []
        for result in summary.failed_results:
            if result.severity == Severity.INFO:
                continue
            event = AlertEvent(
                contract_name=summary.contract_name,
                run_id=summary.run_id,
                check_type=result.check_type,
                severity=result.severity,
                message=result.message,
            )
            events.append(event)
            for channel in self.channels:
                channel.send(event)
        return events
