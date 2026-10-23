import time

import jwt
import pytest

from suite_sso import SuiteIdentity, TokenInvalido, emitir_token, verificar_token

SECRETO = "s" * 40


def identidad(**extra):
    datos = dict(
        sub="7",
        email="ana@unab.cl",
        nombre="Ana",
        organizacion="unab",
        roles=("estudiante",),
        modulos=("malla", "horarios"),
    )
    datos.update(extra)
    return SuiteIdentity(**datos)


def test_ida_y_vuelta_conserva_identidad():
    token = emitir_token(identidad(), secreto=SECRETO)
    i = verificar_token(token, secreto=SECRETO)
    assert (i.sub, i.email, i.organizacion) == ("7", "ana@unab.cl", "unab")
    assert i.tiene_modulo("malla") and not i.tiene_modulo("mapa-calor")
    assert i.tiene_rol("estudiante")


def test_rechaza_firma_con_otro_secreto():
    token = emitir_token(identidad(), secreto=SECRETO)
    with pytest.raises(TokenInvalido):
        verificar_token(token, secreto="x" * 40)


def test_rechaza_token_expirado():
    token = emitir_token(identidad(), ttl=-1, secreto=SECRETO)
    with pytest.raises(TokenInvalido):
        verificar_token(token, secreto=SECRETO)


def test_rechaza_token_de_otra_audiencia():
    ahora = int(time.time())
    ajeno = jwt.encode(
        {"sub": "1", "aud": "otra-app", "iss": "suite-unab-core", "iat": ahora, "exp": ahora + 60},
        SECRETO,
        algorithm="HS256",
    )
    with pytest.raises(TokenInvalido):
        verificar_token(ajeno, secreto=SECRETO)


def test_rechaza_algoritmo_none():
    sin_firma = jwt.encode({"sub": "1"}, key=None, algorithm="none")
    with pytest.raises(TokenInvalido):
        verificar_token(sin_firma, secreto=SECRETO)


def test_exige_secreto_largo():
    with pytest.raises(TokenInvalido):
        emitir_token(identidad(), secreto="corto")
