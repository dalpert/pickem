from __future__ import annotations

# Canonical player names keyed by email address
PLAYER_NAMES: dict[str, str] = {
    "adam.lassman@gmail.com": "Adam",
    "andrespintopro@gmail.com": "Andres",
    "warnercp10@gmail.com": "Colin",
    "dalpert89@gmail.com": "Daniel",
    "greg.angel029@gmail.com": "Greg",
    "jtocci19@gmail.com": "James",
    "jordan.angel7472@gmail.com": "Jordan",
}


def canonical_name(email: str, fallback: str = "") -> str:
    """Return the canonical display name for a player.

    Uses email as the primary key. Falls back to the provided name if email
    is not in the mapping.
    """
    return PLAYER_NAMES.get(email.strip().lower(), fallback.strip() or email)
