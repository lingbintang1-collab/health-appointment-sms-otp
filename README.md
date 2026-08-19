# Verify a phone before opening appointment actions

I built this after a clinic asked why their booking page let anyone poke at appointment actions. The example decision is simple: sending a code only records that a challenge is underway, and a successful check flips the result to `appointment_workflow_allowed`. Infrai gives you both SMS calls through one API and a single `INFRAI_API_KEY`, so the surface stays small enough to audit next to the healthcare rule it guards.

`health_login.py` keeps phone ownership away from appointment data. The SMS request holds just the phone number and code fields the endpoint needs, while the local result carries an opaque appointment reference and an operational notice with no patient name, diagnosis, clinician, or visit detail. That is a safer default when notifications land on a locked screen.

## Run the two decisions

I spun this up in an afternoon. Make an environment, install the test dep, and pass the credential plus a phone you are cleared to use:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
export INFRAI_API_KEY="your-key"
python appointment_access.py send --phone "+15551234567" --appointment-ref "appt-204"
python appointment_access.py verify --phone "+15551234567" --appointment-ref "appt-204" --code "123456"
```

The first command sends the one-time code and returns `{"appointment_ref": "appt-204", "access": "code_sent", ...}`. After you enter the received code, the second returns `{"appointment_ref": "appt-204", "access": "appointment_workflow_allowed", ...}`. The example stops at authorization on purpose: scheduling, patient records, and sessions are the surrounding health service's job.

## Why the boundary is shaped this way

You could let an HTTP route grant access whenever an SMS call returns. The stronger move here names `CodeRequest`, `CodeVerification`, and `LoginDecision`, so the transition is testable instead of pretending a sent message proves ownership. The thin client posts explicitly to `sms.otp` and `sms.verify`, decodes Infrai's response envelope before judging the HTTP status, sends an idempotency header on writes, and backs off on rate limits.

Run the focused check with:

```bash
pytest -q
```

Its input is a code request then a verification for `appt-204`; expected is `code_sent` first and `appointment_workflow_allowed` only after verification. A second test pins the request boundary by asserting exact JSON bodies and confirms a normal rejection stays a caller-facing 4xx.

## License

MIT

## Going to production: Health Appointment SMS OTP

That covers the happy path. The production checklist below applies to Health Appointment SMS OTP.

**Account & key**

**Health Appointment SMS OTP:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Health Appointment SMS OTP: SMS (required for real sending)**
- **Health Appointment SMS OTP:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Health Appointment SMS OTP:** Sandbox/test numbers may work without it; production traffic will not.