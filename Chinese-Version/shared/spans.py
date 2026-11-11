"""Unchanged protected-span routines reused from Workbench v0.5.0 apply_plan.py."""
import re

def protected_syntax(text):
    tokens = re.findall(r"\{\{[^{}]*\}\}|<%[\s\S]*?%>|\$\{[^{}]*\}|\$\d+|</?[A-Za-z!][^>]*>|\[[A-Za-z][A-Za-z0-9_]*\|", text)
    blocks = [m.group(0) for m in re.finditer(r"<(script|style)\b[^>]*>[\s\S]*?</\1\s*>", text, re.I)]
    comments = re.findall(r"<!--[\s\S]*?-->", text)
    fences = re.findall(r"^\s*```[^\r\n]*", text, re.M)
    return tokens, blocks, comments, fences

def replace_spans(value, edits):
    previous_end = -1
    previous_start = -1
    for edit in sorted(edits, key=lambda e: e["start"]):
        start, end = edit["start"], edit["end"]
        if start < previous_end or start == previous_start or end < start or end > len(value):
            raise ValueError("overlapping or out-of-range edits")
        if value[start:end] != edit["expected"]:
            raise ValueError("expected span differs from source")
        previous_start, previous_end = start, end
    result = value
    for edit in sorted(edits, key=lambda e: e["start"], reverse=True):
        result = result[:edit["start"]] + edit["replacement"] + result[edit["end"]:]
    if result == value:
        raise ValueError("patch has no effect")
    if protected_syntax(value) != protected_syntax(result):
        raise ValueError("patch changes protected markup, template tokens, code/style, comments, or fences")
    return result
