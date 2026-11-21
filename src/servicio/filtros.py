"""Filtros y órdenes que la API aplica sobre el catálogo.

Funciones puras: toman la lista de productos y los parámetros de la consulta
y devuelven la lista filtrada. Los parámetros inválidos levantan
ParametroInvalido, que la capa web traduce en una respuesta 400 con mensaje.
"""

from __future__ import annotations

from src.servicio.datos import Producto, con_precio

ORDENES = (
    "nombre",
    "precio_asc",
    "precio_desc",
    "calificacion",
    "resenas",
)


class ParametroInvalido(ValueError):
    """Un parámetro de la consulta no tiene un valor admitido."""


def _a_float(valor: str | None, campo: str) -> float | None:
    limpio = (valor or "").strip()
    if not limpio:
        return None
    try:
        numero = float(limpio)
    except ValueError as error:
        raise ParametroInvalido(
            f"El parámetro '{campo}' espera un número y recibió {limpio!r}"
        ) from error
    if numero < 0:
        raise ParametroInvalido(f"El parámetro '{campo}' no admite valores negativos")
    return numero


def _validar_orden(valor: str | None) -> str:
    orden = (valor or "nombre").strip()
    if orden not in ORDENES:
        admitidos = ", ".join(ORDENES)
        raise ParametroInvalido(f"El parámetro 'orden' solo admite: {admitidos}")
    return orden


def filtrar(
    productos: list[Producto],
    marca: str | None = None,
    texto: str | None = None,
    min_precio: str | None = None,
    max_precio: str | None = None,
) -> list[Producto]:
    """Aplica los filtros de la consulta; los parámetros vacíos no filtran."""
    resultado = productos
    if (marca or "").strip():
        buscada = marca.strip().lower()
        resultado = [p for p in resultado if p.marca.lower() == buscada]
    if (texto or "").strip():
        buscado = texto.strip().lower()
        resultado = [p for p in resultado if buscado in p.titulo.lower()]
    minimo = _a_float(min_precio, "min_precio")
    maximo = _a_float(max_precio, "max_precio")
    if minimo is not None:
        resultado = [p for p in resultado if p.precio is not None and p.precio >= minimo]
    if maximo is not None:
        resultado = [p for p in resultado if p.precio is not None and p.precio <= maximo]
    return resultado


def ordenar(productos: list[Producto], orden: str | None = None) -> list[Producto]:
    """Ordena la lista según el parámetro 'orden'; por defecto, por nombre."""
    elegido = _validar_orden(orden)
    sin_precio_al_final = lambda p: (p.precio is None, p.precio or 0.0)
    if elegido == "nombre":
        clave = lambda p: (p.marca, p.titulo)
    elif elegido == "precio_asc":
        clave = sin_precio_al_final
    elif elegido == "precio_desc":
        clave = lambda p: (p.precio is None, -(p.precio or 0.0))
    elif elegido == "calificacion":
        clave = lambda p: (-p.calificacion, -p.resenas)
    else:  # resenas
        clave = lambda p: -p.resenas
    return sorted(productos, key=clave)


def catalogo_de_marcas(productos: list[Producto]) -> list[str]:
    """Marcas distintas, alfabéticas; alimenta el filtro de la página."""
    return sorted({p.marca for p in productos})


def contar_sin_precio(productos: list[Producto]) -> int:
    """Productos sin precio conocido, para el aviso de cobertura del panel."""
    return len(productos) - len(con_precio(productos))
