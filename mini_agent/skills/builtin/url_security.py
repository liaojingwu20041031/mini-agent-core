"""Public URL validation shared by built-in network tools."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit


def blocked_host(hostname: str) -> str | None:
    if not hostname:
        return "missing_host"
    lowered = hostname.strip("[]").lower()
    if lowered in {"localhost", "0.0.0.0"}:
        return "blocked_private_url"
    try:
        addresses = socket.getaddrinfo(lowered, None)
    except socket.gaierror:
        return "dns_error"
    for item in addresses:
        ip = ipaddress.ip_address(item[4][0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_unspecified
            or ip.is_multicast
            or ip.is_reserved
        ):
            return "blocked_private_url"
    return None


def validate_public_url(url: str) -> tuple[str | None, str | None]:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        return None, "unsupported_scheme"
    reason = blocked_host(parsed.hostname or "")
    if reason:
        return None, reason
    return parsed.geturl(), None
