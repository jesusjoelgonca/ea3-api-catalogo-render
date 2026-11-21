"""Pruebas de la API web: filtros, órdenes, errores y páginas servidas."""

import unittest

from src.servicio import create_app
from src.servicio.filtros import ParametroInvalido, filtrar, ordenar
from src.servicio.datos import cargar

CATALOGO = "data/catalogo_consolidado.csv"


class PruebaFiltrosPuros(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.productos = cargar(CATALOGO)

    def test_filtro_por_marca_no_distingue_mayusculas(self):
        seleccion = filtrar(self.productos, marca="samsung")
        self.assertTrue(seleccion)
        self.assertTrue(all(p.marca == "Samsung" for p in seleccion))

    def test_filtro_por_texto_busca_en_el_titulo(self):
        seleccion = filtrar(self.productos, texto="galaxy")
        self.assertTrue(seleccion)
        self.assertTrue(all("galaxy" in p.titulo.lower() for p in seleccion))

    def test_rango_de_precio_excluye_al_producto_sin_precio(self):
        seleccion = filtrar(self.productos, min_precio="0", max_precio="100000")
        self.assertTrue(all(p.precio is not None for p in seleccion))

    def test_minimo_mayor_que_maximo_da_lista_vacia(self):
        self.assertEqual(filtrar(self.productos, min_precio="900", max_precio="100"), [])

    def test_parametro_no_numerico_rechazado(self):
        with self.assertRaises(ParametroInvalido):
            filtrar(self.productos, min_precio="barato")

    def test_orden_invalido_rechazado(self):
        with self.assertRaises(ParametroInvalido):
            ordenar(self.productos, "alzar")

    def test_orden_por_precio_descendente(self):
        seleccion = ordenar(filtrar(self.productos), "precio_desc")
        precios = [p.precio for p in seleccion if p.precio is not None]
        self.assertEqual(precios, sorted(precios, reverse=True))


class PruebaApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cliente = create_app(CATALOGO).test_client()

    def test_raiz_devuelve_la_pagina(self):
        respuesta = self.cliente.get("/")
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.data.decode("utf-8")
        self.assertIn("Catálogo de teléfonos", html)
        self.assertIn("B0GW9TVHJB", html)

    def test_healthz_reporta_estado_y_revision(self):
        respuesta = self.cliente.get("/healthz")
        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.get_json()
        self.assertEqual(cuerpo["status"], "ok")
        self.assertEqual(cuerpo["productos"], 16)
        self.assertTrue(cuerpo["revision"])

    def test_api_productos_devuelve_todo_el_catalogo(self):
        cuerpo = self.cliente.get("/api/productos").get_json()
        self.assertEqual(cuerpo["total"], 16)
        self.assertEqual(len(cuerpo["productos"]), 16)

    def test_api_productos_con_filtro_de_marca(self):
        cuerpo = self.cliente.get("/api/productos?marca=Samsung").get_json()
        self.assertTrue(cuerpo["productos"])
        self.assertTrue(all(p["marca"] == "Samsung" for p in cuerpo["productos"]))

    def test_api_productos_con_busqueda_de_texto(self):
        cuerpo = self.cliente.get("/api/productos?q=galaxy").get_json()
        self.assertTrue(cuerpo["productos"])
        self.assertTrue(all("galaxy" in p["titulo"].lower() for p in cuerpo["productos"]))

    def test_api_productos_con_rango_de_precio(self):
        cuerpo = self.cliente.get("/api/productos?min_precio=300&max_precio=800").get_json()
        self.assertTrue(all(300 <= p["precio"] <= 800 for p in cuerpo["productos"]))

    def test_api_productos_parametro_invalido_da_400(self):
        respuesta = self.cliente.get("/api/productos?min_precio=abc")
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("min_precio", respuesta.get_json()["error"])

    def test_api_productos_orden_invalido_da_400(self):
        respuesta = self.cliente.get("/api/productos?orden=voltear")
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("orden", respuesta.get_json()["error"])

    def test_api_producto_por_asin(self):
        respuesta = self.cliente.get("/api/productos/B0GW9TVHJB")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.get_json()["marca"], "Samsung")

    def test_api_producto_inexistente_da_404(self):
        respuesta = self.cliente.get("/api/productos/XXXXXXXXXXXX")
        self.assertEqual(respuesta.status_code, 404)
        self.assertIn("error", respuesta.get_json())

    def test_api_metricas_trae_las_cuatro_secciones(self):
        cuerpo = self.cliente.get("/api/metricas").get_json()
        for seccion in ("resumen", "por_marca", "distribucion_precio", "mejor_calificado"):
            self.assertIn(seccion, cuerpo)

    def test_ruta_api_desconocida_da_404_json(self):
        respuesta = self.cliente.get("/api/otra_cosa")
        self.assertEqual(respuesta.status_code, 404)
        self.assertIn("error", respuesta.get_json())


if __name__ == "__main__":
    unittest.main()
