from .authentication import build_authentication_dependency, AuthenticationDependency
from .authorization import build_authorization_factory, AuthorizationFactory, build_get_roles_dependency, GetRolesDependency
from builder import AppBuilder

_builder = AppBuilder()

authenticate = _builder.build_authentication_dependency()
require_cnf_roles = _builder.build_require_cnf_roles()
get_user_roles = _builder.build_get_roles_dependency()


__all__ = [
    "build_authentication_dependency",
    "AuthenticationDependency",
    "build_authorization_factory",
    "AuthorizationFactory",
    "build_get_roles_dependency",
    "GetRolesDependency",
    "require_cnf_roles",
    "get_user_roles",
]