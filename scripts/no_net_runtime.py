"""Bloquea conexiones salientes no-localhost en tiempo de ejecución.
Importar este módulo en el arranque (app.main)."""
from __future__ import annotations
import builtins
import socket
from socket import AF_INET, AF_INET6
from typing import Tuple

_ALLOWED = {("127.0.0.1", None), ("::1", None)}

_real_socket = socket.socket
_real_create_connection = socket.create_connection


class OutboundBlockedError(PermissionError):
    pass


def _is_local(addr: Tuple[str, int] | str) -> bool:
    if isinstance(addr, tuple):
        host, _port = addr
    else:
        host = addr
    return host.startswith("127.") or host == "::1" or host == "localhost"


class _GuardedSocket(_real_socket):  # type: ignore[misc]
    def connect(self, address):  # type: ignore[override]
        if not _is_local(address):
            raise OutboundBlockedError(f"Outbound blocked to {address}")
        return super().connect(address)


def _guarded_create_connection(address, timeout=None, source_address=None):  # noqa: D401
    if not _is_local(address):
        raise OutboundBlockedError(f"Outbound blocked to {address}")
    return _real_create_connection(address, timeout=timeout, source_address=source_address)


# Patch globales
socket.socket = _GuardedSocket  # type: ignore[assignment]
socket.create_connection = _guarded_create_connection  # type: ignore[assignment]

# Bloqueo de family raw si alguien intenta usar bajo nivel
_orig_socket = builtins.__dict__.get("socket", None)
__all__ = ["OutboundBlockedError"]