"""suite_sso — identidad compartida entre los módulos de Suite UNAB.

El servicio `core` emite un JWT firmado (HS256) en la cookie `suite_sso`
cuando el usuario inicia sesión. Cada módulo valida esa cookie localmente,
sin llamar a `core` en cada request, y comprueba que la institución del
usuario tenga licencia para el módulo (modelo "suite": cada app funciona
sola o como parte del paquete).
"""

from .tokens import (  # noqa: F401
    COOKIE_NAME,
    SuiteIdentity,
    TokenInvalido,
    emitir_token,
    verificar_token,
)

__version__ = "1.0.0"
