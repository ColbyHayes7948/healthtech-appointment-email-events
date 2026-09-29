from src.healthtech_events import AppointmentNotification, summarize_events


def test_bounce_blocks_follow_up_and_open_is_recorded():
    notification = AppointmentNotification("patient@example.org", "Sam", "2026-09-12", "Northside Clinic")
    assert notification.email_payload()["to"] == "patient@example.org"
    assert "body" in notification.email_payload()
    assert "text" not in notification.email_payload()
    assert summarize_events([{"event": "open"}, {"event": "bounce"}]) == {
        "opened": True, "bounced": True, "follow_up": False
    }
