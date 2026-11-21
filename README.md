# EA3 — API del catálogo con automatización y despliegue en la nube

[![CI](https://github.com/jesusjoelgonca/ea3-api-catalogo-render/actions/workflows/ci.yml/badge.svg)](https://github.com/jesusjoelgonca/ea3-api-catalogo-render/actions/workflows/ci.yml)
[![CD](https://github.com/jesusjoelgonca/ea3-api-catalogo-render/actions/workflows/cd.yml/badge.svg)](https://github.com/jesusjoelgonca/ea3-api-catalogo-render/actions/workflows/cd.yml)

Tercera evidencia de aprendizaje del curso **Programación para Análisis de Datos**
(PREICA2602B020048). Continúa la EA1 (extracción del catálogo) y la EA2 (panel
estático con GitHub Pages): aquí el mismo catálogo se sirve como **aplicación
web dinámica con Flask**, con una API JSON consultable, y se automatiza el ciclo
completo con **GitHub Actions** hasta el despliegue en **Render**.

- **Estudiante:** Jesus Gonzalez
- **Datos de entrada:** `data/catalogo_consolidado.csv` — 16 teléfonos extraídos
  de Amazon.com en la EA1 (artículo principal: Samsung Galaxy A57 5G, ASIN
  `B0GW9TVHJB`)
- **Servicio publicado:** <https://ea3-catalogo-api.onrender.com>
- **Entregable:** informe en PDF (`Gonzalez_Jesus_Automatizando_EA3.pdf`) y
  cuaderno `Gonzalez_Jesus_Automatizando_EA3.ipynb`, entregados por la plataforma

## Qué hace el proyecto

1. Carga y valida el catálogo consolidado de la EA1 al arrancar (si el CSV no
   cumple el contrato, el servicio no levanta).
2. Sirve una página HTML con el catálogo y las cifras del mercado.
3. Expone una API JSON con filtros por marca, búsqueda de texto, rango de
   precios y cinco órdenes de clasificación.
4. GitHub Actions ejecuta las pruebas en cada cambio (4 combinaciones de
   sistema operativo × Python) y, al llegar a `main`, Render reconstruye y
   publica el servicio; el flujo de CD verifica que la versión publicada sea
   exactamente el commit desplegado.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Página del catálogo con métricas del mercado |
| GET | `/healthz` | Estado del servicio y commit desplegado |
| GET | `/api/productos` | Catálogo completo; admite `marca`, `q`, `min_precio`, `max_precio`, `orden` |
| GET | `/api/productos/<asin>` | Un producto por ASIN (404 si no existe) |
| GET | `/api/metricas` | Resumen, agregados por marca, distribución y top |

Parámetros de `/api/productos`:

- `marca=Samsung` — coincidencia exacta, sin distinguir mayúsculas.
- `q=galaxy` — búsqueda de texto en el título.
- `min_precio=300&max_precio=800` — rango cerrado; excluye los sin precio.
- `orden=nombre|precio_asc|precio_desc|calificacion|resenas`.

Los parámetros inválidos devuelven `400` con un mensaje que nombra el
parámetro y el problema; los recursos ausentes devuelven `404` con JSON.

## Instalación y uso

Requiere Python 3.12 o superior.

```bash
pip install -r requirements.txt

# Servidor de desarrollo
python wsgi.py            # http://127.0.0.1:5000

# Pruebas unitarias (41)
python -m unittest discover -s tests -v
```

## Estructura

```
EA3/
├── Gonzalez_Jesus_Automatizando_EA3.ipynb   # cuaderno ejecutado (evidencia)
├── wsgi.py                    # punto de entrada de gunicorn / flask
├── render.yaml                # blueprint del servicio en Render
├── requirements.txt           # flask + gunicorn
├── data/
│   └── catalogo_consolidado.csv   # catálogo de la EA1 (insumo)
├── src/servicio/
│   ├── app.py                 # fábrica de la aplicación y endpoints
│   ├── datos.py               # carga y validación del CSV
│   ├── metricas.py            # indicadores del mercado
│   ├── filtros.py             # filtros y órdenes de la API
│   └── templates/index.html   # página servida en la raíz
├── tests/                     # 41 pruebas (datos, métricas, filtros, API)
└── .github/workflows/         # integración y despliegue continuos
```

## Flujo de trabajo DevOps

El desarrollo siguió el mismo esquema de ramas por funcionalidad de la EA2:
cada característica entra a `main` por medio de un *pull request* que GitHub
Actions verifica antes de fusionar, y cada fusión dispara el despliegue.

### Integración continua (`.github/workflows/ci.yml`)

Corre en cada *push* y en cada *pull request*, sobre una matriz de
**Ubuntu y Windows × Python 3.12 y 3.13**. Instala las dependencias, compila
todos los módulos (`compileall`) y ejecuta las 41 pruebas. La matriz demuestra
que la API no depende del sistema operativo ni de la versión menor de Python.

### Despliegue continuo (`.github/workflows/cd.yml`)

Al actualizarse `main`, Render construye y publica el servicio por su cuenta
(`autoDeploy`, configurado en `render.yaml`). El flujo de CD completa el ciclo:

1. Dispara el *deploy hook* de Render cuando el secreto `RENDER_DEPLOY_HOOK`
   está configurado.
2. Consulta `/healthz` hasta que la respuesta reporte el SHA del commit que
   acaba de fusionarse: Render inyecta `RENDER_GIT_COMMIT` en cada release, de
   modo que la verificación confirma que **la versión publicada es exactamente
   la de este commit**, no solo que el servicio responde.

Configuración requerida en el repositorio (Settings → Secrets and variables →
Actions):

- Variable `RENDER_URL`: URL pública del servicio, sin `/` final.
- Secreto `RENDER_DEPLOY_HOOK` (opcional): URL del *deploy hook* de Render.

## Estado

Operativo. El servicio responde en Render con el catálogo completo, la rama
`main` exige los cuatro trabajos de CI en verde antes de fusionar, y cada
fusión queda verificada por el flujo de CD contra el SHA publicado. El
cuaderno `Gonzalez_Jesus_Automatizando_EA3.ipynb` reproduce la cadena completa:
catálogo, API en pruebas, flujos de Actions y verificación del servicio vivo.
