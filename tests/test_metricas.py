"""Pruebas de los indicadores del mercado (heredadas de la EA2)."""

import unittest
from pathlib import Path

from src.servicio.datos import cargar
from src.servicio.metricas import (
    correlacion_precio_calificacion,
    distribucion_precio,
    mejor_calificado,
    por_marca,
    resumen_general,
)

CATALOGO = Path("data/catalogo_consolidado.csv")


class PruebaResumenGeneral(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.productos = cargar(CATALOGO)

    def test_totales_del_catalogo(self):
        resumen = resumen_general(self.productos)
        self.assertEqual(resumen["productos"], 16)
        self.assertEqual(resumen["con_precio"], 15)
        self.assertEqual(resumen["resenas_totales"], sum(p.resenas for p in self.productos))

    def test_marcas_distintas(self):
        resumen = resumen_general(self.productos)
        self.assertEqual(resumen["marcas"], len({p.marca for p in self.productos}))

    def test_rango_de_precios_coherente(self):
        resumen = resumen_general(self.productos)
        self.assertLessEqual(resumen["precio_minimo"], resumen["precio_mediano"])
        self.assertLessEqual(resumen["precio_mediano"], resumen["precio_maximo"])

    def test_descuento_promedio_en_escala_cero_cien(self):
        resumen = resumen_general(self.productos)
        descuento = resumen["descuento_promedio"]
        self.assertTrue(descuento is None or 0 <= descuento <= 100)


class PruebaPorMarca(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.filas = por_marca(cargar(CATALOGO))

    def test_filas_suma_el_total(self):
        self.assertEqual(sum(f["productos"] for f in self.filas), 16)

    def test_ordenado_por_precio_promedio_descendente(self):
        precios = [f["precio_promedio"] for f in self.filas if f["precio_promedio"] is not None]
        self.assertEqual(precios, sorted(precios, reverse=True))

    def test_samsung_presente(self):
        marcas = {f["marca"] for f in self.filas}
        self.assertIn("Samsung", marcas)


class PruebaDistribucionYCorrelacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.productos = cargar(CATALOGO)

    def test_tramos_cubren_todos_los_con_precio(self):
        tramos = distribucion_precio(self.productos)
        self.assertEqual(sum(t["productos"] for t in tramos), 15)

    def test_correlacion_en_rango_valido(self):
        r = correlacion_precio_calificacion(self.productos)
        self.assertIsNotNone(r)
        self.assertTrue(-1 <= r <= 1)

    def test_mejor_calificado_devuelve_cinco(self):
        top = mejor_calificado(self.productos, cantidad=5)
        self.assertEqual(len(top), 5)
        calificaciones = [t["calificacion"] for t in top]
        self.assertEqual(calificaciones, sorted(calificaciones, reverse=True))


if __name__ == "__main__":
    unittest.main()
