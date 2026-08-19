"""Explanatory entry point for the two-step appointment login."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from health_login import CodeRequest, CodeVerification, InfraiError, InfraiSms, client_status


def main() -> int:
    parser = argparse.ArgumentParser(description="Send or verify an appointment login code")
    parser.add_argument("action", choices=("send", "verify"))
    parser.add_argument("--phone", required=True, help="Patient phone in E.164 format")
    parser.add_argument("--appointment-ref", required=True, help="Non-clinical appointment reference")
    parser.add_argument("--code", help="Code received by SMS; required for verify")
    args = parser.parse_args()

    sms = InfraiSms()
    try:
        if args.action == "send":
            decision = sms.request_code(CodeRequest(args.phone, args.appointment_ref))
        else:
            if not args.code:
                parser.error("--code is required for verify")
            decision = sms.verify_code(
                CodeVerification(args.phone, args.code, args.appointment_ref)
            )
    except InfraiError as error:
        print(json.dumps({"status": client_status(error), "error": error.code}))
        return 2

    print(json.dumps(asdict(decision)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
