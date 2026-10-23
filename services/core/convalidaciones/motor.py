"""Motor de convalidación de Suite UNAB (versión servidor).

Port fiel del motor que corre en el navegador (apps/convalidacion): mismo
tokenizador, stemming conservador, IDF global sobre todo el catálogo UNAB
y puntaje híbrido  score = cobertura + (1 - cobertura) · coseno.
Mantenerlos alineados permite que el servidor reproduzca los resultados del
cliente y que la evaluación de precisión (ver tests/test_motor.py) aplique
a ambos.
"""

from __future__ import annotations

import math
import re
import statistics
import unicodedata
from dataclasses import dataclass, field

UMBRAL_CONVALIDA = 0.45  # zona alta  -> convalidable
UMBRAL_REVISION = 0.25  # zona media -> revisión manual
UMBRAL_AE = 0.4  # cobertura mínima para dar por cubierto un aprendizaje esperado

STOP = frozenset(
    """de la que el en y a los del se las por un para con no una su al lo como mas pero sus le ya o este si porque esta entre cuando muy sin sobre tambien me hasta hay donde quien desde todo nos durante todos uno les ni contra otros ese eso ante ellos e esto mi antes algunos unos yo otro otras otra tanto esa estos mucho quienes nada muchos cual poco ella estar estas algunas algo nosotros tu te ti tus ellas vosotros os mediante cuyo cuya segun ser son ademas asi etc cada tales tal este esta estos estas ademas dicha dicho dichas dichos cuales sera seran debe deben puede pueden mismo misma mismos mismas dos tres cual modo forma parte partir traves luego entonces ello cuyo ámbito ambito accion acciones ra ae unidad unidades aprendizaje aprendizajes esperado esperados contenido contenidos asignatura curso estudiante estudiantes nivel niveles general""".split()
)

_RE_NO_LETRA = re.compile(r"[^a-z\u00f1\s]")


def quitar_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))


def stem(w: str) -> str:
    """Stemmer conservador de plurales del español (no deja raíces cortas)."""
    minimo = 4
    if len(w) > minimo + 1:
        if w.endswith("bles"):
            return w[:-1]
        if w.endswith("ses"):
            return w[:-1]
        if w.endswith("es"):
            return w[:-2] if w[-3] not in "aeiou" else w[:-1]
    if len(w) > minimo and w.endswith("s"):
        return w[:-1]
    return w


def tokenizar(texto: str) -> list[str]:
    limpio = _RE_NO_LETRA.sub(" ", quitar_acentos((texto or "").lower()))
    salida = []
    for t in limpio.split():
        if len(t) < 3 or t in STOP:
            continue
        t = stem(t)
        if len(t) < 3 or t in STOP:
            continue
        salida.append(t)
    return salida


def _mediana(valores) -> float:
    valores = list(valores)
    return statistics.median(valores) if valores else 0.0


@dataclass
class AsignaturaDestino:
    codigo: str
    nombre: str
    contenidos: str = ""
    aprendizajes: list[str] = field(default_factory=list)
    semestre: int | None = None
    creditos: int | None = None

    def tokens(self) -> list[str]:
        # el nombre se repite 3 veces: pesa más que la descripción (igual que el cliente)
        return tokenizar(f"{self.nombre} {self.nombre} {self.nombre} {self.contenidos}")


def construir_idf_global(base: dict[str, list[AsignaturaDestino]]) -> dict[str, float]:
    """IDF sobre todo el catálogo UNAB, contando cada código una sola vez."""
    vistos, docs = set(), []
    for asignaturas in base.values():
        for a in asignaturas:
            if a.codigo in vistos:
                continue
            vistos.add(a.codigo)
            docs.append(set(a.tokens()))
    n = len(docs)
    df: dict[str, int] = {}
    for toks in docs:
        for t in toks:
            df[t] = df.get(t, 0) + 1
    return {t: math.log((n + 1) / (d + 1)) + 1 for t, d in df.items()}


def _vector(tf: dict[str, int], idf: dict[str, float]) -> dict[str, float]:
    vec = {t: (1 + math.log(f)) * idf.get(t, 0.0) for t, f in tf.items()}
    norma = math.sqrt(sum(w * w for w in vec.values())) or 1.0
    return {t: w / norma for t, w in vec.items()}


