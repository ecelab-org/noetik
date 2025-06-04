"""
A simple parser for tool calls in the form of a string.
It expects a string formatted like:
    {"tool": "<name>", "args": { ... }}
and returns a dictionary with the tool name and its arguments.
"""

from typing import (
    Dict,
    List,
    Mapping,
    Tuple,
)


class ToolCallParseError(RuntimeError):
    """Raised when the string cannot be parsed into {"tool": ..., "args": {...}}"""


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
_WS = " \t\r\n"
_QUOTE_SET = {"'", '"'}


def _skip_ws(s: str, i: int) -> int:
    while i < len(s) and s[i] in _WS:
        i += 1
    return i


def _read_quoted(s: str, i: int) -> Tuple[str, int]:
    """Read a Python-like quoted string, honouring back-slash escapes and triple quotes."""
    # Check for triple quotes first
    if i + 2 < len(s):
        triple_single = s[i : i + 3] == "'''"
        triple_double = s[i : i + 3] == '"""'
        if triple_single or triple_double:
            quote = s[i : i + 3]
            i += 3
            start = i
            # Find the matching closing triple quote
            while i + 2 < len(s):
                if s[i : i + 3] == quote:
                    return s[start:i], i + 3
                i += 1
            raise ToolCallParseError("unterminated triple-quoted string")

    # Regular single quotes
    quote = s[i]
    if quote not in _QUOTE_SET:
        raise ToolCallParseError(f"expected quote at pos {i}")
    i += 1
    out: List[str] = []
    esc = False
    while i < len(s):
        ch = s[i]
        if esc:
            out.append(ch)
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == quote:
            return "".join(out), i + 1
        else:
            out.append(ch)
        i += 1
    raise ToolCallParseError("unterminated string literal")


def _find_matching_brace(s: str, i: int) -> int:
    """Given s[i] == '{', return index just past its matching '}'."""
    depth = 0
    while i < len(s):
        ch = s[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        elif ch in _QUOTE_SET:
            _, i = _read_quoted(s, i)  # skip over quoted section
            continue  # i already advanced
        i += 1
    raise ToolCallParseError("unbalanced braces")


def _read_key(s: str, i: int) -> Tuple[str, int]:
    i = _skip_ws(s, i)
    if s[i] not in _QUOTE_SET:
        raise ToolCallParseError(f"dict key at pos {i} must be quoted")
    key, i = _read_quoted(s, i)
    i = _skip_ws(s, i)
    if i >= len(s) or s[i] != ":":
        raise ToolCallParseError(f"missing ':' after key {key!r}")
    return key, i + 1


def _read_value(s: str, i: int) -> Tuple[str, int]:
    i = _skip_ws(s, i)
    if i >= len(s):
        raise ToolCallParseError("unexpected end of input while reading value")

    if s[i] in _QUOTE_SET:
        return _read_quoted(s, i)
    elif s[i] == "{":
        j = _find_matching_brace(s, i)
        return s[i:j], j  # keep nested dict as raw text
    else:
        # read until top-level comma or closing brace
        depth = 0
        start = i
        while i < len(s):
            ch = s[i]
            if ch in _QUOTE_SET:
                _, i = _read_quoted(s, i)
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                if depth == 0:
                    break
                depth -= 1
            elif ch == "," and depth == 0:
                break
            i += 1
        return s[start:i].strip(), i


def _parse_shallow_dict(s: str) -> Dict[str, str]:
    """Parse a {k: v, …} dict where *values* are treated as raw strings."""
    i = _skip_ws(s, 0)
    if i >= len(s) or s[i] != "{":
        raise ToolCallParseError("dict must start with '{'")
    i += 1
    out: Dict[str, str] = {}
    while True:
        i = _skip_ws(s, i)
        if i >= len(s):
            raise ToolCallParseError("unexpected end of input in dict")
        if s[i] == "}":
            return out
        key, i = _read_key(s, i)
        val, i = _read_value(s, i)
        out[key] = val
        i = _skip_ws(s, i)
        if i < len(s) and s[i] == ",":
            i += 1  # consume comma and loop


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def parse_tool_call(text: str) -> Mapping[str, str | Mapping[str, str]]:
    """
    Best-effort parser for strings of the form
        {"tool": "<name>", "args": { ... }}
    Returns
        {"tool": <str>, "args": {<str>: <str>, ...}}
    All arg-values are delivered as raw strings (quotes stripped if present).
    """
    top = _parse_shallow_dict(text)

    if "tool" not in top or "args" not in top:
        raise ToolCallParseError("both 'tool' and 'args' keys are required")

    tool_val = top["tool"]
    # If tool itself was quoted, _read_value stripped the quotes already.
    tool_val = tool_val.strip()
    if not tool_val:
        raise ToolCallParseError("'tool' name is empty")

    # Parse the inner args dict (tool_val is str; we discard).
    args_raw = top["args"].strip()
    if not args_raw.startswith("{"):
        raise ToolCallParseError("'args' must start with '{'")
    args_dict = _parse_shallow_dict(args_raw)

    return {"tool": tool_val, "args": args_dict}
