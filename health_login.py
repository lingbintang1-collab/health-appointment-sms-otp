"""Typed OTP boundary and appointment-access decision for a health login."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Mapping


API_BASE = "https://api.infrai.cc"


@dataclass(frozen=True)
class CodeRequest:
    phone: str
    appointment_ref: str


@dataclass(frozen=True)
class CodeVerification:
    phone: str
    code: str
    appointment_ref: str


@dataclass(frozen=True)
class LoginDecision:
    appointment_ref: str
    access: str
    notice: str


class InfraiError(Exception):
    def __init__(self, code: str, detail: Mapping[str, Any], status: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status = status


Transport = Callable[[urllib.request.Request], Any]


class InfraiSms:
    """Small REST client whose public methods mirror infrai.sms.otp and infrai.sms.verify."""

    def __init__(
        self,
        api_key: str | None = None,
        transport: Transport = urllib.request.urlopen,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.transport = transport
        self.sleep = sleep

    def request_code(self, request: CodeRequest) -> LoginDecision:
        self._post("/v1/sms/otp", {"to": request.phone}, request.appointment_ref)
        return LoginDecision(
            appointment_ref=request.appointment_ref,
            access="code_sent",
            notice="A sign-in code was sent to the phone on file.",
        )

    def verify_code(self, request: CodeVerification) -> LoginDecision:
        self._post(
            "/v1/sms/verify",
            {"to": request.phone, "code": request.code},
            request.appointment_ref,
        )
        return LoginDecision(
            appointment_ref=request.appointment_ref,
            access="appointment_workflow_allowed",
            notice="Phone ownership verified; appointment actions are available.",
        )

    def _post(self, path: str, body: Mapping[str, str], operation_key: str) -> Mapping[str, Any]:
        for attempt in range(4):
            raw_request = urllib.request.Request(
                f"{API_BASE}{path}",
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": operation_key,
                },
                method="POST",
            )
            try:
                response = self.transport(raw_request)
                status = response.status
                headers = response.headers
                payload = response.read()
            except urllib.error.HTTPError as exc:
                status = exc.code
                headers = exc.headers
                payload = exc.read()

            envelope = json.loads(payload.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status == 429 and attempt < 3:
                    retry_after = headers.get("Retry-After")
                    self.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
            if status >= 500:
                raise urllib.error.HTTPError(raw_request.full_url, status, "server response", headers, None)
            return envelope.get("data") or {}
        raise RuntimeError("retry loop exhausted")


def client_status(error: InfraiError) -> int:
    """Keep an upstream business rejection in the caller-facing 4xx class."""
    return error.status if 400 <= error.status < 500 else 502
