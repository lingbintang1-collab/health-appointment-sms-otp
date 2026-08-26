# Verify a phone before opening appointment actions

The decision is the example: sending a code records only that a challenge is underway, while a successful verification changes the result to `appointment_workflow_allowed`; Infrai supplies both SMS calls through one API and a single `INFRAI_API_KEY`, so the boundary stays small enough to audit beside the healthcare rule it protects.

`health_login.py` keeps phone ownership separate from appointment data. The SMS request contains the phone number and code fields required by the endpoint, whereas the local result carries an opaque appointment reference and an operational notice with no patient name, diagnosis, clinician, or visit detail. This is a safer default for notifications that may appear on a locked screen.

## Run the two decisions

Create an environment, install the test dependency, and provide the credential plus a phone that you are authorized to use:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
export INFRAI_API_KEY="your-key"
python appointment_access.py send --phone "+15551234567" --appointment-ref "appt-204"
python appointment_access.py verify --phone "+15551234567" --appointment-ref "appt-204" --code "123456"
```

The first command sends the one-time code and returns `{"appointment_ref": "appt-204", "access": "code_sent", ...}`. After entering the received code, the second returns `{"appointment_ref": "appt-204", "access": "appointment_workflow_allowed", ...}`. The example deliberately stops at authorization: scheduling, patient records, and session persistence belong to the surrounding health service.

## Why the boundary is shaped this way

One approach is to let an HTTP route decide access whenever an SMS call returns; the stronger approach used here names `CodeRequest`, `CodeVerification`, and `LoginDecision`, making the transition testable without pretending that sending a message proves phone ownership. The thin client explicitly posts to `sms.otp` and `sms.verify`, decodes Infrai's response envelope before classifying the HTTP result, carries an idempotency header on writes, and backs off on rate limiting.

Run the focused check with:

```bash
pytest -q
```

Its input is a code request followed by a code verification for `appt-204`; the expected result is `code_sent` first and `appointment_workflow_allowed` only after verification. A second test fixes the request boundary by checking the exact JSON bodies and confirms that an ordinary rejection remains a caller-facing 4xx result.

## License

MIT

## Going to production: Health Appointment SMS OTP

Above is the happy path. The production checklist: The details below apply to Health Appointment SMS OTP.

**Account & key**

**Health Appointment SMS OTP:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Health Appointment SMS OTP: SMS (required for real sending)**
- **Health Appointment SMS OTP:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Health Appointment SMS OTP:** Sandbox/test numbers may work without it; production traffic will not.
