# Legacy SSL Requests Cheat Sheet

A cheat sheet for easily communicating with servers using older SSL/TLS versions and configuring proxies using PAC (Proxy Auto-Configuration).

> ⚠️ **Warning**: Older SSL/TLS versions (TLS 1.0, TLS 1.1) are deprecated and pose security risks. Use only when compatibility with legacy systems is required.

## Installation

```bash
pip install requests urllib3 pypac
```

## Quick Start

### Basic Legacy SSL Request

```python
from legacy_ssl_requests import create_legacy_session, legacy_get

# Create and use a session
session = create_legacy_session()
response = session.get("https://legacy-server.example.com")

# Or use one-liner
response = legacy_get("https://legacy-server.example.com")
```

### PAC Support

```python
from legacy_ssl_requests import create_pac_session

# Specify PAC URL
session = create_pac_session(pac_url="http://proxy.example.com/proxy.pac")
response = session.get("https://example.com")

# Use system PAC
session = create_pac_session(use_system_pac=True)
response = session.get("https://example.com")
```

### Legacy SSL + PAC

```python
from legacy_ssl_requests import create_legacy_pac_session

# Combine both features
session = create_legacy_pac_session(
    pac_url="http://proxy.example.com/proxy.pac",
    verify_ssl=False
)
response = session.get("https://internal-legacy-server.local")
```

## Detailed Usage

### Custom SSL Adapters

```python
import requests
from legacy_ssl_requests import LegacySSLAdapter, TLSv1Adapter, TLSv11Adapter

# Generic legacy adapter
session = requests.Session()
session.mount("https://", LegacySSLAdapter())

# TLS 1.0 only (deprecated)
session = requests.Session()
session.mount("https://", TLSv1Adapter())

# TLS 1.1 only (deprecated)
session = requests.Session()
session.mount("https://", TLSv11Adapter())
```

### Custom Cipher Suites

```python
from legacy_ssl_requests import LegacySSLAdapter

# Specify particular cipher suites
adapter = LegacySSLAdapter(ciphers="AES256-SHA:AES128-SHA")
session = requests.Session()
session.mount("https://", adapter)
```

### Manual PAC Proxy Resolution

```python
from legacy_ssl_requests import PACProxyResolver, create_legacy_session

# Create PAC resolver
resolver = PACProxyResolver(pac_url="http://proxy.example.com/proxy.pac")

# Get proxy for URL
proxy = resolver.get_proxy_for_url("https://example.com")
# Result: {'http': 'http://proxy.example.com:8080', 'https': 'http://proxy.example.com:8080'}

# Make request with proxy
session = create_legacy_session()
response = session.get("https://example.com", proxies=proxy)
```

### Using Local PAC File

```python
from legacy_ssl_requests import create_pac_session

# Use local PAC file
session = create_pac_session(pac_file_path="./proxy.pac")
response = session.get("https://example.com")
```

## Common Use Cases

### Accessing Legacy Servers in Corporate Networks

```python
from legacy_ssl_requests import create_legacy_pac_session

# Access legacy server using corporate PAC
session = create_legacy_pac_session(
    use_system_pac=True,
    verify_ssl=False  # Allow self-signed certificates
)

# Access internal legacy API
response = session.get("https://legacy-api.internal.corp/data")
data = response.json()
```

### Disabling SSL Certificate Verification

```python
from legacy_ssl_requests import create_legacy_session

# Session without certificate verification (for development)
session = create_legacy_session(verify_ssl=False)
response = session.get("https://self-signed.example.com")
```

### POST Requests

```python
from legacy_ssl_requests import legacy_post, create_legacy_session

# One-liner
response = legacy_post(
    "https://legacy-api.example.com/submit",
    json={"key": "value"}
)

# Using session
session = create_legacy_session()
response = session.post(
    "https://legacy-api.example.com/submit",
    data={"username": "user", "password": "pass"}
)
```

## Troubleshooting

### Common Errors and Solutions

#### `ssl.SSLError: [SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED]`

```python
# Automatically resolved by using LegacySSLAdapter
from legacy_ssl_requests import create_legacy_session
session = create_legacy_session()
```

#### `ssl.SSLError: [SSL: DH_KEY_TOO_SMALL]`

```python
# Use cipher suite with lower SECLEVEL
from legacy_ssl_requests import LegacySSLAdapter

adapter = LegacySSLAdapter(ciphers="DEFAULT:@SECLEVEL=0")
session = requests.Session()
session.mount("https://", adapter)
```

#### `pypac.parser.PACFetchError`

```python
# If PAC file cannot be fetched, configure proxy directly
session = create_legacy_session()
proxies = {
    "http": "http://proxy.example.com:8080",
    "https": "http://proxy.example.com:8080"
}
response = session.get("https://example.com", proxies=proxies)
```

## API Reference

| Function/Class | Description |
| -------------- | ----------- |
| `create_legacy_session()` | Create a session with legacy SSL support |
| `create_pac_session()` | Create a session with PAC support |
| `create_legacy_pac_session()` | Create a session with both features |
| `legacy_get()` | GET request with legacy SSL support |
| `legacy_post()` | POST request with legacy SSL support |
| `LegacySSLAdapter` | Customizable SSL adapter |
| `TLSv1Adapter` | TLS 1.0 specific adapter |
| `TLSv11Adapter` | TLS 1.1 specific adapter |
| `PACProxyResolver` | Manual PAC resolution class |

## Dependencies

- `requests` >= 2.25.0
- `urllib3` >= 1.26.0
- `pypac` >= 0.16.0 (required for PAC features)

## License

MIT License
