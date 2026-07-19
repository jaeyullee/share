#!/usr/bin/env python3
"""Validate the small chat dataset used by the Week 5 LoRA lab."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ALLOWED_ROLES = {"system", "user", "assistant"}


def validate(path: Path) -> int:
    rows = 0
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            messages = record.get("messages")
            if not isinstance(messages, list) or len(messages) < 2:
                raise ValueError(f"line {line_number}: messages must contain at least two entries")
            roles = []
            for message in messages:
                role = message.get("role")
                content = message.get("content")
                if role not in ALLOWED_ROLES:
                    raise ValueError(f"line {line_number}: unsupported role {role!r}")
                if not isinstance(content, str) or not content.strip():
                    raise ValueError(f"line {line_number}: content must be a non-empty string")
                roles.append(role)
            if "user" not in roles or "assistant" not in roles:
                raise ValueError(f"line {line_number}: user and assistant messages are required")
            rows += 1
    if rows < 10:
        raise ValueError(f"dataset is too small for the lab: {rows} rows")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args()
    print(f"valid_rows={validate(args.dataset)}")


if __name__ == "__main__":
    main()

