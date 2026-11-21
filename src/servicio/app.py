"""Fábrica de la aplicación Flask que sirve el catálogo de la EA1.

El catálogo se carga una sola vez al crear la aplicación: si el CSV no cumple
el contrato, el servicio no arranca (falla rápido), que es el comportamiento
que el despliegue espera. Los endpoints devuelven HTML en la raíz y JSON en
la API; los errores de consulta son 400 con mensaje y los recursos ausentes,
404 con cuerpo JSON.
"""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from src.servicio.datos import CatalogoNoValido, Producto, a_diccionario, cargar
from src.servicio.filtros import (
    ParametroInvalido,
    catalogo_de_marcas,
    contar_sin_precio,
    filtrar,
    ordenar,
)
from src.servicio.metricas import (
    distribucion_precio,
    mejor_calificado,
    por_marca,
    resumen_general,
)

RUTA_CATALOGO_DEFECTO = Path("data") / "catalogo_consolidado.csv"


def _revision() -> str:
    """Commit desplegado; Render inyecta RENDER_GIT_COMMIT en cada release."""
    return (os.getenv("RENDER_GIT_COMMIT") or "local")[:7]


def create_app(catalogo: str | Path | None = None) -> Flask:
    """Construye la aplicación con el catálogo dado (o el de la carpeta data)."""
    ruta = Path(catalogo or os.getenv("CATALOGO_RUTA") or RUTA_CATALOGO_DEFECTO)
    try:
        productos = cargar(ruta)
    except CatalogoNoValido as error:
        raise RuntimeError(f"El servicio no puede arrancar: {error}") from error

    app = Flask(__name__)
    por_asin = {p.asin: p for p in productos}

    @app.get("/")
    def inicio():
        resumen = resumen_general(productos)
        return render_template(
            "index.html",
            resumen=resumen,
            productos=ordenar(productos, "nombre"),
            marcas=catalogo_de_marcas(productos),
            sin_precio=contar_sin_precio(productos),
            top_calificados=mejor_calificado(productos),
            revision=_revision(),
        )

    @app.get("/healthz")
    def salud():
        return jsonify(status="ok", revision=_revision(), productos=len(productos))

    @app.get("/api/productos")
    def api_productos():
        try:
            seleccion = ordenar(
                filtrar(
                    productos,
                    marca=request.args.get("marca"),
                    texto=request.args.get("q"),
                    min_precio=request.args.get("min_precio"),
                    max_precio=request.args.get("max_precio"),
                ),
                request.args.get("orden"),
            )
        except ParametroInvalido as error:
            return jsonify(error=str(error)), 400
        return jsonify(total=len(seleccion), productos=[a_diccionario(p) for p in seleccion])

    @app.get("/api/productos/<asin>")
    def api_producto(asin: str):
        producto = por_asin.get(asin.upper())
        if producto is None:
            return jsonify(error=f"No existe un producto con el ASIN {asin!r}"), 404
        return jsonify(a_diccionario(producto))

    @app.get("/api/metricas")
    def api_metricas():
        return jsonify(
            resumen=resumen_general(productos),
            por_marca=por_marca(productos),
            distribucion_precio=distribucion_precio(productos),
            mejor_calificado=mejor_calificado(productos),
        )

    @app.errorhandler(404)
    def no_encontrado(_error):
        if request.path.startswith("/api/"):
            return jsonify(error="Recurso no encontrado"), 404
        return render_template("index.html", resumen=None), 404

    return app
