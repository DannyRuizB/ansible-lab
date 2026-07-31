"""Custom Jinja tests for the lab (playbook 30).

A test plugin mirrors the filter plugin recipe (playbook 19) one namespace
over: a ``TestModule`` class whose ``tests()`` method returns a
``{name: callable}`` mapping, auto-discovered from the ``test_plugins`` path
(set in ansible.cfg). The difference is the CONTRACT: a filter TRANSFORMS a
value, a test ANSWERS a yes/no question about it — it is what ``is`` /
``is not`` evaluate and, crucially, what ``select`` / ``reject`` /
``selectattr`` / ``rejectattr`` expect. The two namespaces are separate: a
filter can never be called as a test, nor the other way around (playbook 30
provokes both failures on purpose).

Good manners demonstrated here: always return a real ``bool`` (truthiness
"works" until an empty string or a 0 slips through a condition), and never
raise on an unexpected type — a test that explodes inside a ``select``
takes the whole template down; the polite answer to "is this weird thing a
private IP?" is simply False.
"""

from __future__ import annotations

import ipaddress
import re

# Six hex octets with ONE separator style, colon or hyphen — the backreference
# rejects mixed separators. Cisco dot notation is deliberately out of contract.
_MAC_RE = re.compile(r"^[0-9A-Fa-f]{2}([:-])(?:[0-9A-Fa-f]{2}\1){4}[0-9A-Fa-f]{2}$")

_RFC1918 = (
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
)


def es_ipv4_privada(value):
    """True for an RFC 1918 IPv4 address (10/8, 172.16/12, 192.168/16).

    Strictly RFC 1918 on purpose: ``ipaddress``'s own ``is_private`` also
    says yes to loopback, link-local and other special ranges, which is not
    what "private LAN address" means in an inventory.
    """
    try:
        ip = ipaddress.IPv4Address(str(value))
    except (ipaddress.AddressValueError, ValueError):
        return False
    return any(ip in net for net in _RFC1918)


def es_puerto_privilegiado(value):
    """True for a TCP/UDP port below 1024 (binding one needs root or a cap).

    Booleans are excluded explicitly: ``int(True) == 1`` would make ``True``
    a "privileged port", which is the kind of truthiness accident the bool
    contract exists to prevent.
    """
    if isinstance(value, bool):
        return False
    try:
        port = int(value)
    except (TypeError, ValueError):
        return False
    return 0 < port < 1024


def es_mac_valida(value):
    """True for a MAC address in colon or hyphen notation (consistent)."""
    return bool(_MAC_RE.match(str(value)))


class TestModule:
    """Expose the lab's custom tests to Jinja."""

    def tests(self):
        return {
            "es_ipv4_privada": es_ipv4_privada,
            "es_puerto_privilegiado": es_puerto_privilegiado,
            "es_mac_valida": es_mac_valida,
        }
