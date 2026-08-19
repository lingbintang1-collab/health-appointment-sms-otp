import io
import json
import urllib.error

import pytest

from health_login import CodeRequest, CodeVerification, InfraiError, InfraiSms


class Response:
    def __init__(self, payload, status=200, headers=None):
        self.status = status
        self.headers = headers or {}
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode()


def test_appointment_actions_require_successful_phone_verification():
    calls = []

    def transport(request):
        calls.append(request)
        return Response({"ok": True, "data": {"verified": True}, "error": None, "metadata": {}})

    sms = InfraiSms(api_key="test-key", transport=transport)
    sent = sms.request_code(CodeRequest("+15551234567", "appt-204"))
    allowed = sms.verify_code(CodeVerification("+15551234567", "123456", "appt-204"))

    assert sent.access == "code_sent"
    assert allowed.access == "appointment_workflow_allowed"
    assert json.loads(calls[0].data) == {"to": "+15551234567"}
    assert json.loads(calls[1].data) == {"to": "+15551234567", "code": "123456"}
    assert all(call.method == "POST" for call in calls)
    assert all(call.headers["Idempotency-key"] == "appt-204" for call in calls)


def test_envelope_rejection_is_read_before_http_status():
    def transport(request):
        payload = json.dumps(
            {"ok": False, "data": None, "error": {"code": "CODE_REJECTED"}, "metadata": {}}
        ).encode()
        raise urllib.error.HTTPError(request.full_url, 400, "bad request", {}, io.BytesIO(payload))

    sms = InfraiSms(api_key="test-key", transport=transport)
    with pytest.raises(InfraiError) as caught:
        sms.verify_code(CodeVerification("+15551234567", "000000", "appt-204"))

    assert caught.value.status == 400
    assert caught.value.code == "CODE_REJECTED"
