from app.core.errors import AuthorizationError
from app.models.enums import Role

ROLE_RANK: dict[Role, int] = {
    Role.VIEWER: 10,
    Role.ANALYST: 20,
    Role.ADMIN: 30,
    Role.OWNER: 40,
}


def assert_role(current_role: Role, allowed: set[Role]) -> None:
    if current_role not in allowed:
        raise AuthorizationError()


def assert_min_role(current_role: Role, minimum_role: Role) -> None:
    if ROLE_RANK[current_role] < ROLE_RANK[minimum_role]:
        raise AuthorizationError()

