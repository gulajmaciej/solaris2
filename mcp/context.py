from typing import Any

_CURRENT_SESSION: Any | None = None


def set_session(session: Any | None) -> None:
    global _CURRENT_SESSION
    _CURRENT_SESSION = session


def get_session() -> Any:
    if _CURRENT_SESSION is not None:
        return _CURRENT_SESSION

    # Fallback to the local singleton session if no context is set.
    from core.session import SESSION

    return SESSION
