import ipaddress
import re
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

DOMAIN_RE = re.compile(
    r"(?:[a-zа-яё0-9](?:[a-zа-яё0-9-]{0,61}[a-zа-яё0-9])?\.)+"
    r"(?:[a-zа-яё]{2,63}|xn--[a-z0-9-]{2,59})",
    re.IGNORECASE,
)

MONTHS_RU = [
    "января", "февраля", "марта", "апреля",
    "мая", "июня", "июля", "августа",
    "сентября", "октября", "ноября", "декабря",
]


def parse_title(text):
    if len(text) > 80:
        raise ValueError("Слишком длинное, до 80 символов")
    return text.strip()


def parse_url(text):
    text = re.sub(r"\s+", "", text)

    if "://" not in text:
        text = "https://" + text

    try:
        url = urlsplit(text)
        port = url.port
    except ValueError as exc:
        raise ValueError("Некорректная ссылка или порт") from exc

    if url.scheme.lower() not in ("http", "https"):
        raise ValueError("Допустимы только http:// и https://")

    if not url.hostname or not url.netloc:
        raise ValueError("Укажите адрес сайта")

    if url.username is not None or url.password is not None:
        raise ValueError("Ссылка не должна содержать логин или пароль")

    try:
        ipaddress.ip_address(url.hostname)
    except ValueError:
        if not DOMAIN_RE.fullmatch(url.hostname.rstrip(".")):
            raise ValueError("Некорректный домен")

    if url.netloc.endswith(":") or port == 0:
        raise ValueError("Некорректный порт")

    return urlunsplit((
        url.scheme.lower(),
        url.netloc,
        url.path,
        url.query,
        url.fragment,
    ))


def parse_date(text):
    text = text.strip()

    match = re.fullmatch(r"(\d{2})-(\d{2}) (\d{2}):(\d{2})", text)

    if not match:
        raise ValueError(
            'Введите дату в формате "ММ-ДД ЧЧ:ММ", '
            "например: 10-21 18:00"
        )

    month, day, hour, minute = map(int, match.groups())
        
    try:
        datetime(2000, month, day, hour, minute)
    except ValueError as exc:
        raise ValueError(
            "Такой даты или времени не существует"
        ) from exc

    now = datetime.now().replace(second=0, microsecond=0)
    year = now.year

    # Находим ближайшую возможную дату.

    while year <= 9999:
        try:
            event_date = datetime(
                year, month, day, hour, minute
            )
        except ValueError:
            year += 1
            continue

        if event_date > now:
            return event_date.strftime("%Y-%m-%d %H:%M:%S")

        year += 1

    raise ValueError("Не удалось подобрать год для этой даты")


def format_date(text):
    event_date = datetime.strptime(
        text.strip(),
        "%Y-%m-%d %H:%M:%S",
    )

    month = MONTHS_RU[event_date.month - 1]

    return f"{event_date.day} {month} {event_date:%H:%M}"
