"""Legacy SSL/TLS support for requests with PAC proxy support.

This package provides utilities for making HTTP requests with legacy SSL/TLS
versions and Proxy Auto-Configuration (PAC) support.
"""

from __future__ import annotations

from .legacy_ssl_requests import (
    LegacySSLAdapter,
    PACProxyResolver,
    TLSv1Adapter,
    TLSv11Adapter,
    create_legacy_pac_session,
    create_legacy_session,
    create_pac_session,
    legacy_get,
    legacy_post,
)

__all__ = [
    "LegacySSLAdapter",
    "TLSv1Adapter",
    "TLSv11Adapter",
    "PACProxyResolver",
    "create_legacy_session",
    "create_pac_session",
    "create_legacy_pac_session",
    "legacy_get",
    "legacy_post",
]

__version__ = "1.0.0"
