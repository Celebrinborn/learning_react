from .authentication import build_authentication_dependency, AuthenticationDependency
from .authorization import build_authorization_factory, AuthorizationFactory
from builder import AppBuilder

_builder = AppBuilder()

authenticate = _builder.build_authentication_dependency()
require_cnf_roles = _builder.build_require_cnf_roles()


__all__ = [
    "build_authentication_dependency",
    "AuthenticationDependency",
    "build_authorization_factory",
    "AuthorizationFactory",
    "require_cnf_roles",
]