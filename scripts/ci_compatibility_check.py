#!/usr/bin/env python3
"""
scripts/ci_compatibility_check.py
==================================

RAE-Suite CI compatibility gate.

Simulates breaking-change detection across three surfaces:

  1. OpenAPI specs           (old vs new revision)
  2. Protobuf definitions    (old vs new revision, directory diff)
  3. Mandatory claims policy (rollout governance for newly-required claims)

This is intentionally a *simulation* / heuristic engine, not a byte-perfect
reimplementation of tools like `oasdiff` or `buf breaking`. It catches the
common, high-impact breaking patterns and enforces an explicit organizational
policy for rolling out new mandatory claims.

Design notes / limitations
--------------------------
  * Only local OpenAPI `$ref`s (`#/...`) are resolved. External refs
    (`other.yaml#/Foo`) are skipped and surfaced as INFO findings
    (rule EXTERNAL_REF_UNRESOLVED) instead of being silently ignored.
  * Recursive schemas (self-referential $refs) are handled via identity-based
    cycle detection; a given (old, new) schema pair is diffed exactly once.
  * The proto parser is regex-based but strips `//` and `/* */` comments and
    unwraps `oneof` blocks before field extraction. Comment-stripping is not
    string-literal-aware, so `//` inside a string default may truncate that
    string (field-level detection is unaffected).
  * Finding fingerprints are intentionally *precise* (domain|rule|location).
    They are stable across runs for the same finding, and waivers apply to
    exactly one finding — never to a class of findings.

Exit codes
----------
  0  -> No breaking findings (warnings allowed unless --fail-on-warning)
  1  -> Breaking findings present (and not waived)
  2  -> Tool/config/input error (bad files, bad policy, etc.)

Usage
-----
  python scripts/ci_compatibility_check.py \\
      --openapi-old specs/openapi/v1.old.yaml \\
      --openapi-new specs/openapi/v1.new.yaml \\
      --claims-schema-name TokenClaims \\
      --proto-old-dir proto/old \\
      --proto-new-dir proto/new \\
      --claims-policy policy/claims_rollout.yaml \\
      --waiver-file policy/waivers.yaml \\
      --json-report build/compat_report.json

  # Smoke-test the engine itself with embedded sample data:
  python scripts/ci_compatibility_check.py --self-test
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import yaml  # PyYAML
except ImportError:  # pragma: no cover
    yaml = None

VERSION = "1.1.0"

EXIT_OK = 0
EXIT_BREAKING = 1
EXIT_ERROR = 2

DEFAULT_MIN_ROLLOUT_DAYS = 30
DEFAULT_CLAIMS_SCHEMA_NAME = "TokenClaims"

# Exceptions that indicate bad user input / validation problems (vs. bugs).
_INPUT_ERRORS = (FileNotFoundError, ValueError, KeyError, TypeError)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class Severity(IntEnum):
    INFO = 0
    WARNING = 1
    BREAKING = 2

    @property
    def label(self) -> str:
        return self.name

    @property
    def color(self) -> str:
        return {
            Severity.INFO: "\033[36m",      # cyan
            Severity.WARNING: "\033[33m",   # yellow
            Severity.BREAKING: "\033[31m",  # red
        }[self]


@dataclass
class Finding:
    rule_id: str
    severity: Severity
    domain: str          # "openapi" | "proto" | "claims"
    location: str
    message: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    waived: bool = False
    waiver_reason: Optional[str] = None

    @property
    def fingerprint(self) -> str:
        # Intentionally precise: a waiver suppresses exactly one finding.
        raw = f"{self.domain}|{self.rule_id}|{self.location}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.label
        d["fingerprint"] = self.fingerprint
        return d


# ---------------------------------------------------------------------------
# Generic utilities
# ---------------------------------------------------------------------------

def _require_yaml() -> None:
    if yaml is None:
        raise RuntimeError(
            "PyYAML is required to parse YAML files. Install it with "
            "'pip install pyyaml', or convert inputs to JSON."
        )


def load_data_file(path: Optional[str]) -> Any:
    """Load a YAML or JSON file into a Python structure."""
    if path is None:
        return None
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {path}")
    text = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    if suffix == ".json":
        return json.loads(text)
    if suffix in (".yaml", ".yml"):
        _require_yaml()
        try:
            return yaml.safe_load(text)
        except Exception as exc:
            raise ValueError(f"YAML parse error in {path}: {exc}") from exc
    # Unknown extension: try YAML (superset of JSON), then JSON.
    if yaml is not None:
        try:
            return yaml.safe_load(text)
        except Exception:
            pass
    return json.loads(text)


def ensure_mapping(data: Any, what: str) -> Dict[str, Any]:
    """Validate that a loaded document is a non-empty mapping."""
    if data is None:
        raise ValueError(f"{what}: document is empty")
    if not isinstance(data, dict):
        raise ValueError(
            f"{what}: expected a mapping/object at top level, "
            f"got {type(data).__name__}"
        )
    return data


def parse_date(value: Any) -> date:
    # NOTE: datetime is a subclass of date — check it FIRST so YAML
    # timestamps like `2024-01-01T00:00:00` normalize to plain dates.
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    raise ValueError(f"Cannot parse date from value: {value!r}")


def resolve_schema(
    schema: Any,
    root: Dict[str, Any],
    _depth: int = 0,
    _external_refs: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """Resolve a local `$ref` (`#/...`) against the root document. Best-effort.

    External refs are recorded in `_external_refs` (if provided) and resolve
    to {} so callers skip them gracefully instead of diffing garbage.
    """
    if not isinstance(schema, dict):
        return {}
    if _depth > 20:
        return schema
    if "$ref" in schema:
        ref = schema["$ref"]
        if isinstance(ref, str):
            if ref.startswith("#/"):
                node: Any = root
                for part in ref[2:].split("/"):
                    node = node.get(part, {}) if isinstance(node, dict) else {}
                return resolve_schema(node, root, _depth + 1, _external_refs)
            if _external_refs is not None:
                _external_refs.add(ref)
        return {}
    return schema


# Shared sentinel for "no schema". A singleton (rather than a fresh `{}` per
# call) keeps identity-based cycle detection sound for recursive schemas.
_EMPTY_SCHEMA: Dict[str, Any] = {}


# ---------------------------------------------------------------------------
# OpenAPI compatibility engine
# ---------------------------------------------------------------------------

HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def diff_schema(
    old_schema: Any,
    new_schema: Any,
    root_old: Dict[str, Any],
    root_new: Dict[str, Any],
    location: str,
    direction: str,               # "request" | "response"
    findings: List[Finding],
    visited: Optional[Set[Tuple[int, int]]] = None,
    external_refs: Optional[Set[str]] = None,
) -> None:
    """Recursively diff two (possibly $ref'd) JSON schemas.

    Cycle safety: keyed on resolved-object identity, so self-referential
    schemas terminate and each (old, new) pair is diffed exactly once.
    """
    if visited is None:
        visited = set()

    old_schema = resolve_schema(old_schema, root_old, _external_refs=external_refs) or _EMPTY_SCHEMA
    new_schema = resolve_schema(new_schema, root_new, _external_refs=external_refs) or _EMPTY_SCHEMA

    visit_key = (id(old_schema), id(new_schema))
    if visit_key in visited:
        return
    visited.add(visit_key)

    old_type = old_schema.get("type")
    new_type = new_schema.get("type")
    if old_type and new_type and old_type != new_type:
        findings.append(Finding(
            rule_id="SCHEMA_TYPE_CHANGED",
            severity=Severity.BREAKING,
            domain="openapi",
            location=location,
            message=f"Type changed from '{old_type}' to '{new_type}'",
            old_value=str(old_type),
            new_value=str(new_type),
        ))

    old_enum = set(old_schema.get("enum") or [])
    new_enum = set(new_schema.get("enum") or [])
    removed_enum = old_enum - new_enum
    if removed_enum:
        findings.append(Finding(
            rule_id="ENUM_VALUE_REMOVED",
            severity=Severity.BREAKING,
            domain="openapi",
            location=location,
            message=f"Enum values removed: {sorted(map(str, removed_enum))}",
        ))
    added_enum = new_enum - old_enum
    if added_enum:
        findings.append(Finding(
            rule_id="ENUM_VALUE_ADDED",
            severity=Severity.INFO,
            domain="openapi",
            location=location,
            message=f"Enum values added: {sorted(map(str, added_enum))}",
        ))

    old_props: Dict[str, Any] = old_schema.get("properties") or {}
    new_props: Dict[str, Any] = new_schema.get("properties") or {}
    old_required: Set[str] = set(old_schema.get("required") or [])
    new_required: Set[str] = set(new_schema.get("required") or [])

    # Fields removed
    for name in old_props:
        child_loc = f"{location}.{name}"
        if name not in new_props:
            sev = Severity.BREAKING if direction == "response" else Severity.WARNING
            findings.append(Finding(
                rule_id="FIELD_REMOVED",
                severity=sev,
                domain="openapi",
                location=child_loc,
                message=(
                    f"Field '{name}' removed from {direction} schema"
                    + (" (clients may depend on it)" if direction == "response" else
                       " (server no longer reads it; ensure this is intentional)")
                ),
            ))
        else:
            diff_schema(old_props[name], new_props[name], root_old, root_new,
                        child_loc, direction, findings, visited, external_refs)

    # Fields added
    for name in new_props:
        if name not in old_props:
            child_loc = f"{location}.{name}"
            if name in new_required:
                sev = Severity.BREAKING if direction == "request" else Severity.INFO
                findings.append(Finding(
                    rule_id="FIELD_ADDED_REQUIRED",
                    severity=sev,
                    domain="openapi",
                    location=child_loc,
                    message=(
                        f"New REQUIRED field '{name}' added to {direction} schema"
                        + (" — existing clients omitting it will fail" if direction == "request" else "")
                    ),
                ))
            else:
                findings.append(Finding(
                    rule_id="FIELD_ADDED",
                    severity=Severity.INFO,
                    domain="openapi",
                    location=child_loc,
                    message=f"New optional field '{name}' added to {direction} schema",
                ))

    # Required-ness transitions on fields present in both revisions
    newly_required = (new_required - old_required) & set(old_props) & set(new_props)
    for name in newly_required:
        child_loc = f"{location}.{name}"
        if direction == "request":
            findings.append(Finding(
                rule_id="FIELD_BECAME_REQUIRED",
                severity=Severity.BREAKING,
                domain="openapi",
                location=child_loc,
                message=f"Field '{name}' changed from optional to required in request — breaks existing clients",
            ))
        # For responses, becoming required is a *stronger* server guarantee: not breaking.

    newly_optional = (old_required - new_required) & set(old_props) & set(new_props)
    for name in newly_optional:
        child_loc = f"{location}.{name}"
        if direction == "response":
            findings.append(Finding(
                rule_id="FIELD_GUARANTEE_WEAKENED",
                severity=Severity.BREAKING,
                domain="openapi",
                location=child_loc,
                message=f"Field '{name}' is no longer guaranteed present in response (was required)",
            ))
        # For requests, relaxing a requirement is safe for existing clients.

    # Array items
    if old_schema.get("type") == "array" or new_schema.get("type") == "array":
        diff_schema(
            old_schema.get("items", _EMPTY_SCHEMA),
            new_schema.get("items", _EMPTY_SCHEMA),
            root_old, root_new, f"{location}[]", direction, findings, visited, external_refs,
        )


def _content_schema(media_holder: Dict[str, Any]) -> Dict[str, Any]:
    """Extract {content-type: schema} map from a requestBody/response object."""
    content = media_holder.get("content") or {}
    out = {}
    for ctype, body in content.items():
        out[ctype] = (body or {}).get("schema", _EMPTY_SCHEMA) if isinstance(body, dict) else _EMPTY_SCHEMA
    return out


def compare_parameters(
    old_params_raw: List[Any],
    new_params_raw: List[Any],
    root_old: Dict[str, Any],
    root_new: Dict[str, Any],
    location: str,
    findings: List[Finding],
    external_refs: Optional[Set[str]] = None,
) -> None:
    """Diff operation parameters.

    `*_params_raw` should contain path-item-level parameters FIRST and
    operation-level parameters SECOND so the latter override by (name, in).
    $ref'd parameters are resolved before keying.
    """
    def resolved(raw_list: List[Any], root: Dict[str, Any]) -> Dict[Tuple[Any, Any], Dict[str, Any]]:
        out: Dict[Tuple[Any, Any], Dict[str, Any]] = {}
        for p in raw_list:
            rp = resolve_schema(p, root, _external_refs=external_refs)
            if not rp:
                continue
            out[(rp.get("name"), rp.get("in"))] = rp
        return out

    old_params = resolved(old_params_raw, root_old)
    new_params = resolved(new_params_raw, root_new)

    for k, p in old_params.items():
        name, loc_in = k
        ploc = f"{location}.parameters.{loc_in}:{name}"
        if k not in new_params:
            sev = Severity.BREAKING if p.get("required") else Severity.WARNING
            findings.append(Finding(
                rule_id="PARAMETER_REMOVED",
                severity=sev,
                domain="openapi",
                location=ploc,
                message=f"Parameter '{name}' ({loc_in}) removed",
            ))
        else:
            new_p = new_params[k]
            was_req, is_req = bool(p.get("required")), bool(new_p.get("required"))
            if not was_req and is_req:
                findings.append(Finding(
                    rule_id="PARAMETER_BECAME_REQUIRED",
                    severity=Severity.BREAKING,
                    domain="openapi",
                    location=ploc,
                    message=f"Parameter '{name}' ({loc_in}) changed from optional to required",
                ))
            old_psch = resolve_schema(p.get("schema"), root_old, _external_refs=external_refs)
            new_psch = resolve_schema(new_p.get("schema"), root_new, _external_refs=external_refs)
            old_ptype, new_ptype = old_psch.get("type"), new_psch.get("type")
            if old_ptype and new_ptype and old_ptype != new_ptype:
                findings.append(Finding(
                    rule_id="PARAMETER_TYPE_CHANGED",
                    severity=Severity.BREAKING,
                    domain="openapi",
                    location=ploc,
                    message=f"Parameter '{name}' type changed from '{old_ptype}' to '{new_ptype}'",
                ))

    for k, p in new_params.items():
        name, loc_in = k
        if k not in old_params and p.get("required"):
            findings.append(Finding(
                rule_id="PARAMETER_ADDED_REQUIRED",
                severity=Severity.BREAKING,
                domain="openapi",
                location=f"{location}.parameters.{loc_in}:{name}",
                message=f"New REQUIRED parameter '{name}' ({loc_in}) added — breaks existing callers",
            ))


def compare_request_body(old_op, new_op, root_old, root_new, location, findings,
                          external_refs=None):
    old_rb = resolve_schema(old_op.get("requestBody") or {}, root_old, _external_refs=external_refs)
    new_rb = resolve_schema(new_op.get("requestBody") or {}, root_new, _external_refs=external_refs)
    if not old_rb and not new_rb:
        return
    if old_rb and not new_rb:
        findings.append(Finding(
            rule_id="REQUEST_BODY_REMOVED", severity=Severity.WARNING, domain="openapi",
            location=f"{location}.requestBody",
            message="Request body removed (verify server behavior for legacy payloads)",
        ))
        return

    was_required = bool(old_rb.get("required")) if old_rb else False
    is_required = bool(new_rb.get("required")) if new_rb else False
    if not was_required and is_required:
        findings.append(Finding(
            rule_id="REQUEST_BODY_BECAME_REQUIRED", severity=Severity.BREAKING, domain="openapi",
            location=f"{location}.requestBody",
            message="Request body changed from optional to required",
        ))

    old_schemas = _content_schema(old_rb)
    new_schemas = _content_schema(new_rb)
    for ctype, new_schema in new_schemas.items():
        old_schema = old_schemas.get(ctype)
        if old_schema is None:
            continue
        diff_schema(old_schema, new_schema, root_old, root_new,
                    f"{location}.requestBody[{ctype}]", "request", findings,
                    external_refs=external_refs)
    for ctype in old_schemas:
        if ctype not in new_schemas:
            findings.append(Finding(
                rule_id="REQUEST_CONTENT_TYPE_REMOVED", severity=Severity.BREAKING, domain="openapi",
                location=f"{location}.requestBody",
                message=f"Request content-type '{ctype}' no longer accepted",
            ))


def compare_responses(old_op, new_op, root_old, root_new, location, findings,
                       external_refs=None):
    # Normalize status keys to str: YAML parses `200:` as int, `"200":` as str.
    old_resp = {str(k): v for k, v in (old_op.get("responses") or {}).items()}
    new_resp = {str(k): v for k, v in (new_op.get("responses") or {}).items()}

    for status, body in old_resp.items():
        rloc = f"{location}.responses.{status}"
        if status not in new_resp:
            findings.append(Finding(
                rule_id="RESPONSE_STATUS_REMOVED", severity=Severity.BREAKING, domain="openapi",
                location=rloc, message=f"Response status '{status}' removed",
            ))
            continue
        old_body = resolve_schema(body or {}, root_old, _external_refs=external_refs)
        new_body = resolve_schema(new_resp[status] or {}, root_new, _external_refs=external_refs)
        old_schemas = _content_schema(old_body)
        new_schemas = _content_schema(new_body)
        for ctype, old_schema in old_schemas.items():
            new_schema = new_schemas.get(ctype)
            if new_schema is None:
                findings.append(Finding(
                    rule_id="RESPONSE_CONTENT_TYPE_REMOVED", severity=Severity.BREAKING, domain="openapi",
                    location=rloc, message=f"Response content-type '{ctype}' removed for status '{status}'",
                ))
                continue
            diff_schema(old_schema, new_schema, root_old, root_new,
                        f"{rloc}[{ctype}]", "response", findings,
                        external_refs=external_refs)
    for status in new_resp:
        if status not in old_resp:
            findings.append(Finding(
                rule_id="RESPONSE_STATUS_ADDED", severity=Severity.INFO, domain="openapi",
                location=f"{location}.responses.{status}", message=f"New response status '{status}' added",
            ))


def _ops_by_method(path_item: Any) -> Dict[str, Dict[str, Any]]:
    """Normalized {method: operation} map for a path item (lowercased keys)."""
    if not isinstance(path_item, dict):
        return {}
    return {
        m.lower(): op for m, op in path_item.items()
        if isinstance(m, str) and m.lower() in HTTP_METHODS and isinstance(op, dict)
    }


def check_openapi(old_spec: Dict[str, Any], new_spec: Dict[str, Any]) -> List[Finding]:
    findings: List[Finding] = []
    external_refs: Set[str] = set()

    old_paths = old_spec.get("paths", {}) or {}
    new_paths = new_spec.get("paths", {}) or {}
    if not isinstance(old_paths, dict) or not isinstance(new_paths, dict):
        raise ValueError("OpenAPI 'paths' must be a mapping in both specs")

    for path, old_item in old_paths.items():
        if path not in new_paths:
            findings.append(Finding(
                rule_id="PATH_REMOVED", severity=Severity.BREAKING, domain="openapi",
                location=f"paths.{path}", message=f"Path '{path}' removed",
            ))
            continue
        new_item = new_paths[path]
        old_ops = _ops_by_method(old_item)
        new_ops = _ops_by_method(new_item)
        # Path-item-level parameters are shared; operation-level override them.
        old_shared = old_item.get("parameters") or [] if isinstance(old_item, dict) else []
        new_shared = new_item.get("parameters") or [] if isinstance(new_item, dict) else []

        for method, old_op in old_ops.items():
            loc = f"paths.{path}.{method}"
            if method not in new_ops:
                findings.append(Finding(
                    rule_id="OPERATION_REMOVED", severity=Severity.BREAKING, domain="openapi",
                    location=loc, message=f"Operation '{method.upper()} {path}' removed",
                ))
                continue
            new_op = new_ops[method]
            compare_parameters(
                list(old_shared) + list(old_op.get("parameters") or []),
                list(new_shared) + list(new_op.get("parameters") or []),
                old_spec, new_spec, loc, findings, external_refs,
            )
            compare_request_body(old_op, new_op, old_spec, new_spec, loc, findings, external_refs)
            compare_responses(old_op, new_op, old_spec, new_spec, loc, findings, external_refs)

    for path, new_item in new_paths.items():
        if path not in old_paths:
            findings.append(Finding(
                rule_id="PATH_ADDED", severity=Severity.INFO, domain="openapi",
                location=f"paths.{path}", message=f"New path '{path}' added",
            ))
            continue
        old_ops = _ops_by_method(old_paths[path])
        for method in _ops_by_method(new_item):
            if method not in old_ops:
                findings.append(Finding(
                    rule_id="OPERATION_ADDED", severity=Severity.INFO, domain="openapi",
                    location=f"paths.{path}.{method}", message=f"New operation '{method.upper()} {path}' added",
                ))

    for ref in sorted(external_refs):
        findings.append(Finding(
            rule_id="EXTERNAL_REF_UNRESOLVED", severity=Severity.INFO, domain="openapi",
            location=ref,
            message="External $ref not resolved (only local '#/...' refs are supported); "
                    "its schema was skipped",
        ))

    return findings


# ---------------------------------------------------------------------------
# Protobuf compatibility engine (lightweight, regex-based)
# ---------------------------------------------------------------------------

@dataclass
class ProtoField:
    name: str
    number: int
    type: str
    label: str  # "singular" | "repeated" | "optional" | "required"


@dataclass
class ProtoMessage:
    qualified_name: str
    fields_by_number: Dict[int, ProtoField] = field(default_factory=dict)
    reserved_numbers: Set[int] = field(default_factory=set)
    reserved_names: Set[str] = field(default_factory=set)


@dataclass
class ProtoEnum:
    qualified_name: str
    values_by_number: Dict[int, str] = field(default_factory=dict)
    reserved_numbers: Set[int] = field(default_factory=set)


FIELD_RE = re.compile(
    r'^[ \t]*(repeated|optional|required)?\s*([\w\.]+)\s+(\w+)\s*=\s*(\d+)\s*(\[[^\]]*\])?\s*;',
    re.MULTILINE,
)
ENUM_VALUE_RE = re.compile(r'^[ \t]*(\w+)\s*=\s*(-?\d+)\s*(\[[^\]]*\])?\s*;', re.MULTILINE)
RESERVED_RE = re.compile(r'reserved\s+([^;]+);')
PACKAGE_RE = re.compile(r'^\s*package\s+([\w\.]+)\s*;', re.MULTILINE)
ONEOF_RE = re.compile(r'\boneof\s+\w+\s*\{')


def _strip_comments(text: str) -> str:
    """Remove // line and /* */ block comments.

    Prevents commented-out fields/values (e.g. `// string foo = 2;`) from
    being parsed as live declarations. Not string-literal-aware (documented
    heuristic limitation).
    """
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    return re.sub(r'//[^\n]*', '', text)


def _unwrap_oneofs(body: str) -> str:
    """Replace `oneof Name { ... }` with its inner contents (keeping fields)."""
    result: List[str] = []
    idx = 0
    while True:
        m = ONEOF_RE.search(body, idx)
        if not m:
            result.append(body[idx:])
            break
        result.append(body[idx:m.start()])
        start = m.end()
        depth = 1
        j = start
        while j < len(body) and depth > 0:
            if body[j] == "{":
                depth += 1
            elif body[j] == "}":
                depth -= 1
            j += 1
        result.append(body[start:j - 1])  # keep inner field declarations
        idx = j
    return "".join(result)


def _strip_nested_blocks(body: str) -> str:
    """Remove nested `{...}` content (nested messages/enums) leaving top-level lines."""
    out = []
    depth = 0
    for ch in body:
        if ch == "{":
            depth += 1
            continue
        if ch == "}":
            depth -= 1
            continue
        if depth == 0:
            out.append(ch)
    return "".join(out)


def _extract_top_level_blocks(text: str, keyword: str) -> Dict[str, str]:
    """Extract top-level `message Name { ... }` / `enum Name { ... }` bodies (flattened)."""
    blocks: Dict[str, str] = {}
    pattern = re.compile(rf'\b{keyword}\s+(\w+)\s*\{{')
    idx = 0
    while True:
        m = pattern.search(text, idx)
        if not m:
            break
        name = m.group(1)
        start = m.end()
        depth = 1
        j = start
        while j < len(text) and depth > 0:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
            j += 1
        body_full = text[start:j - 1]
        # Unwrap oneofs BEFORE stripping nested blocks so oneof fields survive.
        blocks[name] = _strip_nested_blocks(_unwrap_oneofs(body_full))
        idx = j
    return blocks


def _parse_reserved(body: str) -> Tuple[Set[int], Set[str]]:
    nums: Set[int] = set()
    names: Set[str] = set()
    for m in RESERVED_RE.finditer(body):
        for part in m.group(1).split(","):
            part = part.strip()
            if not part:
                continue
            if part.startswith('"'):
                names.add(part.strip('"'))
            elif " to " in part:
                a, b = part.split(" to ")
                try:
                    nums.update(range(int(a.strip()), int(b.strip()) + 1))
                except ValueError:
                    pass
            elif part.lstrip("-").isdigit():
                nums.add(int(part))
    return nums, names


def parse_proto_text(
    text: str, namespace: str
) -> Tuple[Dict[str, ProtoMessage], Dict[str, ProtoEnum], List[Finding]]:
    """Parse a .proto source string into messages/enums plus parse-level findings."""
    text = _strip_comments(text)
    findings: List[Finding] = []

    pkg_match = PACKAGE_RE.search(text)
    package = pkg_match.group(1) if pkg_match else namespace

    messages: Dict[str, ProtoMessage] = {}
    for name, body in _extract_top_level_blocks(text, "message").items():
        msg = ProtoMessage(qualified_name=f"{package}.{name}")
        msg.reserved_numbers, msg.reserved_names = _parse_reserved(body)
        for m in FIELD_RE.finditer(body):
            label = m.group(1) or "singular"
            ftype, fname, fnum = m.group(2), m.group(3), int(m.group(4))
            if fnum in msg.fields_by_number:
                prev = msg.fields_by_number[fnum]
                findings.append(Finding(
                    rule_id="PROTO_DUPLICATE_FIELD_NUMBER",
                    severity=Severity.BREAKING, domain="proto",
                    location=f"{msg.qualified_name}#{fnum}",
                    message=(
                        f"Duplicate field number #{fnum} in message '{msg.qualified_name}' "
                        f"('{prev.name}' and '{fname}') — file would not compile; "
                        f"keeping first declaration for diffing"
                    ),
                ))
                continue
            msg.fields_by_number[fnum] = ProtoField(name=fname, number=fnum, type=ftype, label=label)
        messages[msg.qualified_name] = msg

    enums: Dict[str, ProtoEnum] = {}
    for name, body in _extract_top_level_blocks(text, "enum").items():
        en = ProtoEnum(qualified_name=f"{package}.{name}")
        en.reserved_numbers, _ = _parse_reserved(body)
        for m in ENUM_VALUE_RE.finditer(body):
            vnum, vname = int(m.group(2)), m.group(1)
            if vnum in en.values_by_number:
                findings.append(Finding(
                    rule_id="PROTO_DUPLICATE_ENUM_NUMBER",
                    severity=Severity.INFO, domain="proto",
                    location=f"{en.qualified_name}#{vnum}",
                    message=(
                        f"Duplicate enum number #{vnum} in '{en.qualified_name}' "
                        f"('{en.values_by_number[vnum]}' and '{vname}') — "
                        f"legal only with allow_alias; keeping first"
                    ),
                ))
                continue
            en.values_by_number[vnum] = vname
        enums[en.qualified_name] = en

    return messages, enums, findings


def parse_proto_dir(
    dir_path: str,
) -> Tuple[Dict[str, ProtoMessage], Dict[str, ProtoEnum], List[Finding]]:
    all_messages: Dict[str, ProtoMessage] = {}
    all_enums: Dict[str, ProtoEnum] = {}
    all_findings: List[Finding] = []
    root = Path(dir_path)
    if not root.exists():
        raise FileNotFoundError(f"Proto directory not found: {dir_path}")
    for proto_file in sorted(root.rglob("*.proto")):
        text = proto_file.read_text(encoding="utf-8")
        messages, enums, parse_findings = parse_proto_text(text, proto_file.stem)
        all_messages.update(messages)
        all_enums.update(enums)
        all_findings.extend(parse_findings)
    return all_messages, all_enums, all_findings


def compare_proto_messages(old_messages: Dict[str, ProtoMessage],
                            new_messages: Dict[str, ProtoMessage]) -> List[Finding]:
    findings: List[Finding] = []

    for qname, old_msg in old_messages.items():
        loc = f"proto.message.{qname}"
        if qname not in new_messages:
            findings.append(Finding(
                rule_id="MESSAGE_REMOVED", severity=Severity.BREAKING, domain="proto",
                location=loc, message=f"Message '{qname}' removed",
            ))
            continue
        new_msg = new_messages[qname]

        for num, old_f in old_msg.fields_by_number.items():
            floc = f"{loc}#{num}"
            if num not in new_msg.fields_by_number:
                if num in new_msg.reserved_numbers or old_f.name in new_msg.reserved_names:
                    findings.append(Finding(
                        rule_id="FIELD_REMOVED_RESERVED", severity=Severity.INFO, domain="proto",
                        location=floc,
                        message=f"Field '{old_f.name}' (#{num}) removed and properly reserved",
                    ))
                else:
                    findings.append(Finding(
                        rule_id="FIELD_REMOVED_UNRESERVED", severity=Severity.BREAKING, domain="proto",
                        location=floc,
                        message=(
                            f"Field '{old_f.name}' (#{num}) removed WITHOUT reservation — "
                            f"risk of field number reuse; add `reserved {num};` and "
                            f"`reserved \"{old_f.name}\";`"
                        ),
                    ))
            else:
                new_f = new_msg.fields_by_number[num]
                if new_f.type != old_f.type and new_f.name != old_f.name:
                    findings.append(Finding(
                        rule_id="FIELD_NUMBER_REUSE_SUSPECTED", severity=Severity.BREAKING, domain="proto",
                        location=floc,
                        message=(
                            f"Field #{num} changed identity entirely "
                            f"('{old_f.name}:{old_f.type}' -> '{new_f.name}:{new_f.type}') — "
                            f"suspected field number reuse"
                        ),
                    ))
                else:
                    if new_f.type != old_f.type:
                        findings.append(Finding(
                            rule_id="FIELD_TYPE_CHANGED", severity=Severity.BREAKING, domain="proto",
                            location=floc,
                            message=f"Field '{old_f.name}' (#{num}) type changed: '{old_f.type}' -> '{new_f.type}'",
                        ))
                    if new_f.label != old_f.label:
                        findings.append(Finding(
                            rule_id="FIELD_CARDINALITY_CHANGED", severity=Severity.BREAKING, domain="proto",
                            location=floc,
                            message=f"Field '{old_f.name}' (#{num}) cardinality changed: "
                                    f"'{old_f.label}' -> '{new_f.label}'",
                        ))
                    if new_f.name != old_f.name:
                        findings.append(Finding(
                            rule_id="FIELD_RENAMED", severity=Severity.WARNING, domain="proto",
                            location=floc,
                            message=f"Field #{num} renamed '{old_f.name}' -> '{new_f.name}' "
                                    f"(wire-compatible, but breaks JSON/text encoding & generated code)",
                        ))

        for num, new_f in new_msg.fields_by_number.items():
            if num not in old_msg.fields_by_number:
                if num in old_msg.reserved_numbers or new_f.name in old_msg.reserved_names:
                    findings.append(Finding(
                        rule_id="RESERVED_FIELD_REUSED", severity=Severity.BREAKING, domain="proto",
                        location=f"{loc}#{num}",
                        message=(
                            f"New field '{new_f.name}' (#{num}) reuses a number/name that was "
                            f"explicitly RESERVED in the old revision — this violates the "
                            f"reservation and risks wire incompatibility with stale data"
                        ),
                    ))
                else:
                    findings.append(Finding(
                        rule_id="FIELD_ADDED", severity=Severity.INFO, domain="proto",
                        location=f"{loc}#{num}", message=f"New field '{new_f.name}' (#{num}) added",
                    ))

    for qname in new_messages:
        if qname not in old_messages:
            findings.append(Finding(
                rule_id="MESSAGE_ADDED", severity=Severity.INFO, domain="proto",
                location=f"proto.message.{qname}", message=f"New message '{qname}' added",
            ))

    return findings


def compare_proto_enums(old_enums: Dict[str, ProtoEnum], new_enums: Dict[str, ProtoEnum]) -> List[Finding]:
    findings: List[Finding] = []
    for qname, old_en in old_enums.items():
        loc = f"proto.enum.{qname}"
        if qname not in new_enums:
            findings.append(Finding(
                rule_id="ENUM_REMOVED", severity=Severity.BREAKING, domain="proto",
                location=loc, message=f"Enum '{qname}' removed",
            ))
            continue
        new_en = new_enums[qname]
        for num, name in old_en.values_by_number.items():
            vloc = f"{loc}#{num}"
            if num not in new_en.values_by_number:
                if num in new_en.reserved_numbers:
                    findings.append(Finding(
                        rule_id="ENUM_VALUE_REMOVED_RESERVED", severity=Severity.INFO, domain="proto",
                        location=vloc, message=f"Enum value '{name}' (#{num}) removed and reserved",
                    ))
                else:
                    findings.append(Finding(
                        rule_id="ENUM_VALUE_REMOVED_UNRESERVED", severity=Severity.BREAKING, domain="proto",
                        location=vloc,
                        message=f"Enum value '{name}' (#{num}) removed without reservation",
                    ))
            elif new_en.values_by_number[num] != name:
                findings.append(Finding(
                    rule_id="ENUM_VALUE_RENUMBERED", severity=Severity.BREAKING, domain="proto",
                    location=vloc,
                    message=f"Enum number #{num} reassigned '{name}' -> '{new_en.values_by_number[num]}'",
                ))
        for num, name in new_en.values_by_number.items():
            if num not in old_en.values_by_number:
                findings.append(Finding(
                    rule_id="ENUM_VALUE_ADDED", severity=Severity.INFO, domain="proto",
                    location=f"{loc}#{num}", message=f"New enum value '{name}' (#{num}) added",
                ))
    return findings


def check_proto(old_dir: str, new_dir: str) -> List[Finding]:
    old_messages, old_enums, old_parse_findings = parse_proto_dir(old_dir)
    new_messages, new_enums, new_parse_findings = parse_proto_dir(new_dir)
    findings: List[Finding] = []
    # Parse-level problems in the NEW revision are gate-relevant; old-side
    # duplicates are informational context for diff accuracy.
    findings.extend(new_parse_findings)
    findings.extend(compare_proto_messages(old_messages, new_messages))
    findings.extend(compare_proto_enums(old_enums, new_enums))
    return findings


# ---------------------------------------------------------------------------
# Mandatory claims rollout policy engine
# ---------------------------------------------------------------------------

@dataclass
class ClaimPolicyEntry:
    name: str
    status: str                 # proposed | rollout | mandatory
    introduced_on: date
    mandatory_on: Optional[date]
    min_rollout_days: Optional[int] = None


def load_claims_policy(policy_data: Dict[str, Any]) -> Tuple[Dict[str, ClaimPolicyEntry], int, List[Finding]]:
    findings: List[Finding] = []
    try:
        global_min_days = int(policy_data.get("min_rollout_days", DEFAULT_MIN_ROLLOUT_DAYS))
    except (TypeError, ValueError):
        findings.append(Finding(
            rule_id="CLAIM_POLICY_MALFORMED", severity=Severity.BREAKING, domain="claims",
            location="claims_policy.min_rollout_days",
            message=f"Global min_rollout_days is not an integer "
                    f"({policy_data.get('min_rollout_days')!r}); using default {DEFAULT_MIN_ROLLOUT_DAYS}",
        ))
        global_min_days = DEFAULT_MIN_ROLLOUT_DAYS

    entries: Dict[str, ClaimPolicyEntry] = {}

    for raw in policy_data.get("claims", []) or []:
        if not isinstance(raw, dict):
            findings.append(Finding(
                rule_id="CLAIM_POLICY_MALFORMED", severity=Severity.BREAKING, domain="claims",
                location="claims_policy", message=f"Claim policy entry is not a mapping: {raw!r}",
            ))
            continue
        name = raw.get("name")
        loc = f"claims_policy.{name or '<unnamed>'}"
        if not name:
            findings.append(Finding(
                rule_id="CLAIM_POLICY_MALFORMED", severity=Severity.BREAKING, domain="claims",
                location="claims_policy", message="Claim policy entry missing 'name'",
            ))
            continue
        if name in entries:
            findings.append(Finding(
                rule_id="DUPLICATE_CLAIM_NAME", severity=Severity.BREAKING, domain="claims",
                location=loc,
                message=f"Duplicate claim name '{name}' in policy — keep exactly one entry per claim",
            ))
            continue
        status = raw.get("status")
        if status not in ("proposed", "rollout", "mandatory"):
            findings.append(Finding(
                rule_id="CLAIM_POLICY_INVALID_STATUS", severity=Severity.BREAKING, domain="claims",
                location=loc, message=f"Invalid status '{status}' (expected proposed|rollout|mandatory)",
            ))
            continue
        try:
            introduced_on = parse_date(raw["introduced_on"])
        except Exception as exc:
            findings.append(Finding(
                rule_id="CLAIM_POLICY_INVALID_DATE", severity=Severity.BREAKING, domain="claims",
                location=loc, message=f"Invalid/missing 'introduced_on': {exc}",
            ))
            continue

        mandatory_on = None
        if status in ("rollout", "mandatory") or raw.get("mandatory_on"):
            try:
                mandatory_on = parse_date(raw["mandatory_on"])
            except Exception as exc:
                findings.append(Finding(
                    rule_id="CLAIM_POLICY_INVALID_DATE", severity=Severity.BREAKING, domain="claims",
                    location=loc, message=f"Invalid/missing 'mandatory_on' for status '{status}': {exc}",
                ))
                continue

        min_days_override = raw.get("min_rollout_days")
        if min_days_override is not None:
            try:
                min_days_override = int(min_days_override)
            except (TypeError, ValueError):
                findings.append(Finding(
                    rule_id="CLAIM_POLICY_MALFORMED", severity=Severity.BREAKING, domain="claims",
                    location=loc,
                    message=f"Per-claim min_rollout_days is not an integer ({raw.get('min_rollout_days')!r})",
                ))
                continue

        entry = ClaimPolicyEntry(
            name=name, status=status, introduced_on=introduced_on, mandatory_on=mandatory_on,
            min_rollout_days=min_days_override,
        )
        entries[name] = entry

        if mandatory_on is not None:
            if mandatory_on < introduced_on:
                findings.append(Finding(
                    rule_id="CLAIM_POLICY_BAD_DATE_ORDER", severity=Severity.BREAKING, domain="claims",
                    location=loc, message="'mandatory_on' precedes 'introduced_on'",
                ))
                continue
            min_days = entry.min_rollout_days if entry.min_rollout_days is not None else global_min_days
            rollout_days = (mandatory_on - introduced_on).days
            if rollout_days < min_days:
                findings.append(Finding(
                    rule_id="CLAIM_ROLLOUT_TOO_SHORT", severity=Severity.BREAKING, domain="claims",
                    location=loc,
                    message=(
                        f"Rollout window is {rollout_days}d, below required minimum of {min_days}d "
                        f"(introduced_on={introduced_on}, mandatory_on={mandatory_on})"
                    ),
                ))

    return entries, global_min_days, findings


def check_claim_enforcement_dates(entries: Dict[str, ClaimPolicyEntry], today: date) -> List[Finding]:
    findings = []
    for name, entry in entries.items():
        loc = f"claims_policy.{name}"
        if entry.status == "mandatory" and entry.mandatory_on and today < entry.mandatory_on:
            findings.append(Finding(
                rule_id="CLAIM_ENFORCED_BEFORE_SCHEDULE", severity=Severity.BREAKING, domain="claims",
                location=loc,
                message=(
                    f"Policy marks '{name}' as mandatory but scheduled mandatory_on="
                    f"{entry.mandatory_on} is still in the future (today={today})"
                ),
            ))
    return findings


def _find_claims_schema(spec: Optional[Dict[str, Any]], schema_name: str) -> Optional[Dict[str, Any]]:
    if not spec:
        return None
    return ((spec.get("components") or {}).get("schemas") or {}).get(schema_name)


def check_claims_against_spec(
    old_spec: Optional[Dict[str, Any]],
    new_spec: Optional[Dict[str, Any]],
    schema_name: str,
    entries: Dict[str, ClaimPolicyEntry],
    today: date,
) -> List[Finding]:
    findings: List[Finding] = []

    if new_spec is None:
        return findings

    old_schema = _find_claims_schema(old_spec, schema_name)
    new_schema = _find_claims_schema(new_spec, schema_name)

    if new_schema is None:
        findings.append(Finding(
            rule_id="CLAIMS_SCHEMA_NOT_FOUND", severity=Severity.INFO, domain="claims",
            location=f"components.schemas.{schema_name}",
            message=f"Claims schema '{schema_name}' not found in new spec — skipping cross-check",
        ))
        return findings

    old_required: Set[str] = set((old_schema or {}).get("required", []) or [])
    new_required: Set[str] = set((new_schema or {}).get("required", []) or [])

    newly_required = new_required - old_required
    for claim in sorted(newly_required):
        loc = f"components.schemas.{schema_name}.required[{claim}]"
        entry = entries.get(claim)
        if entry is None:
            findings.append(Finding(
                rule_id="CLAIM_MADE_MANDATORY_WITHOUT_POLICY", severity=Severity.BREAKING, domain="claims",
                location=loc,
                message=(
                    f"Claim '{claim}' became required in spec but has NO rollout policy entry. "
                    f"Add it to the claims policy with status=rollout before making it mandatory."
                ),
            ))
            continue
        if entry.status != "mandatory":
            findings.append(Finding(
                rule_id="CLAIM_MANDATORY_BEFORE_POLICY_APPROVAL", severity=Severity.BREAKING, domain="claims",
                location=loc,
                message=(
                    f"Spec requires claim '{claim}' but its rollout policy status is "
                    f"'{entry.status}' (must be 'mandatory')"
                ),
            ))
            continue
        if entry.mandatory_on and today < entry.mandatory_on:
            findings.append(Finding(
                rule_id="CLAIM_ENFORCED_BEFORE_SCHEDULE", severity=Severity.BREAKING, domain="claims",
                location=loc,
                message=(
                    f"Spec enforces claim '{claim}' as required before its scheduled "
                    f"mandatory_on date ({entry.mandatory_on}, today={today})"
                ),
            ))

    newly_optional = old_required - new_required
    for claim in sorted(newly_optional):
        findings.append(Finding(
            rule_id="CLAIM_REQUIREMENT_RELAXED", severity=Severity.WARNING, domain="claims",
            location=f"components.schemas.{schema_name}.required[{claim}]",
            message=f"Claim '{claim}' is no longer required — review for security regression",
        ))

    return findings


def check_claims_policy(
    policy_data: Dict[str, Any],
    old_spec: Optional[Dict[str, Any]],
    new_spec: Optional[Dict[str, Any]],
    schema_name: str,
    today: date,
    min_days_override: Optional[int],
) -> List[Finding]:
    findings: List[Finding] = []
    if min_days_override is not None:
        policy_data = dict(policy_data)
        policy_data["min_rollout_days"] = min_days_override

    entries, _min_days, policy_findings = load_claims_policy(policy_data)
    findings.extend(policy_findings)
    findings.extend(check_claim_enforcement_dates(entries, today))
    findings.extend(check_claims_against_spec(old_spec, new_spec, schema_name, entries, today))
    return findings


# ---------------------------------------------------------------------------
# Waivers
# ---------------------------------------------------------------------------

def load_waivers(path: Optional[str], today: date) -> Dict[str, Dict[str, Any]]:
    if not path:
        return {}
    data = ensure_mapping(load_data_file(path), f"Waiver file '{path}'")
    result: Dict[str, Dict[str, Any]] = {}
    for w in data.get("waivers", []) or []:
        if not isinstance(w, dict):
            continue
        fp = w.get("fingerprint")
        if not fp:
            continue
        expires_on = w.get("expires_on")
        expired = False
        if expires_on:
            try:
                expired = today > parse_date(expires_on)
            except Exception:
                pass
        result[fp] = {"reason": w.get("reason", ""), "expired": expired, "expires_on": expires_on}
    return result


def apply_waivers(findings: List[Finding], waivers: Dict[str, Dict[str, Any]]) -> List[Finding]:
    for f in findings:
        w = waivers.get(f.fingerprint)
        if not w:
            continue
        if w["expired"]:
            # Governance hygiene: an expired waiver silently lapsing back to
            # "active" is correct, but worth surfacing in CI logs.
            print(
                f"NOTE: waiver {f.fingerprint} ({f.rule_id} @ {f.location}) "
                f"expired on {w.get('expires_on')} — finding is ACTIVE",
                file=sys.stderr,
            )
        else:
            f.waived = True
            f.waiver_reason = w["reason"]
    return findings


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _color(text: str, code: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{code}{text}\033[0m"


def summarize(findings: List[Finding]) -> Dict[str, int]:
    return {
        "total": len(findings),
        "breaking_active": sum(1 for f in findings if f.severity == Severity.BREAKING and not f.waived),
        "breaking_waived": sum(1 for f in findings if f.severity == Severity.BREAKING and f.waived),
        "warning_active": sum(1 for f in findings if f.severity == Severity.WARNING and not f.waived),
        "warning_waived": sum(1 for f in findings if f.severity == Severity.WARNING and f.waived),
        "info": sum(1 for f in findings if f.severity == Severity.INFO),
        "waived_total": sum(1 for f in findings if f.waived),
    }


def print_report(findings: List[Finding], use_color: bool = True) -> None:
    order = {Severity.BREAKING: 0, Severity.WARNING: 1, Severity.INFO: 2}
    findings_sorted = sorted(findings, key=lambda f: (order[f.severity], f.domain, f.location))

    print("\n" + "=" * 88)
    print("  RAE-Suite CI Compatibility Report")
    print("=" * 88)

    if not findings_sorted:
        print("  No findings. ✅")
    else:
        for f in findings_sorted:
            # Pad BEFORE colorizing so ANSI escape codes don't break alignment.
            tag = _color(f"[{f.severity.label}]".rjust(10), f.severity.color, use_color)
            waived_tag = _color(" (WAIVED)", "\033[90m", use_color) if f.waived else ""
            print(f"  {tag} {f.domain:<8} {f.rule_id:<34} {f.location}")
            print(f"             -> {f.message}{waived_tag}")
            if f.waived and f.waiver_reason:
                print(f"             -> waiver reason: {f.waiver_reason}")
            print(f"             -> fingerprint: {f.fingerprint}")

    s = summarize(findings_sorted)
    print("-" * 88)
    print(
        f"  Total: {s['total']}  |  "
        f"Breaking: {s['breaking_active'] + s['breaking_waived']} ({s['breaking_active']} active)  |  "
        f"Warning: {s['warning_active'] + s['warning_waived']} ({s['warning_active']} active)  |  "
        f"Info: {s['info']}  |  Waived: {s['waived_total']}"
    )
    print("=" * 88 + "\n")


def write_json_report(findings: List[Finding], path: str) -> None:
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "metadata": {
            "generated_at": generated_at,
            "tool_version": VERSION,
        },
        "summary": summarize(findings),
        "findings": [f.to_dict() for f in findings],
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Self-test (embedded demo data — no external files needed)
# ---------------------------------------------------------------------------

def _self_test_openapi() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    old_spec = {
        "openapi": "3.0.0",
        "paths": {
            "/v1/users/{id}": {
                "get": {
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {
                        "200": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/User"}}}}
                    },
                }
            },
            "/v1/legacy-report": {"get": {"responses": {"200": {"content": {}}}}},
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "email": {"type": "string"},
                        "role": {"type": "string", "enum": ["admin", "member", "guest"]},
                    },
                    "required": ["id", "email"],
                },
                "TokenClaims": {
                    "type": "object",
                    "properties": {
                        "sub": {"type": "string"},
                        "org_id": {"type": "string"},
                        "session_id": {"type": "string"},
                    },
                    "required": ["sub"],
                },
            }
        },
    }
    new_spec = {
        "openapi": "3.0.0",
        "paths": {
            "/v1/users/{id}": {
                "get": {
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {
                        "200": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/User"}}}}
                    },
                }
            }
            # /v1/legacy-report intentionally removed -> PATH_REMOVED
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},   # SCHEMA_TYPE_CHANGED (string -> integer)
                        "email": {"type": "string"},
                        # 'role' removed from response schema -> FIELD_REMOVED (breaking)
                    },
                    "required": ["id", "email"],
                },
                "TokenClaims": {
                    "type": "object",
                    "properties": {
                        "sub": {"type": "string"},
                        "org_id": {"type": "string"},
                        "session_id": {"type": "string"},
                    },
                    # org_id has a valid, completed rollout -> allowed
                    # session_id has NO policy entry -> should be flagged
                    "required": ["sub", "org_id", "session_id"],
                },
            }
        },
    }
    return old_spec, new_spec


def _self_test_claims_policy() -> Dict[str, Any]:
    return {
        "min_rollout_days": 30,
        "claims": [
            {
                "name": "org_id",
                "status": "mandatory",
                "introduced_on": "2024-01-01",
                "mandatory_on": "2024-02-15",  # 45 days, OK, and in the past
            },
            # 'session_id' intentionally absent -> CLAIM_MADE_MANDATORY_WITHOUT_POLICY
        ],
    }


def _self_test_proto() -> Tuple[str, str]:
    old_proto = """
    syntax = "proto3";
    package rae.suite.v1;

    message Account {
      string id = 1;
      string owner_email = 2;
      int32 tier = 3;
      oneof contact {
        string phone = 5;
      }
      reserved 10 to 12;
    }

    enum Status {
      STATUS_UNSPECIFIED = 0;
      STATUS_ACTIVE = 1;
      STATUS_SUSPENDED = 2;
    }
    """
    new_proto = """
    syntax = "proto3";
    package rae.suite.v1;

    message Account {
      string id = 1;
      // owner_email removed WITHOUT reservation -> breaking
      // string ghost = 99;   // commented-out field must NOT be parsed
      int64 tier = 3;              // type changed int32 -> int64 -> breaking
      repeated string tags = 4;    // new field -> info
      oneof contact {
        string phone = 5;          // oneof field preserved by parser
      }
      string nickname = 10;        // reuses RESERVED number -> breaking
    }

    enum Status {
      STATUS_UNSPECIFIED = 0;
      STATUS_ACTIVE = 1;
      // STATUS_SUSPENDED (2) removed without reservation -> breaking
    }
    """
    return old_proto, new_proto


def run_self_test(today: date) -> List[Finding]:
    print(">>> Running in --self-test mode with embedded demo data (no external files needed)\n")
    findings: List[Finding] = []

    old_spec, new_spec = _self_test_openapi()
    findings.extend(check_openapi(old_spec, new_spec))

    policy_data = _self_test_claims_policy()
    findings.extend(check_claims_policy(
        policy_data, old_spec, new_spec, DEFAULT_CLAIMS_SCHEMA_NAME, today, None,
    ))

    old_proto_text, new_proto_text = _self_test_proto()
    old_messages, old_enums, old_parse = parse_proto_text(old_proto_text, "demo")
    new_messages, new_enums, new_parse = parse_proto_text(new_proto_text, "demo")
    findings.extend(new_parse)
    findings.extend(compare_proto_messages(old_messages, new_messages))
    findings.extend(compare_proto_enums(old_enums, new_enums))

    return findings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ci_compatibility_check.py",
        description="RAE-Suite CI gate: OpenAPI / Protobuf compatibility + mandatory claims rollout policy.",
    )
    p.add_argument("--openapi-old", help="Path to the old (baseline) OpenAPI spec (yaml/json)")
    p.add_argument("--openapi-new", help="Path to the new (candidate) OpenAPI spec (yaml/json)")

    p.add_argument("--proto-old-dir", help="Directory of old .proto files")
    p.add_argument("--proto-new-dir", help="Directory of new .proto files")

    p.add_argument("--claims-policy", help="Path to claims rollout policy YAML/JSON file")
    p.add_argument("--claims-schema-name", default=DEFAULT_CLAIMS_SCHEMA_NAME,
                   help=f"OpenAPI components.schemas name representing token claims "
                        f"(default: {DEFAULT_CLAIMS_SCHEMA_NAME})")
    p.add_argument("--min-rollout-days", type=int, default=None,
                   help=f"Override minimum rollout window in days (default policy file value, "
                        f"else {DEFAULT_MIN_ROLLOUT_DAYS})")

    p.add_argument("--waiver-file", help="Path to waivers YAML/JSON file")
    p.add_argument("--json-report", help="Path to write a machine-readable JSON report")

    p.add_argument("--fail-on-warning", action="store_true", help="Treat WARNING findings as gate failures")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colors in console output")
    p.add_argument("--today", help="Override 'today' date (YYYY-MM-DD) — useful for testing rollout schedules")
    p.add_argument("--self-test", action="store_true", help="Run against embedded demo data instead of real files")
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    return p


def _classify_error(check_name: str, exc: Exception) -> str:
    """Distinguish input/validation problems from unexpected tool failures."""
    if isinstance(exc, _INPUT_ERRORS):
        return f"{check_name} failed (input/validation): {exc}"
    return f"{check_name} failed (unexpected {type(exc).__name__}): {exc}"


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        today = parse_date(args.today) if args.today else datetime.now(timezone.utc).date()
    except Exception as exc:
        print(f"ERROR: invalid --today value: {exc}", file=sys.stderr)
        return EXIT_ERROR

    findings: List[Finding] = []
    errors: List[str] = []

    if args.self_test:
        findings.extend(run_self_test(today))
    else:
        ran_any = False
        old_spec: Optional[Dict[str, Any]] = None
        new_spec: Optional[Dict[str, Any]] = None

        if args.openapi_old or args.openapi_new:
            if not (args.openapi_old and args.openapi_new):
                errors.append("Both --openapi-old and --openapi-new must be provided together")
            else:
                ran_any = True
                try:
                    old_spec = ensure_mapping(
                        load_data_file(args.openapi_old), f"OpenAPI spec '{args.openapi_old}'")
                    new_spec = ensure_mapping(
                        load_data_file(args.openapi_new), f"OpenAPI spec '{args.openapi_new}'")
                    findings.extend(check_openapi(old_spec, new_spec))
                except Exception as exc:
                    errors.append(_classify_error("OpenAPI check", exc))

        if args.proto_old_dir or args.proto_new_dir:
            if not (args.proto_old_dir and args.proto_new_dir):
                errors.append("Both --proto-old-dir and --proto-new-dir must be provided together")
            else:
                ran_any = True
                try:
                    findings.extend(check_proto(args.proto_old_dir, args.proto_new_dir))
                except Exception as exc:
                    errors.append(_classify_error("Proto check", exc))

        if args.claims_policy:
            ran_any = True
            try:
                policy_data = ensure_mapping(
                    load_data_file(args.claims_policy), f"Claims policy '{args.claims_policy}'")
                # Reuse already-loaded/validated specs when available; only
                # load here if the OpenAPI check did not run.
                if old_spec is None and args.openapi_old:
                    old_spec = ensure_mapping(
                        load_data_file(args.openapi_old), f"OpenAPI spec '{args.openapi_old}'")
                if new_spec is None and args.openapi_new:
                    new_spec = ensure_mapping(
                        load_data_file(args.openapi_new), f"OpenAPI spec '{args.openapi_new}'")
                findings.extend(check_claims_policy(
                    policy_data, old_spec, new_spec, args.claims_schema_name,
                    today, args.min_rollout_days,
                ))
            except Exception as exc:
                errors.append(_classify_error("Claims policy check", exc))

        if not ran_any:
            print(
                "Nothing to check. Provide --openapi-old/--openapi-new, "
                "--proto-old-dir/--proto-new-dir, --claims-policy, or use --self-test.",
                file=sys.stderr,
            )
            return EXIT_ERROR

    for err in errors:
        print(f"ERROR: {err}", file=sys.stderr)

    try:
        waivers = load_waivers(args.waiver_file, today)
    except Exception as exc:
        print(f"ERROR: failed to load waiver file: {exc}", file=sys.stderr)
        return EXIT_ERROR

    findings = apply_waivers(findings, waivers)

    use_color = (not args.no_color) and sys.stdout.isatty()
    print_report(findings, use_color=use_color)

    if args.json_report:
        try:
            write_json_report(findings, args.json_report)
            print(f"JSON report written to: {args.json_report}")
        except Exception as exc:
            print(f"ERROR: failed to write JSON report: {exc}", file=sys.stderr)
            errors.append(str(exc))

    if errors:
        return EXIT_ERROR

    summary = summarize(findings)

    if summary["breaking_active"]:
        print(f"CI GATE: FAILED — {summary['breaking_active']} unwaived breaking finding(s).",
              file=sys.stderr)
        return EXIT_BREAKING
    if args.fail_on_warning and summary["warning_active"]:
        print(f"CI GATE: FAILED — {summary['warning_active']} unwaived warning finding(s) "
              f"(--fail-on-warning enabled).", file=sys.stderr)
        return EXIT_BREAKING

    print("CI GATE: PASSED")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
