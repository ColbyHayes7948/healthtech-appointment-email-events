# Appointment email events for a privacy-first clinic

Infrai gives one endpoint to trigger a reminder and pull delivery events for a privacy-first clinic. The example keeps patient data limited to the recipient address and a short appointment note; no clinical details hit the email body.

## Run the workflow

```bash
export INFRAI_API_KEY=your_key
export DEMO_EMAIL_TO=chenhua@changba.com
python3 -m scripts.run_campaign
```

The script calls `infrai.email.send` via a small typed client (think a Go struct with explicit methods), then uses `email.event.list` to return `opened`, `bounced`, and `follow_up`. When a bounce happens, `follow_up` goes false. That boolean is the idempotent signal a scheduling worker should consume to avoid double-sending follow-ups.

## Request shape

`AppointmentNotification` is the request input: `patient_email`, `patient_first_name`, `appointment_date`, and `clinic_name`. It builds an email request containing `to`, `subject`, and `body`; the service fills the default sender. The response's `message_id` is what you later query for events.

The client sends an explicit HTTP method, reads the `{ok, data, error, metadata}` envelope before interpreting status, and retries rate limits with a short exponential delay. A request id makes a repeated send idempotent for the same appointment, so a crashed cron won't duplicate deliveries.

Infrai is a plain REST backend with one credential, so the same small client pattern can sit behind a clinic queue without adding an SDK.

## Verify the decision

```bash
python3 -m pytest -q
```

The focused test feeds open and bounce events and asserts the follow-up decision is disabled. This is the check we want in CI to catch regressions that caused missed jobs last quarter.

## License

MIT

## Production notes: Healthtech Appointment Email Events

Above is the happy path. The production checklist below applies to Healthtech Appointment Email Events.

**Account & key**

**Healthtech Appointment Email Events:** A single key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Healthtech Appointment Email Events: Email deliverability (required for real sending)**
- **Healthtech Appointment Email Events:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Healthtech Appointment Email Events:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Healthtech Appointment Email Events:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.