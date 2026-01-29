"""Legacy SSL/TLS support for requests with PAC proxy support.

This module provides utilities for making HTTP requests with legacy SSL/TLS
versions and Proxy Auto-Configuration (PAC) support.

Requirements:
    pip install requests urllib3 pypac

Note:
    Using legacy SSL versions is NOT recommended for production use.
    Only use this when connecting to legacy systems that cannot be updated.
"""

from __future__ import annotations

import ssl
import warnings
from typing import Any
from urllib.parse import urlparse

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# =============================================================================
# SSL/TLS Configuration
# =============================================================================


class LegacySSLAdapter(HTTPAdapter):
    """HTTP Adapter that allows legacy SSL/TLS versions.

    This adapter enables connections to servers using older SSL/TLS versions
    such as TLSv1.0 or TLSv1.1.

    Attributes:
        ssl_context: Custom SSL context with legacy support.

    Example:
        >>> session = requests.Session()
        >>> session.mount("https://", LegacySSLAdapter())
        >>> response = session.get("https://legacy-server.example.com")
    """

    def __init__(
        self,
        ssl_version: int | None = None,
        ciphers: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the adapter with custom SSL settings.

        Args:
            ssl_version: SSL/TLS version to use (e.g., ssl.PROTOCOL_TLSv1).
                        If None, uses default with legacy support enabled.
            ciphers: Custom cipher suite string.
                    If None, uses DEFAULT:@SECLEVEL=1 for legacy support.
            **kwargs: Additional arguments passed to HTTPAdapter.
        """
        self.ssl_context = self._create_legacy_context(ssl_version, ciphers)
        super().__init__(**kwargs)

    def _create_legacy_context(
        self,
        ssl_version: int | None,
        ciphers: str | None,
    ) -> ssl.SSLContext:
        """Create an SSL context with legacy support.

        Args:
            ssl_version: SSL/TLS version to use.
            ciphers: Custom cipher suite string.

        Returns:
            Configured SSL context.
        """
        # Create context with specified version or default
        if ssl_version is not None:
            ctx = ssl.SSLContext(ssl_version)
        else:
            ctx = create_urllib3_context()

        # Enable legacy renegotiation
        ctx.options |= ssl.OP_LEGACY_SERVER_CONNECT

        # Set ciphers for legacy support
        cipher_suite = ciphers or "DEFAULT:@SECLEVEL=1"
        ctx.set_ciphers(cipher_suite)

        # Disable hostname check for legacy servers (use with caution)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        return ctx

    def init_poolmanager(self, *args: Any, **kwargs: Any) -> None:
        """Initialize pool manager with custom SSL context.

        Args:
            *args: Positional arguments for parent class.
            **kwargs: Keyword arguments for parent class.
        """
        kwargs["ssl_context"] = self.ssl_context
        super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, proxy: str, **proxy_kwargs: Any) -> Any:
        """Return a proxy manager with custom SSL context.

        Args:
            proxy: Proxy URL.
            **proxy_kwargs: Additional proxy configuration.

        Returns:
            Configured proxy manager.
        """
        proxy_kwargs["ssl_context"] = self.ssl_context
        return super().proxy_manager_for(proxy, **proxy_kwargs)


class TLSv1Adapter(LegacySSLAdapter):
    """Adapter specifically for TLS 1.0 connections.

    Warning:
        TLS 1.0 is deprecated and insecure. Use only for legacy systems.

    Example:
        >>> session = requests.Session()
        >>> session.mount("https://", TLSv1Adapter())
        >>> response = session.get("https://old-server.example.com")
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize TLS 1.0 adapter.

        Args:
            **kwargs: Additional arguments passed to LegacySSLAdapter.
        """
        warnings.warn(
            "TLS 1.0 is deprecated and insecure. Use only for legacy systems.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(ssl_version=ssl.PROTOCOL_TLSv1, **kwargs)


class TLSv11Adapter(LegacySSLAdapter):
    """Adapter specifically for TLS 1.1 connections.

    Warning:
        TLS 1.1 is deprecated and insecure. Use only for legacy systems.

    Example:
        >>> session = requests.Session()
        >>> session.mount("https://", TLSv11Adapter())
        >>> response = session.get("https://old-server.example.com")
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize TLS 1.1 adapter.

        Args:
            **kwargs: Additional arguments passed to LegacySSLAdapter.
        """
        warnings.warn(
            "TLS 1.1 is deprecated and insecure. Use only for legacy systems.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(ssl_version=ssl.PROTOCOL_TLSv1_1, **kwargs)


# =============================================================================
# PAC (Proxy Auto-Configuration) Support
# =============================================================================


def create_pac_session(
    pac_url: str | None = None,
    pac_file_path: str | None = None,
    use_system_pac: bool = False,
    legacy_ssl: bool = False,
) -> requests.Session:
    """Create a requests session with PAC proxy support.

    This function creates a session that automatically resolves proxies
    using a PAC file.

    Args:
        pac_url: URL to the PAC file.
        pac_file_path: Local path to a PAC file.
        use_system_pac: If True, use the system's configured PAC.
        legacy_ssl: If True, enable legacy SSL support.

    Returns:
        Configured requests Session with PAC support.

    Raises:
        ValueError: If no PAC source is specified.
        ImportError: If pypac is not installed.

    Example:
        >>> # Using PAC URL
        >>> session = create_pac_session(pac_url="http://proxy.example.com/proxy.pac")
        >>> response = session.get("https://example.com")

        >>> # Using system PAC
        >>> session = create_pac_session(use_system_pac=True)
        >>> response = session.get("https://example.com")
    """
    try:
        from pypac import PACSession, get_pac
        from pypac.parser import PACFile
    except ImportError as e:
        raise ImportError(
            "pypac is required for PAC support. Install with: pip install pypac"
        ) from e

    # Load PAC from specified source
    if pac_url:
        pac = get_pac(url=pac_url)
    elif pac_file_path:
        with open(pac_file_path, "r", encoding="utf-8") as f:
            pac_content = f.read()
        pac = PACFile(pac_content)
    elif use_system_pac:
        pac = get_pac()
    else:
        raise ValueError("Must specify pac_url, pac_file_path, or use_system_pac=True")

    # Create PAC session
    session = PACSession(pac)

    # Add legacy SSL support if requested
    if legacy_ssl:
        adapter = LegacySSLAdapter()
        session.mount("https://", adapter)

    return session


class PACProxyResolver:
    """Resolve proxy settings using a PAC file.

    This class provides manual PAC resolution for cases where you need
    more control over proxy selection.

    Attributes:
        pac: The loaded PAC file object.

    Example:
        >>> resolver = PACProxyResolver(pac_url="http://proxy.example.com/proxy.pac")
        >>> proxy = resolver.get_proxy_for_url("https://example.com")
        >>> print(proxy)  # {'https': 'http://proxy.example.com:8080'}
    """

    def __init__(
        self,
        pac_url: str | None = None,
        pac_file_path: str | None = None,
        use_system_pac: bool = False,
    ) -> None:
        """Initialize the PAC resolver.

        Args:
            pac_url: URL to the PAC file.
            pac_file_path: Local path to a PAC file.
            use_system_pac: If True, use the system's configured PAC.

        Raises:
            ValueError: If no PAC source is specified.
            ImportError: If pypac is not installed.
        """
        try:
            from pypac import get_pac
            from pypac.parser import PACFile
        except ImportError as e:
            raise ImportError(
                "pypac is required for PAC support. Install with: pip install pypac"
            ) from e

        if pac_url:
            self.pac = get_pac(url=pac_url)
        elif pac_file_path:
            with open(pac_file_path, "r", encoding="utf-8") as f:
                pac_content = f.read()
            self.pac = PACFile(pac_content)
        elif use_system_pac:
            self.pac = get_pac()
        else:
            raise ValueError(
                "Must specify pac_url, pac_file_path, or use_system_pac=True"
            )

    def get_proxy_for_url(self, url: str) -> dict[str, str] | None:
        """Get proxy settings for a given URL.

        Args:
            url: The URL to get proxy settings for.

        Returns:
            Dictionary with proxy settings or None if direct connection.

        Example:
            >>> resolver = PACProxyResolver(use_system_pac=True)
            >>> proxy = resolver.get_proxy_for_url("https://example.com")
        """
        if self.pac is None:
            return None

        result = self.pac.find_proxy_for_url(url, urlparse(url).netloc)

        if result == "DIRECT" or result is None:
            return None

        # Parse PAC result (e.g., "PROXY proxy.example.com:8080")
        proxies: dict[str, str] = {}
        for proxy_entry in result.split(";"):
            proxy_entry = proxy_entry.strip()
            if proxy_entry.upper().startswith("PROXY "):
                proxy_addr = proxy_entry[6:].strip()
                proxies["http"] = f"http://{proxy_addr}"
                proxies["https"] = f"http://{proxy_addr}"
            elif proxy_entry.upper().startswith("SOCKS "):
                proxy_addr = proxy_entry[6:].strip()
                proxies["http"] = f"socks5://{proxy_addr}"
                proxies["https"] = f"socks5://{proxy_addr}"

        return proxies if proxies else None


# =============================================================================
# Convenience Functions
# =============================================================================


def create_legacy_session(
    verify_ssl: bool = False,
    ssl_version: int | None = None,
    ciphers: str | None = None,
) -> requests.Session:
    """Create a requests session with legacy SSL support.

    Args:
        verify_ssl: Whether to verify SSL certificates.
        ssl_version: Specific SSL/TLS version to use.
        ciphers: Custom cipher suite string.

    Returns:
        Configured requests Session.

    Example:
        >>> session = create_legacy_session()
        >>> response = session.get("https://legacy-server.example.com")
    """
    # Suppress InsecureRequestWarning
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    session = requests.Session()
    adapter = LegacySSLAdapter(ssl_version=ssl_version, ciphers=ciphers)
    session.mount("https://", adapter)
    session.verify = verify_ssl

    return session


def legacy_get(
    url: str,
    **kwargs: Any,
) -> requests.Response:
    """Make a GET request with legacy SSL support.

    This is a convenience function for one-off requests.

    Args:
        url: URL to request.
        **kwargs: Additional arguments passed to requests.get().

    Returns:
        Response object.

    Example:
        >>> response = legacy_get("https://legacy-server.example.com/api")
        >>> print(response.json())
    """
    session = create_legacy_session()
    return session.get(url, **kwargs)


def legacy_post(
    url: str,
    data: Any = None,
    json: Any = None,
    **kwargs: Any,
) -> requests.Response:
    """Make a POST request with legacy SSL support.

    Args:
        url: URL to request.
        data: Data to send in the body.
        json: JSON data to send in the body.
        **kwargs: Additional arguments passed to requests.post().

    Returns:
        Response object.

    Example:
        >>> response = legacy_post(
        ...     "https://legacy-server.example.com/api",
        ...     json={"key": "value"}
        ... )
    """
    session = create_legacy_session()
    return session.post(url, data=data, json=json, **kwargs)


# =============================================================================
# Combined Legacy SSL + PAC Support
# =============================================================================


def create_legacy_pac_session(
    pac_url: str | None = None,
    pac_file_path: str | None = None,
    use_system_pac: bool = False,
    verify_ssl: bool = False,
    ciphers: str | None = None,
) -> requests.Session:
    """Create a session with both legacy SSL and PAC support.

    This function combines legacy SSL support with PAC proxy resolution.

    Args:
        pac_url: URL to the PAC file.
        pac_file_path: Local path to a PAC file.
        use_system_pac: If True, use the system's configured PAC.
        verify_ssl: Whether to verify SSL certificates.
        ciphers: Custom cipher suite string.

    Returns:
        Configured requests Session with both features.

    Example:
        >>> session = create_legacy_pac_session(
        ...     pac_url="http://proxy.example.com/proxy.pac",
        ...     verify_ssl=False
        ... )
        >>> response = session.get("https://legacy-internal-server.local")
    """
    # Suppress warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Create PAC session
    session = create_pac_session(
        pac_url=pac_url,
        pac_file_path=pac_file_path,
        use_system_pac=use_system_pac,
        legacy_ssl=True,
    )

    # Override adapter with custom ciphers if specified
    if ciphers:
        adapter = LegacySSLAdapter(ciphers=ciphers)
        session.mount("https://", adapter)

    session.verify = verify_ssl

    return session


# =============================================================================
# Usage Examples
# =============================================================================

if __name__ == "__main__":
    # Example 1: Basic legacy SSL request
    print("=== Example 1: Basic Legacy SSL ===")
    session = create_legacy_session()
    # response = session.get("https://legacy-server.example.com")

    # Example 2: Using specific TLS version
    print("\n=== Example 2: Specific TLS Version ===")
    session = requests.Session()
    session.mount("https://", TLSv1Adapter())
    # response = session.get("https://old-server.example.com")

    # Example 3: PAC proxy with legacy SSL
    print("\n=== Example 3: PAC + Legacy SSL ===")
    # session = create_legacy_pac_session(
    #     pac_url="http://proxy.example.com/proxy.pac"
    # )
    # response = session.get("https://internal-server.local")

    # Example 4: Manual proxy resolution
    print("\n=== Example 4: Manual PAC Resolution ===")
    # resolver = PACProxyResolver(use_system_pac=True)
    # proxy = resolver.get_proxy_for_url("https://example.com")
    # session = create_legacy_session()
    # response = session.get("https://example.com", proxies=proxy)

    print("\nAll examples defined. Uncomment to run with actual servers.")
