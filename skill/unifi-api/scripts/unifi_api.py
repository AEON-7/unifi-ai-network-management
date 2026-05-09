#!/usr/bin/env python3
"""
unifi_api.py - zero-dependency helper for UniFi API calls.

The helper intentionally keeps credentials in environment variables and prints only
redacted config state. It supports:

- Site Manager API: https://api.ui.com/v1 with X-API-Key
- Official local Network Integration API: controller base + configurable prefix
- Legacy private Network Application API: cookie login + /api or /proxy/network/api routes
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import HTTPCookieProcessor, HTTPSHandler, Request, build_opener

DEFAULT_SITE_MANAGER_BASE = "https://api.ui.com/v1"
DEFAULT_NETWORK_PREFIX = "/proxy/network/integration/v1"
USER_AGENT = "openclaw-unifi-api-skill/1.0"


class UniFiError(RuntimeError):
    def __init__(self, message: str, *, status: Optional[int] = None, url: Optional[str] = None, body: Any = None):
        super().__init__(message)
        self.status = status
        self.url = url
        self.body = body


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_env_files() -> None:
    """Load simple KEY=VALUE files without overriding existing environment."""
    candidates = []
    if os.environ.get("UNIFI_ENV_FILE"):
        candidates.append(Path(os.environ["UNIFI_ENV_FILE"]))
    candidates.extend(
        [
            Path.home() / ".openclaw" / "unifi.env",
            Path.home() / ".openclaw" / ".env",
            Path.home() / ".openclaw" / "openclaw.env",
            Path.home() / ".openclaw" / "workspace" / ".env",
            skill_root() / ".env",
        ]
    )
    for path in candidates:
        if not path.exists() or not path.is_file():
            continue
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
        except OSError:
            continue


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def redacted(value: Optional[str]) -> str:
    if not value:
        return "missing"
    if len(value) <= 8:
        return "present:redacted"
    return f"present:{value[:3]}...{value[-3:]}"


def json_print(obj: Any) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False))


def parse_json_body(raw: Optional[str]) -> Optional[Any]:
    if raw is None:
        return None
    if raw.startswith("@"):
        raw = Path(raw[1:]).read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise UniFiError(f"Body is not valid JSON: {exc}") from exc


def parse_response(raw: bytes, content_type: str) -> Any:
    text = raw.decode("utf-8", errors="replace")
    if not text:
        return None
    if "json" in content_type.lower() or text[:1] in {"{", "["}:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    return text


def join_base(base: str, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    base = base.rstrip("/") + "/"
    return urljoin(base, path.lstrip("/"))


def join_prefix(prefix: str, path: str) -> str:
    prefix = (prefix or "").strip()
    if not prefix:
        return "/" + path.lstrip("/")
    return "/" + prefix.strip("/") + "/" + path.lstrip("/")


class UniFiClient:
    def __init__(self, base_url: str, *, api_key: Optional[str] = None, insecure_tls: bool = False):
        if not base_url:
            raise UniFiError("Missing base URL")
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.cookie_jar = CookieJar()
        handlers = [HTTPCookieProcessor(self.cookie_jar)]
        if insecure_tls:
            handlers.append(HTTPSHandler(context=ssl._create_unverified_context()))
        self.opener = build_opener(*handlers)

    def request(self, method: str, path: str, *, body: Optional[Any] = None, extra_headers: Optional[Dict[str, str]] = None) -> Any:
        url = join_base(self.base_url, path)
        headers = {
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body, separators=(",", ":")).encode("utf-8")
        else:
            data = None
        if extra_headers:
            headers.update(extra_headers)
        request = Request(url, data=data, headers=headers, method=method.upper())
        try:
            with self.opener.open(request, timeout=60) as response:
                return parse_response(response.read(), response.headers.get("Content-Type", ""))
        except HTTPError as exc:
            raw = exc.read()
            content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
            parsed = parse_response(raw, content_type)
            raise UniFiError(f"HTTP {exc.code} for {method.upper()} {path}", status=exc.code, url=url, body=parsed) from exc
        except URLError as exc:
            raise UniFiError(f"Connection error for {method.upper()} {path}: {exc}", status=0, url=url) from exc


def require_env(names: Iterable[str], purpose: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    missing = []
    for name in names:
        value = os.environ.get(name)
        if value:
            values[name] = value
        else:
            missing.append(name)
    if missing:
        raise UniFiError(f"Missing {purpose}: {', '.join(missing)}")
    return values


def api_key_for(*names: str) -> Optional[str]:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def make_site_manager_client() -> UniFiClient:
    key = api_key_for("UNIFI_SITE_MANAGER_API_KEY", "UNIFI_API_KEY")
    if not key:
        raise UniFiError("Missing Site Manager API key: set UNIFI_SITE_MANAGER_API_KEY or UNIFI_API_KEY")
    base = os.environ.get("UNIFI_SITE_MANAGER_BASE_URL", DEFAULT_SITE_MANAGER_BASE)
    return UniFiClient(base, api_key=key, insecure_tls=False)


def make_network_client() -> Tuple[UniFiClient, str]:
    base = os.environ.get("UNIFI_NETWORK_BASE_URL") or os.environ.get("UNIFI_BASE_URL")
    if not base:
        raise UniFiError("Missing local Network API base URL: set UNIFI_NETWORK_BASE_URL")
    key = api_key_for("UNIFI_NETWORK_API_KEY", "UNIFI_API_KEY")
    if not key:
        raise UniFiError("Missing local Network API key: set UNIFI_NETWORK_API_KEY or UNIFI_API_KEY")
    insecure = env_bool("UNIFI_INSECURE_TLS")
    prefix = os.environ.get("UNIFI_NETWORK_PREFIX", DEFAULT_NETWORK_PREFIX)
    return UniFiClient(base, api_key=key, insecure_tls=insecure), prefix


def make_legacy_client() -> UniFiClient:
    base = os.environ.get("UNIFI_LEGACY_BASE_URL") or os.environ.get("UNIFI_NETWORK_BASE_URL") or os.environ.get("UNIFI_BASE_URL")
    if not base:
        raise UniFiError("Missing legacy base URL: set UNIFI_LEGACY_BASE_URL or UNIFI_NETWORK_BASE_URL")
    client = UniFiClient(base, insecure_tls=env_bool("UNIFI_INSECURE_TLS"))
    username = os.environ.get("UNIFI_USERNAME")
    password = os.environ.get("UNIFI_PASSWORD")
    if not username or not password:
        raise UniFiError("Missing legacy credentials: set UNIFI_USERNAME and UNIFI_PASSWORD")
    login_body = {"username": username, "password": password}
    errors = []
    for route in ("/api/auth/login", "/api/login"):
        try:
            client.request("POST", route, body=login_body)
            return client
        except UniFiError as exc:
            errors.append({"route": route, "status": exc.status, "body": exc.body})
    raise UniFiError("Legacy login failed on /api/auth/login and /api/login", body=errors)


def command_env(_args: argparse.Namespace) -> None:
    data = {
        "env_files_checked": [
            str(Path.home() / ".openclaw" / "unifi.env"),
            str(Path.home() / ".openclaw" / ".env"),
            str(Path.home() / ".openclaw" / "openclaw.env"),
            str(Path.home() / ".openclaw" / "workspace" / ".env"),
            str(skill_root() / ".env"),
        ],
        "site_manager": {
            "base_url": os.environ.get("UNIFI_SITE_MANAGER_BASE_URL", DEFAULT_SITE_MANAGER_BASE),
            "api_key": redacted(api_key_for("UNIFI_SITE_MANAGER_API_KEY", "UNIFI_API_KEY")),
        },
        "network": {
            "base_url": os.environ.get("UNIFI_NETWORK_BASE_URL") or os.environ.get("UNIFI_BASE_URL") or "missing",
            "prefix": os.environ.get("UNIFI_NETWORK_PREFIX", DEFAULT_NETWORK_PREFIX),
            "api_key": redacted(api_key_for("UNIFI_NETWORK_API_KEY", "UNIFI_API_KEY")),
            "insecure_tls": env_bool("UNIFI_INSECURE_TLS"),
        },
        "legacy": {
            "base_url": os.environ.get("UNIFI_LEGACY_BASE_URL") or os.environ.get("UNIFI_NETWORK_BASE_URL") or os.environ.get("UNIFI_BASE_URL") or "missing",
            "username": redacted(os.environ.get("UNIFI_USERNAME")),
            "password": redacted(os.environ.get("UNIFI_PASSWORD")),
            "site": os.environ.get("UNIFI_SITE", "default"),
            "insecure_tls": env_bool("UNIFI_INSECURE_TLS"),
        },
    }
    json_print(data)


def command_site_manager_get(args: argparse.Namespace) -> None:
    json_print(make_site_manager_client().request("GET", args.path))


def command_site_manager_post(args: argparse.Namespace) -> None:
    require_write_ack(args)
    json_print(make_site_manager_client().request("POST", args.path, body=parse_json_body(args.body)))


def command_network_get(args: argparse.Namespace) -> None:
    client, prefix = make_network_client()
    json_print(client.request("GET", join_prefix(prefix, args.path)))


def command_network_post(args: argparse.Namespace) -> None:
    require_write_ack(args)
    client, prefix = make_network_client()
    json_print(client.request("POST", join_prefix(prefix, args.path), body=parse_json_body(args.body)))


def legacy_site(args: argparse.Namespace) -> str:
    return args.site or os.environ.get("UNIFI_SITE", "default")


def command_legacy_get(args: argparse.Namespace) -> None:
    json_print(make_legacy_client().request("GET", args.path))


def command_legacy_post(args: argparse.Namespace) -> None:
    require_write_ack(args)
    json_print(make_legacy_client().request("POST", args.path, body=parse_json_body(args.body)))


def command_legacy_sites(_args: argparse.Namespace) -> None:
    client = make_legacy_client()
    errors = []
    for path in ("/api/self/sites", "/proxy/network/api/self/sites"):
        try:
            json_print(client.request("GET", path))
            return
        except UniFiError as exc:
            errors.append({"path": path, "status": exc.status, "body": exc.body})
    raise UniFiError("Could not list legacy sites", body=errors)


def command_legacy_clients(args: argparse.Namespace) -> None:
    site = legacy_site(args)
    client = make_legacy_client()
    errors = []
    for path in (f"/api/s/{site}/stat/sta", f"/proxy/network/api/s/{site}/stat/sta"):
        try:
            json_print(client.request("GET", path))
            return
        except UniFiError as exc:
            errors.append({"path": path, "status": exc.status, "body": exc.body})
    raise UniFiError(f"Could not list clients for site {site}", body=errors)


def command_legacy_devices(args: argparse.Namespace) -> None:
    site = legacy_site(args)
    client = make_legacy_client()
    errors = []
    for path in (f"/api/s/{site}/stat/device", f"/proxy/network/api/s/{site}/stat/device"):
        try:
            json_print(client.request("GET", path))
            return
        except UniFiError as exc:
            errors.append({"path": path, "status": exc.status, "body": exc.body})
    raise UniFiError(f"Could not list devices for site {site}", body=errors)


def require_write_ack(args: argparse.Namespace) -> None:
    if not getattr(args, "yes_I_understand", False):
        raise UniFiError("POST/write refused. Re-run with --yes-I-understand after verifying the target object and rollback path.")


def add_body_and_ack(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--body", required=True, help="JSON body, or @path/to/body.json")
    parser.add_argument("--yes-I-understand", action="store_true", help="Required for POST/write operations")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="UniFi API helper for OpenClaw skills")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("env", help="Show detected config with secrets redacted")
    p.set_defaults(func=command_env)

    p = sub.add_parser("site-manager-get", help="GET from https://api.ui.com/v1")
    p.add_argument("path")
    p.set_defaults(func=command_site_manager_get)

    p = sub.add_parser("site-manager-post", help="POST to https://api.ui.com/v1")
    p.add_argument("path")
    add_body_and_ack(p)
    p.set_defaults(func=command_site_manager_post)

    p = sub.add_parser("network-get", help="GET from official local Network Integration API")
    p.add_argument("path")
    p.set_defaults(func=command_network_get)

    p = sub.add_parser("network-post", help="POST to official local Network Integration API")
    p.add_argument("path")
    add_body_and_ack(p)
    p.set_defaults(func=command_network_post)

    p = sub.add_parser("legacy-get", help="GET from private legacy Network Application API")
    p.add_argument("path")
    p.set_defaults(func=command_legacy_get)

    p = sub.add_parser("legacy-post", help="POST to private legacy Network Application API")
    p.add_argument("path")
    add_body_and_ack(p)
    p.set_defaults(func=command_legacy_post)

    p = sub.add_parser("legacy-sites", help="List legacy sites")
    p.set_defaults(func=command_legacy_sites)

    p = sub.add_parser("legacy-clients", help="List clients from a legacy site")
    p.add_argument("--site", default=None)
    p.set_defaults(func=command_legacy_clients)

    p = sub.add_parser("legacy-devices", help="List devices from a legacy site")
    p.add_argument("--site", default=None)
    p.set_defaults(func=command_legacy_devices)

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    load_env_files()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
        return 0
    except UniFiError as exc:
        json_print(
            {
                "ok": False,
                "error": str(exc),
                "status": exc.status,
                "url": exc.url,
                "body": exc.body,
            }
        )
        return 1
    except KeyboardInterrupt:
        json_print({"ok": False, "error": "interrupted"})
        return 130


if __name__ == "__main__":
    sys.exit(main())