"""
Yandex Cloud Function — приём заявок с robertfitchell.ru.
Регион ru-central1 → данные обрабатываются на серверах в РФ (152-ФЗ).

Принимает JSON-POST от формы, отправляет заявку на почту через
SMTP Яндекса (smtp.yandex.ru — серверы в РФ).

Переменные окружения функции (задаются в консоли Yandex Cloud,
в код НЕ зашиваются):
  SMTP_USER  — логин ящика-отправителя, напр. robot@yandex.ru
  SMTP_PASS  — пароль приложения (НЕ основной пароль; создаётся в Яндекс ID)
  MAIL_TO    — куда слать заявки, напр. fitchellr@yandex.ru
  ALLOW_ORIGIN — https://robertfitchell.ru
"""

import json
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header

FIELDS = ["name", "phone", "company", "program", "message", "page"]


def _resp(status, body, origin):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }


def handler(event, context):
    origin = os.environ.get("ALLOW_ORIGIN", "*")

    # Preflight CORS
    if event.get("httpMethod") == "OPTIONS":
        return _resp(200, {"ok": True}, origin)

    if event.get("httpMethod") != "POST":
        return _resp(405, {"ok": False, "error": "method not allowed"}, origin)

    # Тело может прийти base64-кодированным
    raw = event.get("body", "") or ""
    if event.get("isBase64Encoded"):
        import base64
        raw = base64.b64decode(raw).decode("utf-8")

    try:
        data = json.loads(raw)
    except Exception:
        return _resp(400, {"ok": False, "error": "bad json"}, origin)

    # Обязательное согласие на обработку ПДн
    if not data.get("consent"):
        return _resp(400, {"ok": False, "error": "consent required"}, origin)

    if not str(data.get("name", "")).strip() or not str(data.get("phone", "")).strip():
        return _resp(400, {"ok": False, "error": "name and phone required"}, origin)

    lines = []
    for f in FIELDS:
        v = str(data.get(f, "")).strip()
        if v:
            lines.append(f"{f}: {v}")
    lines.append("consent: да")
    text = "Новая заявка с сайта robertfitchell.ru\n\n" + "\n".join(lines)

    user = os.environ["SMTP_USER"]
    msg = MIMEText(text, "plain", "utf-8")
    msg["Subject"] = Header("Заявка с сайта robertfitchell.ru", "utf-8")
    msg["From"] = user
    msg["To"] = os.environ["MAIL_TO"]

    try:
        with smtplib.SMTP_SSL("smtp.yandex.ru", 465, timeout=10) as s:
            s.login(user, os.environ["SMTP_PASS"])
            s.sendmail(user, [os.environ["MAIL_TO"]], msg.as_string())
    except Exception as exc:
        return _resp(502, {"ok": False, "error": f"mail failed: {exc}"}, origin)

    return _resp(200, {"ok": True}, origin)
