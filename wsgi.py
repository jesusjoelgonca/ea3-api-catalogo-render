"""Punto de entrada para el servidor WSGI del despliegue.

Render ejecuta ``gunicorn wsgi:app``; localmente la aplicación también puede
levantarse con ``flask --app src.servicio run`` o ``python wsgi.py``.
"""

from src.servicio import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
