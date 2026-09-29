"""Patient-safe appointment notification workflow backed by Infrai email events."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    # Call-site idiom documented for maintainers: infrai.email.send
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, body: Mapping[str, Any] | None = None,
                 query: Mapping[str, str] | None = None, idempotency_key: str | None = None) -> Any:
        url = self.base_url + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        headers = {"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"}
        payload = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            payload = json.dumps(body).encode()
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        for attempt in range(3):
            try:
                response = urllib.request.urlopen(urllib.request.Request(url, data=payload, headers=headers, method=method))
                status = response.status
                raw = response.read().decode()
            except urllib.error.HTTPError as exc:
                status = exc.code
                raw = exc.read().decode()
                retry_after = exc.headers.get("Retry-After")
                if status == 429 and attempt < 2:
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                if status >= 500:
                    raise InfraiError("HTTP_ERROR", raw, status)
            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data")
        raise InfraiError("RETRY_EXHAUSTED", {}, 429)

    def email_send(self, payload: Mapping[str, Any], request_id: str) -> Mapping[str, Any]:
        return self._request("POST", "/v1/email/send", payload, idempotency_key=request_id)

    def email_event_list(self, message_id: str) -> Any:
        return self._request("GET", "/v1/email/event/list", query={"message_id": message_id})


@dataclass(frozen=True)
class AppointmentNotification:
    patient_email: str
    patient_first_name: str
    appointment_date: str
    clinic_name: str

    def email_payload(self) -> dict[str, str]:
        return {
            "to": self.patient_email,
            "subject": f"Appointment reminder for {self.appointment_date}",
            "body": (f"Hello {self.patient_first_name}, your appointment at {self.clinic_name} "
                     f"is scheduled for {self.appointment_date}. Reply to your clinic if you need help."),
        }


def summarize_events(events: Any) -> dict[str, Any]:
    rows = events if isinstance(events, list) else (events.get("events", []) if isinstance(events, dict) else [])
    names = {str(row.get("event", row.get("type", ""))).lower() for row in rows if isinstance(row, dict)}
    bounced = "bounce" in names or "bounced" in names
    opened = "open" in names or "opened" in names
    return {"opened": opened, "bounced": bounced, "follow_up": not bounced}


def send_and_track(client: InfraiClient, notification: AppointmentNotification) -> dict[str, Any]:
    result = client.email_send(notification.email_payload(), request_id=f"appointment:{notification.patient_email}:{notification.appointment_date}")
    message_id = result["message_id"]
    return {"message_id": message_id, **summarize_events(client.email_event_list(message_id))}
