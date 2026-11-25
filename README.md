# Venison Returns Voice Agent

Agente de voz que atiende llamadas de clientes de una tienda online ficticia (**Venison**) para gestionar
devoluciones: comprueba si un pedido se puede devolver y, si se puede, registra la devolución. Es un proyecto de
demostración de extremo a extremo: base de datos, API, despliegue en la nube y agente de voz.

## Cómo funciona

```
Cliente --llamada--> Vapi --HTTPS + X-API-Key--> API (FastAPI) --> PostgreSQL
                  (voz y modelo)            (contenedor en AWS Lightsail)   (Lightsail)
```

1. El cliente llama y el agente (en [Vapi](https://vapi.ai)) le pide el número de pedido y el código postal.
2. Para comprobar y registrar, el agente llama a **dos herramientas** que hacen una petición HTTPS a la API.
3. La API consulta la base de datos, **aplica las reglas de negocio** y responde con una frase lista para leerse en
   voz alta.

Las reglas viven en la API y no en el prompt del agente: aunque el modelo se equivoque al llamar a una herramienta,
la API no registra nada que incumpla la política.

## Política de devoluciones (ficticia)

Resumen de [docs/politica.md](docs/politica.md):

- Un pedido se puede devolver dentro de los **30 días** desde su fecha.
- Los productos de **outlet** no se devuelven.
- Cada pedido admite **una sola** devolución.
- El cliente se identifica con el **número de pedido y su código postal**.
- La solución puede ser **reembolso** o **cambio**, según elija el cliente.
- El agente **no promete plazos** de reembolso: los confirma el equipo.

## La API

| Endpoint | Para qué sirve | ¿Necesita clave? |
|---|---|---|
| `GET /health` | Comprobar que la API está viva | No |
| `GET /orders/{id}` | Consultar un pedido | Sí |
| `POST /returns/eligibility` | Saber si un pedido se puede devolver (`order_id`, `postal_code`) | Sí |
| `POST /returns` | Registrar una devolución (`order_id`, `postal_code`, `resolution`, `reason` opcional) | Sí |

La clave se envía en la cabecera `X-API-Key`. Sin ella, o con una incorrecta, la API responde **401**. Los dos
endpoints de `/returns` responden siempre **200** con un `code` (`ok`, `registered`, `not_found`, `already_returned`,
`outlet` o `expired`) y un `message` en español. Con la API arrancada, `/docs` muestra la documentación interactiva.

## Qué hay en el repositorio

```
returns-voice-agent/
├── api/                   API en Python (FastAPI + PostgreSQL)
│   ├── app/               main.py (endpoints y reglas) y db.py (conexión)
│   ├── tests/             42 tests con pytest
│   ├── Dockerfile         imagen para Lightsail (linux/amd64)
│   ├── .env.example       variables de entorno, con valores falsos
│   └── README.md          arrancar la API, base de tests y tests
├── db/
│   ├── schema.sql         tablas customers, orders y returns
│   └── seed.sql           datos de demostración (recarga completa)
└── docs/
    ├── politica.md        política de devoluciones
    ├── DEPLOY.md          despliegue en AWS Lightsail, paso a paso
    └── VAPI.md            configuración del agente de voz en Vapi
```

## Probarlo en local

Hace falta [uv](https://docs.astral.sh/uv/) y PostgreSQL. Desde la carpeta `api/`:

```bash
cp .env.example .env                                  # rellena DATABASE_URL, TEST_DATABASE_URL y API_KEY
uv sync                                               # instala las dependencias
uv run --env-file .env uvicorn app.main:app --reload  # arranca la API
uv run --env-file .env pytest -v                      # ejecuta los tests
```

Antes hay que crear la base y cargar `db/schema.sql` y `db/seed.sql`, y una base aparte para los tests. Los pasos
completos están en [api/README.md](api/README.md). Los tests **vacían** su base, así que se niegan a ejecutarse si su
nombre no termina en `_test`.

## Despliegue y agente de voz

- **[docs/DEPLOY.md](docs/DEPLOY.md):** comparativa de opciones en AWS, por qué se eligió Lightsail, los pasos que se
  siguieron, los problemas que aparecieron y cómo actualizarlo o apagarlo.
- **[docs/VAPI.md](docs/VAPI.md):** ajustes del asistente, las cuatro herramientas, el prompt y las pruebas de voz.

## Seguridad

- Ningún secreto está en el repositorio: la clave de la API y la conexión a la base se leen de variables de entorno,
  y `.env` está en `.gitignore`.
- La imagen de Docker se publica sin secretos; la configuración llega al contenedor desde la consola de Lightsail.
- Los datos son ficticios. La base de la demo tiene el acceso público activado y la protege solo su contraseña.

## Estado y límites

- Es una **demo**: los datos son de prueba y las fechas de los pedidos del seed envejecen con el tiempo, por lo que
  conviene recargar el seed antes de repetir pruebas.
- La transferencia a una persona se ha probado como llamada a la herramienta desde el navegador, pero no por
  teléfono real.
- Cada pedido admite una sola devolución: para repetir un registro hay que recargar el seed o usar otro pedido.
