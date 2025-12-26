from enum import Enum


class MCPPermission(Enum):
    PLAY_TURN = "play_turn"


ROLE_PERMISSIONS = {
    "observer": [],
    "player_agent": [
        MCPPermission.PLAY_TURN,
    ],
    "supervisor": [
        MCPPermission.PLAY_TURN,
    ],
}


def is_allowed(role: str, permission: MCPPermission) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, [])
