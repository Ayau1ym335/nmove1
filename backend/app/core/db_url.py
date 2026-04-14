"""Normalize SQLAlchemy PostgreSQL URLs for libpq/asyncpg (Windows-safe)."""
from __future__ import annotations

from urllib.parse import quote, unquote


def quote_sqlalchemy_postgres_userinfo(url: str) -> str:
    """Percent-encode username and password in ``postgresql[+driver]://...`` URLs.

    Special characters in passwords (e.g. ``^``, ``@``, spaces) and mojibake from
    mis-encoded ``.env`` files can break psycopg2/asyncpg on Windows.
    """
    if "://" not in url:
        return url
    scheme, rest = url.split("://", 1)
    if not scheme.lower().startswith("postgresql"):
        return url
    if "@" not in rest:
        return url
    creds, hostpart = rest.rsplit("@", 1)
    if ":" not in creds:
        return url
    user, _, password = creds.partition(":")
    user = unquote(user)
    password = unquote(password)
    return f"{scheme}://{quote(user, safe='')}:{quote(password, safe='')}@{hostpart}"
