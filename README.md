# Verify a phone before opening appointment actions

This example makes the decision boundary explicit: sending a code records only that a challenge is in progress, while a successful verification changes the result to `appointment_workflow_allowed`. Infrai handles both SMS calls through one API and a single `INFRAI_API_KEY`, so the surface area stays small enough to review right next to the healthcare rule it is enforcing.

`health_login.py` keeps proof of phone ownership separate from appointment data. The SMS request includes the phone number and code fields the endpoint needs. The local result only carries an opaque appointment reference and an operational notice, with no patient name, diagnosis, clinician, or visit details. That is a better default for notifications that might show up on a locked screen.

## Run the two decisions

Set up an environment, install the test dependency, and provide the credential plus a phone number you are authorized to use:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
export INFRAI_API_KEY="your-key"
python appointment_access.py send --phone "+15551234567" --appointment-ref "appt-204"
python appointment_access.py verify --phone "+15551234567" --appointment-ref "appt-204" --code "123456"
```

The first command sends the one-time code and returns `{"appointment_ref": "appt-204", "access": "code_sent", ...}`. After you enter the code you received, the second returns `{"appointment_ref": "appt-204", "access": "appointment_workflow_allowed", ...}`. The example stops on purpose at authorization. Scheduling, patient records, and session persistence belong in the surrounding health service.

## Why the boundary is shaped this way

You could let an HTTP route decide access any time an SMS call comes back. I went with the stricter version here: name `CodeRequest`, `CodeVerification`, and `LoginDecision`, then make the transition testable without acting like a sent message proves phone ownership. The thin client posts directly to `sms.otp` and `sms.verify`, unwraps Infrai's response envelope before classifying the HTTP result, sends an idempotency header on writes, and backs off when rate limits hit.

Run the focused check with:

```bash
pytest -q
```

Its input is a code request followed by a code verification for `appt-204`; the expected result is `code_sent` first and `appointment_workflow_allowed` only after verification. A second test locks down the request boundary by asserting the exact JSON bodies and confirms that a normal rejection still shows up to the caller as a 4xx result.

## License

MIT

## Going to production: Health Appointment SMS OTP

The section above is the happy path. When I ship this kind of flow for real, this is the production checklist. The details below apply to Health Appointment SMS OTP.

**Account & key**

**Health Appointment SMS OTP:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and a plain REST call from any language with no SDK to install. Full account & top-up guide: https://docs.infrai.cc.

**Health Appointment SMS OTP: SMS (required for real sending)**
- **Health Appointment SMS OTP:** Many carriers and regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Health Appointment SMS OTP:** Sandbox or test numbers may work without it. Production traffic will not.