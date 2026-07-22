"""Custom Jinja filters for the lab (playbook 19).

A filter plugin is just a Python module exposing a ``FilterModule`` class
whose ``filters()`` method returns a ``{name: callable}`` mapping. Ansible
auto-discovers it from the ``filter_plugins`` path (set in ansible.cfg), and
from then on the names are usable in templates and playbooks exactly like the
built-in filters — the whole point being that when Jinja's ~50 built-ins fall
short, you drop down to Python instead of contorting a one-liner.
"""

from __future__ import annotations

import re


def to_snake(value):
    """CamelCase / kebab-case / 'space case' -> snake_case.

    Handles the camelCase boundary (a lowercase or digit followed by an
    uppercase letter) and collapses any run of non-alphanumerics into a
    single underscore.
    """
    text = str(value)
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", text)
    text = re.sub(r"[^0-9A-Za-z]+", "_", text)
    return text.strip("_").lower()


def redact_secrets(value, keep=2, mask="*"):
    """Mask a secret, keeping the first ``keep`` characters.

    A string no longer than ``keep`` is masked in full, so short secrets
    never leak through the "keep the prefix" shortcut.
    """
    text = str(value)
    if len(text) <= keep:
        return mask * len(text)
    return text[:keep] + mask * (len(text) - keep)


def human_bytes(value, binary=True):
    """Byte count -> human string (``1536`` -> ``1.5 KiB``).

    ``binary=True`` uses 1024-based units (KiB/MiB…); ``binary=False`` uses
    1000-based (KB/MB…). Plain bytes render as a whole number, larger units
    with one decimal.
    """
    number = float(value)
    base = 1024 if binary else 1000
    units = (
        ["B", "KiB", "MiB", "GiB", "TiB"]
        if binary
        else ["B", "KB", "MB", "GB", "TB"]
    )
    idx = 0
    while abs(number) >= base and idx < len(units) - 1:
        number /= base
        idx += 1
    if idx == 0:
        return f"{int(number)} {units[idx]}"
    return f"{number:.1f} {units[idx]}"


class FilterModule:
    """Register the lab's custom filters with Ansible."""

    def filters(self):
        return {
            "to_snake": to_snake,
            "redact_secrets": redact_secrets,
            "human_bytes": human_bytes,
        }
