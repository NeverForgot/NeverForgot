"""Utilitaires de date coherents entre Postgres et SQLite.

Postgres renvoie des `datetime` timezone-aware pour les colonnes
`DateTime(timezone=True)` ; SQLite les renvoie toujours naive, quel que soit
le flag `timezone=True` — l'ecart est invisible en tests (SQLite) et casse
en production (Postgres) des qu'une valeur generee en Python (`datetime.now`)
est comparee/soustraite a une valeur relue depuis la base
(`TypeError: can't subtract offset-naive and offset-aware datetimes`).
"""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_naive_utc(value: datetime) -> datetime:
    """Normalise en UTC naive pour des comparaisons/soustractions fiables,
    que `value` vienne de Postgres (aware) ou de SQLite (naive)."""
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value