def _tf(tokens: list[str]) -> dict[str, int]:
    tf: dict[str, int] = {}
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1
    return tf


@dataclass
class _Doc:
    asig: AsignaturaDestino
    vec: dict[str, float]
    clave: set[str]
    ae: list[tuple[str, list[str]]]


class IndiceCarrera:
    """Índice TF-IDF de una carrera de destino, usando el IDF global."""

    def __init__(self, asignaturas: list[AsignaturaDestino], idf: dict[str, float]):
        self.idf = idf
        piso_idf = _mediana(idf.values())
        self.docs: list[_Doc] = []
        for a in asignaturas:
            tf = _tf(a.tokens())
            vec = _vector(tf, idf)
            idf_med = _mediana(idf.get(t, 0.0) for t in tf)
            clave = [
                t
                for t, _ in sorted(((t, w) for t, w in vec.items() if idf.get(t, 0.0) >= idf_med), key=lambda x: -x[1])[
                    :12
                ]
            ]
            ae = []
            for texto in a.aprendizajes or []:
                toks = list(dict.fromkeys(tokenizar(texto)))
                dist = [t for t in toks if idf.get(t, 0.0) >= piso_idf]
                if len(dist) < 2:
                    dist = toks
                dist = sorted(dist, key=lambda t: -idf.get(t, 0.0))[:6]
                ae.append((texto, dist))
            self.docs.append(_Doc(a, vec, set(clave), ae))

    def evaluar(self, texto_origen: str) -> list[dict]:
        tf = _tf(tokenizar(texto_origen))
        presentes = set(tf)
        dv = _vector(tf, self.idf)
        resultados = []
        for d in self.docs:
            chico, grande = (dv, d.vec) if len(dv) < len(d.vec) else (d.vec, dv)
            cos = sum(w * grande.get(t, 0.0) for t, w in chico.items())
            coincidencias = [t for t in d.clave if t in presentes]
            cov = len(coincidencias) / len(d.clave) if d.clave else 0.0
            score = cov + (1 - cov) * cos
            ae_ok = sum(
                1 for _, terms in d.ae if terms and sum(t in presentes for t in terms) / len(terms) >= UMBRAL_AE
            )
            resultados.append(
                {
                    "codigo": d.asig.codigo,
                    "nombre": d.asig.nombre,
                    "semestre": d.asig.semestre,
                    "creditos": d.asig.creditos,
                    "score": round(score, 4),
                    "cobertura": round(cov, 4),
                    "coseno": round(cos, 4),
                    "terminos": sorted(coincidencias),
                    "aprendizajes_pct": round(ae_ok / len(d.ae) * 100) if d.ae else None,
                    "estado": estado_de(score),
                }
            )
        resultados.sort(key=lambda r: -r["score"])
        return resultados


# Con solo el nombre hay menos evidencia: se exige más para sugerir revisión.
UMBRAL_REVISION_NOMBRE = 0.35


def estado_de(score: float, solo_nombre: bool = False) -> str:
    if score >= UMBRAL_CONVALIDA:
        return "convalidable"
    if score >= (UMBRAL_REVISION_NOMBRE if solo_nombre else UMBRAL_REVISION):
        return "revision"
    return "sin_coincidencia"


# ─────────────────────────────────────────────────────────────────────
# Modo "por nombre" (catálogo de mallas): el postulante elige su malla de
# origen y marca asignaturas; no hay programa en PDF, solo el nombre.
# El modo por contenidos de arriba rinde mal con textos tan cortos, así que
# se combina con (1) conceptos curriculares curados y (2) similitud de
# nombres ponderada por IDF.
# ─────────────────────────────────────────────────────────────────────
import json  # noqa: E402
from pathlib import Path  # noqa: E402

_RE_SUFIJOS = re.compile(r"\s+para\s+(ingenieria|informatica|obras civiles)(\s+(electrica|en minas|informatica))?\b")
_RE_PARENTESIS = re.compile(r"\([^)]*\)")
_RE_PUNTUACION = re.compile(r"[^a-z0-9\u00f1/, ]")


def normalizar_nombre(nombre: str) -> str:
    s = quitar_acentos((nombre or "").lower())
    s = _RE_PARENTESIS.sub(" ", s)
    s = _RE_SUFIJOS.sub(" ", s)
    s = _RE_PUNTUACION.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip(" ,")


