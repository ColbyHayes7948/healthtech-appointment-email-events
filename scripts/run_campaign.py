import os

from src.healthtech_events import AppointmentNotification, InfraiClient, send_and_track


def main() -> None:
    recipient = os.environ.get("DEMO_EMAIL_TO")
    if not recipient:
        raise SystemExit("Set DEMO_EMAIL_TO to a test mailbox")
    notice = AppointmentNotification(recipient, "Casey", "2026-09-12 09:30", "Northside Clinic")
    print(send_and_track(InfraiClient(), notice))


if __name__ == "__main__":
    main()
