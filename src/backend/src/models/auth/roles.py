from enum import StrEnum

class UserRole(StrEnum):
    ADMIN = "admin"
    PLAYER = "player"
    DM = "dm"
    GUEST = "guest"