class Conceptos:
    """Diccionario curado de conceptos curriculares (data/convalidacion/conceptos.json)."""

    def __init__(self, definicion: dict):
        self.version = definicion.get("_version", "")
        self._reglas = [
            (clave, [re.compile(p) for p in c["patrones"]]) for clave, c in definicion.get("conceptos", {}).items()
        ]

    @classmethod
    def desde_archivo(cls, ruta: str | Path) -> Conceptos:
        return cls(json.loads(Path(ruta).read_text(encoding="utf-8")))

    def de(self, nombre: str) -> set[str]:
        n = normalizar_nombre(nombre)
        return {clave for clave, patrones in self._reglas if any(p.search(n) for p in patrones)}


def similitud_nombres(a: str, b: str, idf: dict[str, float]) -> float:
    """Coeficiente de Dice ponderado por IDF entre dos nombres de asignatura."""
    ta, tb = set(tokenizar(normalizar_nombre(a))), set(tokenizar(normalizar_nombre(b)))
    if not ta or not tb:
        return 0.0
    tope = max(idf.values()) if idf else 1.0
    peso = lambda t: idf.get(t, tope)  # noqa: E731 - término no visto en UNAB = muy específico
    comun = sum(peso(t) for t in ta & tb)
    return 2 * comun / (sum(peso(t) for t in ta) + sum(peso(t) for t in tb))


PESO_CONCEPTO = 0.9  # coincidir en concepto curado es evidencia fuerte
PESO_NOMBRE = 0.7  # similitud léxica de nombres
PESO_CONTENIDO = 0.3  # nombre de origen vs contenidos del programa UNAB


def puntaje_por_nombre(concepto_comun: bool, sim_nombre: float, score_contenido: float) -> float:
    por_concepto = PESO_CONCEPTO + (1 - PESO_CONCEPTO) * sim_nombre if concepto_comun else 0.0
    por_texto = PESO_NOMBRE * sim_nombre + PESO_CONTENIDO * score_contenido
    return round(max(por_concepto, por_texto), 4)


_ROMANOS = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10, "xi": 11}
_RE_NIVEL = re.compile(r"\b(viii|vii|iii|ii|iv|ix|vi|xi|x|v|i|[1-9])\s*$")
PENALIZACION_NIVEL = 0.6  # "Cálculo I" no debe convalidar "Cálculo II"


def nivel_de(nombre: str) -> int | None:
    """Nivel final del nombre (I, II, 2…). Mismo criterio que el cliente."""
    s = re.sub(r"[^a-z0-9ivx ]", " ", quitar_acentos((nombre or "").lower())).strip()
    m = _RE_NIVEL.search(s)
    if not m:
        return None
    return _ROMANOS.get(m.group(1)) or int(m.group(1))


def evaluar_asignatura(
    indice: IndiceCarrera,
    conceptos: Conceptos,
    nombre: str,
    texto: str = "",
    conceptos_destino: dict[str, set[str]] | None = None,
) -> list[dict]:
    """Candidatos UNAB para una asignatura de origen (contenidos + conceptos + nombre + nivel).

    Es la función que usa producción (servicio.sugerir) y la evaluación de precisión.
    """
    if conceptos_destino is None:
        conceptos_destino = {d.asig.codigo: conceptos.de(d.asig.nombre) for d in indice.docs}
    consulta = f"{nombre} {texto or ''}".strip()
    candidatos = indice.evaluar(consulta) if consulta else []
    c_origen = conceptos.de(nombre)
    n_origen = nivel_de(nombre)
    for c in candidatos:
        sim = similitud_nombres(nombre, c["nombre"], indice.idf)
        comun = c_origen & conceptos_destino.get(c["codigo"], set())
        c["score"] = max(c["score"], puntaje_por_nombre(bool(comun), sim, c["score"]))
        c["concepto"] = sorted(comun) or None
        n_dest = nivel_de(c["nombre"])
        if n_origen is not None and n_dest is not None and n_origen != n_dest:
            c["score"] = round(c["score"] * PENALIZACION_NIVEL, 4)
        c["estado"] = estado_de(c["score"], solo_nombre=not texto)
    candidatos.sort(key=lambda c: -c["score"])
    return candidatos
