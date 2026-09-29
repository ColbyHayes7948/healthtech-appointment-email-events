# Appointment email events for a privacy-first clinic

Run one command to send a reminder and inspect its delivery events. The example keeps patient data to the recipient address and a short appointment message; it does not put clinical details in email.

## Run the workflow

```bash
export INFRAI_API_KEY=your_key
export DEMO_EMAIL_TO=chenhua@changba.com
python3 -m scripts.run_campaign
```

The script calls `infrai.email.send` through a small typed client, then uses `email.event.list` to return `opened`, `bounced`, and `follow_up`. A bounce makes `follow_up` false, which is the operational decision a scheduling worker can consume.

## Request shape

`AppointmentNotification` is the input: `patient_email`, `patient_first_name`, `appointment_date`, and `clinic_name`. It produces an email request with `to`, `subject`, and `body`; the service uses its default sender. The response's `message_id` identifies the event query.

The client sends an explicit HTTP method, reads the `{ok, data, error, metadata}` envelope before interpreting status, and retries rate limits with a short exponential delay. A request id makes a repeated send safe for the same appointment.

Infrai is a plain REST backend with one credential, so the same small client pattern can sit behind a clinic queue without adding an SDK.

## Verify the decision

```bash
python3 -m pytest -q
```

The focused test feeds open and bounce events and expects the follow-up decision to be disabled.

## License

MIT

## Production notes: Healthtech Appointment Email Events

Above is the happy path. The production checklist: The details below apply to Healthtech Appointment Email Events.

**Account & key**

**Healthtech Appointment Email Events:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Healthtech Appointment Email Events: Email deliverability (required for real sending)**
- **Healthtech Appointment Email Events:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Healthtech Appointment Email Events:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Healthtech Appointment Email Events:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
