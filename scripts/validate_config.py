#!/usr/bin/env python3
"""Validate a .coderabbit.yaml against the CodeRabbit v2 JSON schema.

Usage:
    python3 validate_config.py [path/to/.coderabbit.yaml] [--refresh]

Reports two classes of problem:
  ERROR   — the config is invalid and CodeRabbit will reject it
  WARNING — the key is unknown at that position, so it parses but never takes effect

Exit codes: 0 clean, 1 errors found, 2 could not run (missing PyYAML or no schema).
"""

import json
import os
import subprocess
import sys
import time
import urllib.request

SCHEMA_URL = "https://coderabbit.ai/integrations/schema.v2.json"
CACHE = os.path.join(
    os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")),
    "coderabbit-schema.v2.json",
)
MAX_CACHE_AGE = 7 * 24 * 3600

TYPE_MAP = {
    "string": str,
    "boolean": bool,
    "integer": int,
    "number": (int, float),
    "array": list,
    "object": dict,
}


def fetch(url):
    """Fetch over urllib, falling back to curl when the local TLS stack is too old."""
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            return resp.read()
    except Exception:  # noqa: BLE001 - retry with curl before giving up
        return subprocess.run(
            ["curl", "-sSfL", "--max-time", "20", url],
            check=True,
            capture_output=True,
        ).stdout


def load_schema(refresh=False):
    if not refresh and os.path.exists(CACHE) and time.time() - os.path.getmtime(CACHE) < MAX_CACHE_AGE:
        with open(CACHE) as fh:
            return json.load(fh)
    try:
        raw = fetch(SCHEMA_URL)
        os.makedirs(os.path.dirname(CACHE), exist_ok=True)
        with open(CACHE, "wb") as fh:
            fh.write(raw)
        return json.loads(raw)
    except Exception as exc:  # noqa: BLE001 - fall back to a stale cache if we have one
        if os.path.exists(CACHE):
            print(f"note: could not fetch schema ({exc}); using cached copy", file=sys.stderr)
            with open(CACHE) as fh:
                return json.load(fh)
        print(f"error: could not fetch schema from {SCHEMA_URL}: {exc}", file=sys.stderr)
        sys.exit(2)


def type_ok(value, expected):
    py = TYPE_MAP.get(expected)
    if py is None:
        return True
    if expected in ("integer", "number") and isinstance(value, bool):
        return False
    return isinstance(value, py)


def validate(node, schema, path, errors, warnings):
    if not isinstance(schema, dict):
        return

    expected = schema.get("type")
    if expected and not type_ok(node, expected):
        got = type(node).__name__
        hint = ""
        if expected == "string" and isinstance(node, bool):
            hint = '  (YAML reads bare `off`/`on` as a boolean — quote it: mode: "off")'
        errors.append(f'{path}: expected {expected}, got {got}{hint}')
        return

    if "enum" in schema and node not in schema["enum"]:
        errors.append(f'{path}: {node!r} is not one of {schema["enum"]}')
        return

    if isinstance(node, dict) and "properties" in schema:
        props = schema["properties"]
        strict = schema.get("additionalProperties") is False
        for key, value in node.items():
            child_path = f"{path}.{key}" if path else key
            if key not in props:
                msg = f"{child_path}: unknown key"
                if strict:
                    errors.append(msg + " — CodeRabbit rejects unknown keys here")
                else:
                    warnings.append(msg + " — parses, but has no effect (check nesting/spelling)")
                continue
            validate(value, props[key], child_path, errors, warnings)

    if isinstance(node, list):
        items = schema.get("items")
        if isinstance(items, dict) and "anyOf" not in items:
            for i, item in enumerate(node):
                validate(item, items, f"{path}[{i}]", errors, warnings)
        if "maxItems" in schema and len(node) > schema["maxItems"]:
            errors.append(f'{path}: {len(node)} items exceeds the maximum of {schema["maxItems"]}')


def main():
    args = [a for a in sys.argv[1:] if a != "--refresh"]
    refresh = "--refresh" in sys.argv[1:]
    target = args[0] if args else ".coderabbit.yaml"

    try:
        import yaml  # noqa: PLC0415 - optional dependency, checked at runtime
    except ImportError:
        print(
            "error: PyYAML is required.\n"
            "  pip install pyyaml   (or:  python3 -m pip install --user pyyaml)\n"
            "Skipping validation — check keys against references/schema-reference.md by hand.",
            file=sys.stderr,
        )
        sys.exit(2)

    if not os.path.exists(target):
        print(f"error: {target} not found", file=sys.stderr)
        sys.exit(2)

    with open(target) as fh:
        try:
            config = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            print(f"error: {target} is not valid YAML:\n{exc}", file=sys.stderr)
            sys.exit(1)

    if config is None:
        print(f"error: {target} is empty", file=sys.stderr)
        sys.exit(1)

    errors, warnings = [], []
    validate(config, load_schema(refresh), "", errors, warnings)

    for w in warnings:
        print(f"WARNING  {w}")
    for e in errors:
        print(f"ERROR    {e}")

    if errors:
        print(f"\n{target}: {len(errors)} error(s), {len(warnings)} warning(s)")
        sys.exit(1)
    print(f"\n{target}: valid ({len(warnings)} warning(s))")
    sys.exit(0)


if __name__ == "__main__":
    main()
