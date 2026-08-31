"""
Yandex Cloud Function — приём заявок с robertfitchell.ru и robertfitchell.online.
Регион ru-central1 → данные обрабатываются на серверах в РФ (152-ФЗ).

Принимает JSON-POST от формы, отправляет заявку на почту через
SMTP Яндекса (smtp.yandex.ru — серверы в РФ).

В письмо добавляется блок «Подтверждение согласия»: дата и время по Москве,
IP-адрес отправителя, браузер, редакция документов и точная формулировка,
под которой стоял отмеченный чекбокс. Доказывать наличие согласия по 152-ФЗ
обязан оператор, а письмо — единственное место, где заявка хранится.

Переменные окружения (задаются в консоли Yandex Cloud, в код НЕ зашиваются):
  SMTP_USER    — логин ящика-отправителя, напр. robot@yandex.ru
  SMTP_PASS    — пароль приложения (НЕ основной пароль; создаётся в Яндекс ID)
  MAIL_TO      — куда слать заявки, напр. robertahmetgareev@yandex.ru
  ALLOW_ORIGIN — через запятую: https://robertfitchell.ru,https://robertfitchell.online
"""

import json
import os
import smtplib
import logging
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.header import Header

FIELDS = ["name", "surname", "phone", "company", "program", "city", "message", "page"]

MAX_LEN = 2000  # максимальная длина одного поля (анти-DoS)

MSK = timezone(timedelta(hours=3))  # Москва — время фиксации согласия

# формулировка по умолчанию, если фронт её не прислал (старая версия страницы)
DEFAULT_CONSENT_TEXT = (
    "Я даю согласие на обработку персональных данных "
    "и принимаю Политику конфиденциальности"
)

_DEFAULT_ORIGINS = "https://robertfitchell.ru,https://robertfitchell.online"
_ALLOW = [o.strip() for o in os.environ.get("ALLOW_ORIGIN", _DEFAULT_ORIGINS).split(",")]


def _cors_origin(req_origin):
    if "*" in _ALLOW:
        return "*"
    return req_origin if req_origin in _ALLOW else (_ALLOW[0] if _ALLOW else "*")


def _client_ip(headers):
    """IP отправителя. Yandex Cloud кладёт реальный адрес в X-Forwarded-For;
    первый элемент списка — сам клиент, остальные прокси."""
    fwd = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for") or ""
    if fwd:
        return fwd.split(",")[0].strip()[:64]
    return (headers.get("X-Real-Ip") or headers.get("x-real-ip") or "не определён")[:64]


def _resp(status, body, req_origin=""):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": _cors_origin(req_origin),
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }


def handler(event, context):
    headers = event.get("headers") or {}
    req_origin = headers.get("origin", "") or headers.get("Origin", "")

    if event.get("httpMethod") == "OPTIONS":
        return _resp(200, {"ok": True}, req_origin)

    if event.get("httpMethod") != "POST":
        return _resp(405, {"ok": False, "error": "method not allowed"}, req_origin)

    raw = event.get("body", "") or ""
    try:
        if event.get("isBase64Encoded"):
            import base64
            raw = base64.b64decode(raw).decode("utf-8")
        data = json.loads(raw)
    except Exception:
        return _resp(400, {"ok": False, "error": "bad request"}, req_origin)

    if not data.get("consent"):
        return _resp(400, {"ok": False, "error": "consent required"}, req_origin)

    name = str(data.get("name", "")).strip()[:MAX_LEN]
    phone = str(data.get("phone", "")).strip()[:MAX_LEN]
    if not name or not phone:
        return _resp(400, {"ok": False, "error": "name and phone required"}, req_origin)

    page = str(data.get("page", req_origin)).strip()[:MAX_LEN]
    lines = [f"Страница: {page}", ""]
    labels = {
        "name": "Имя", "surname": "Фамилия", "phone": "Телефон",
        "company": "Компания", "program": "Программа",
        "city": "Город", "message": "Комментарий",
    }
    for f in FIELDS[:-1]:
        v = str(data.get(f, "")).strip()[:MAX_LEN]
        if v:
            lines.append(f"{labels.get(f, f)}: {v}")

    # --- подтверждение согласия (152-ФЗ: доказывает оператор) ---
    received = datetime.now(MSK).strftime("%d.%m.%Y %H:%M:%S МСК")
    consent_text = str(data.get("consentText", "")).strip()[:MAX_LEN] or DEFAULT_CONSENT_TEXT
    docs_version = str(data.get("docsVersion", "")).strip()[:64] or "не передана"
    user_agent = str(headers.get("User-Agent") or headers.get("user-agent") or "")[:MAX_LEN]

    lines += [
        "",
        "--- Подтверждение согласия (152-ФЗ) ---",
        f"Дата и время получения: {received}",
        f"IP-адрес отправителя: {_client_ip(headers)}",
        f"Браузер (User-Agent): {user_agent or 'не передан'}",
        f"Редакция документов на момент согласия: {docs_version}",
        f"Отмечен чекбокс: «{consent_text}»",
        "Согласие на обработку ПДн: получено (форма без отметки не отправляется)",
        "",
        "Письмо хранить 12 месяцев с даты последнего обращения субъекта",
        "(п. 5.1 Политики), затем уничтожить с составлением акта.",
    ]

    subject_site = "robertfitchell.online" if "online" in page else "robertfitchell.ru"
    text = f"Новая заявка с сайта {subject_site}\n\n" + "\n".join(lines)

    user = os.environ["SMTP_USER"]
    msg = MIMEText(text, "plain", "utf-8")
    msg["Subject"] = Header(f"Заявка с {subject_site}", "utf-8")
    msg["From"] = user
    msg["To"] = os.environ["MAIL_TO"]

    try:
        with smtplib.SMTP_SSL("smtp.yandex.ru", 465, timeout=10) as s:
            s.login(user, os.environ["SMTP_PASS"])
            s.sendmail(user, [os.environ["MAIL_TO"]], msg.as_string())
    except Exception as exc:
        logging.exception("mail send failed: %s", exc)
        return _resp(502, {"ok": False, "error": "mail failed"}, req_origin)

    return _resp(200, {"ok": True}, req_origin)
