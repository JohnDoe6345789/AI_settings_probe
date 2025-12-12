#!/usr/bin/env python3
"""
Local Assistant Probe

Purpose:
- Probe a local OpenAI-compatible API (e.g., Open WebUI) using trial-and-error
  to discover working settings for Continue config.yaml.
- Output a YAML snippet you can paste into Continue.

Design constraints:
- Small functions (<=10 lines), typed, IO at edges, safe defaults.
- No external dependencies (uses stdlib only).

Usage:
  # Using command-line arguments:
  python -m local_assistant_probe.probe --host localhost --port 3000 --api-key sk-... --model-hint llama3

  # Using .env file (recommended):
  cp .env.example .env
  # Edit .env with your settings
  python -m local_assistant_probe.probe

Environment Variables:
  PROBE_HOST        - API host (default: localhost)
  PROBE_PORT        - API port (default: 3000)
  PROBE_API_KEY     - API key (required)
  PROBE_MODEL_HINT  - Model hint to search for (default: llama3)
  PROBE_TITLE       - Configuration title (default: Local Assistant)
  PROBE_MODEL_NAME  - Model name for output (default: LLama3)
  PROBE_TIMEOUT     - Request timeout in seconds (default: 3.0)
  PROBE_DEBUG       - Enable debug output (default: false)

Notes:
- Command-line arguments override environment variables.
- This script will NOT modify your current working directory.
- It prints YAML to stdout by default.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_CONTEXT: List[Dict[str, str]] = [
    {"provider": "code"},
    {"provider": "docs"},
    {"provider": "diff"},
    {"provider": "terminal"},
    {"provider": "problems"},
    {"provider": "folder"},
    {"provider": "codebase"},
]


@dataclass(frozen=True)
class ProbeResult:
    api_base: str
    model: str
    use_legacy_completions_endpoint: bool


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Dict[str, str]
    body: bytes


def _join(base: str, path: str) -> str:
    base2 = base[:-1] if base.endswith("/") else base
    path2 = path if path.startswith("/") else f"/{path}"
    return f"{base2}{path2}"


def _http_request(
    method: str,
    url: str,
    headers: Dict[str, str],
    data: Optional[bytes],
    timeout_s: float,
) -> HttpResponse:
    req = urllib.request.Request(url=url, data=data, method=method)
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            body = resp.read()
            hdrs = {k.lower(): v for k, v in resp.headers.items()}
            return HttpResponse(status=resp.status, headers=hdrs, body=body)
    except urllib.error.HTTPError as e:
        body = e.read() if hasattr(e, "read") else b""
        hdrs = {k.lower(): v for k, v in getattr(e, "headers", {}).items()}
        return HttpResponse(status=int(e.code), headers=hdrs, body=body)


def _auth_headers(api_key: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def _try_json(resp: HttpResponse) -> Optional[Any]:
    if not resp.body:
        return None
    try:
        return json.loads(resp.body.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return None


def _extract_model_ids(payload: Any) -> List[str]:
    if isinstance(payload, dict) and "data" in payload and isinstance(payload["data"], list):
        return [str(x.get("id")) for x in payload["data"] if isinstance(x, dict) and "id" in x]
    if isinstance(payload, dict) and "models" in payload and isinstance(payload["models"], list):
        return [str(x.get("id") or x.get("name")) for x in payload["models"] if isinstance(x, dict)]
    if isinstance(payload, list):
        return [str(x.get("id") or x.get("name")) for x in payload if isinstance(x, dict)]
    return []


def _pick_model(model_ids: Sequence[str], hint: str) -> Optional[str]:
    if not model_ids:
        return None
    if hint:
        for mid in model_ids:
            if hint.lower() in mid.lower():
                return mid
    return model_ids[0]


def _candidate_api_bases(host: str, port: int) -> List[str]:
    root = f"http://{host}:{port}"
    return [
        f"{root}/api",
        f"{root}/v1",
        f"{root}/api/openai/v1",
        f"{root}/api/openai/v1",  # intentional duplicate to preserve ordering
        root,
    ]


def _probe_models(
    api_base: str,
    api_key: str,
    timeout_s: float,
) -> Tuple[Optional[List[str]], str]:
    url = _join(api_base, "/models")
    resp = _http_request("GET", url, _auth_headers(api_key), None, timeout_s)
    payload = _try_json(resp)
    ids = _extract_model_ids(payload) if resp.status == 200 else None
    return ids, f"{url} -> {resp.status}"


def _chat_payload(model: str) -> bytes:
    obj = {"model": model, "messages": [{"role": "user", "content": "ping"}], "stream": False}
    return json.dumps(obj).encode("utf-8")


def _probe_chat(api_base: str, api_key: str, model: str, timeout_s: float) -> Tuple[bool, str]:
    url = _join(api_base, "/chat/completions")
    resp = _http_request("POST", url, _auth_headers(api_key), _chat_payload(model), timeout_s)
    ok = resp.status == 200 and _try_json(resp) is not None
    return ok, f"{url} -> {resp.status}"


def _probe_legacy_completions(
    api_base: str,
    api_key: str,
    model: str,
    timeout_s: float,
) -> Tuple[bool, str]:
    url = _join(api_base, "/completions")
    body = json.dumps({"model": model, "prompt": "ping", "max_tokens": 8}).encode("utf-8")
    resp = _http_request("POST", url, _auth_headers(api_key), body, timeout_s)
    ok = resp.status == 200 and _try_json(resp) is not None
    return ok, f"{url} -> {resp.status}"


def _yaml_quote(s: str) -> str:
    s2 = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s2}"'


def _render_yaml(result: ProbeResult, api_key: str, title: str, model_name: str) -> str:
    lines: List[str] = []
    lines.append(f"name: {title}")
    lines.append("version: 1.0.0")
    lines.append("schema: v1")
    lines.append("models:")
    lines.append(f"  - name: {model_name}")
    lines.append("    provider: openai")
    lines.append(f"    model: {result.model}")
    lines.append("    env:")
    lines.append(
        f"      useLegacyCompletionsEndpoint: "
        f"{'true' if result.use_legacy_completions_endpoint else 'false'}"
    )
    lines.append(f"    apiBase: {result.api_base}")
    lines.append(f"    apiKey: {_yaml_quote(api_key)}")
    lines.append("    roles:")
    lines.append("      - chat")
    lines.append("      - edit")
    lines.append("context:")
    for item in DEFAULT_CONTEXT:
        lines.append(f"  - provider: {item['provider']}")
    lines.append("")
    return "\n".join(lines)


def _best_effort_probe(
    host: str,
    port: int,
    api_key: str,
    model_hint: str,
    timeout_s: float,
) -> Tuple[Optional[ProbeResult], List[str]]:
    notes: List[str] = []
    for base in _candidate_api_bases(host, port):
        ids, n1 = _probe_models(base, api_key, timeout_s)
        notes.append(n1)
        model = _pick_model(ids or [], model_hint) if ids is not None else None
        if not model:
            continue
        ok, n2 = _probe_chat(base, api_key, model, timeout_s)
        notes.append(n2)
        if ok:
            return ProbeResult(base, model, False), notes
        ok2, n3 = _probe_legacy_completions(base, api_key, model, timeout_s)
        notes.append(n3)
        if ok2:
            return ProbeResult(base, model, True), notes
    return None, notes


def _load_env() -> None:
    env_path = Path(".env")
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def _str_to_bool(val: str) -> bool:
    return val.lower() in ("true", "1", "yes", "on")


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default=os.getenv("PROBE_HOST", "localhost"))
    p.add_argument("--port", type=int, default=int(os.getenv("PROBE_PORT", "3000")))
    p.add_argument("--api-key", default=os.getenv("PROBE_API_KEY"), required=not os.getenv("PROBE_API_KEY"))
    p.add_argument("--model-hint", default=os.getenv("PROBE_MODEL_HINT", "llama3"))
    p.add_argument("--title", default=os.getenv("PROBE_TITLE", "Local Assistant"))
    p.add_argument("--model-name", default=os.getenv("PROBE_MODEL_NAME", "LLama3"))
    p.add_argument("--timeout", type=float, default=float(os.getenv("PROBE_TIMEOUT", "3.0")))
    p.add_argument("--debug", action="store_true", default=_str_to_bool(os.getenv("PROBE_DEBUG", "false")))
    return p.parse_args(list(argv))


def main(argv: Sequence[str]) -> int:
    _load_env()
    args = _parse_args(argv)
    res, notes = _best_effort_probe(
        host=args.host,
        port=args.port,
        api_key=args.api_key,
        model_hint=args.model_hint,
        timeout_s=args.timeout,
    )
    if args.debug:
        for n in notes:
            print(f"# {n}", file=sys.stderr)
    if not res:
        print("ERROR: Could not find a working OpenAI-compatible endpoint.", file=sys.stderr)
        if not args.debug:
            print("Tip: rerun with --debug to see attempted endpoints.", file=sys.stderr)
        return 2
    yaml = _render_yaml(res, args.api_key, args.title, args.model_name)
    sys.stdout.write(yaml)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
