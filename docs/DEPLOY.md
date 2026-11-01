# Despliegue en AWS (Lightsail)

Estado: **desplegado y verificado el 2026-11-01**. Este documento recoge la comparativa que llevó a elegir Lightsail, el
estado actual, cómo se hizo de verdad (con los problemas que aparecieron) y cómo actualizarlo o apagarlo.

Objetivo: la API FastAPI + una base de datos PostgreSQL en AWS, con una URL HTTPS, usando servicios gestionados
(sin Kubernetes ni servidor propio). Todo lo de AWS se hizo con clics en la consola web.

## 0. Estado actual

| Pieza | Valor |
|---|---|
| Región | Europa (Estocolmo), `eu-north-1`. La consola la fijó por defecto: no hubo selector de región |
| Base de datos | Lightsail, recurso `venison-db`, PostgreSQL 18.6, plan Standard 1 GB (15 $/mes) |
| Nombre de la base dentro del servidor | **`dbvenison`** (no `venison`: ver 3.4) |
| Acceso a la base | **Modo público activado**; la única protección es la contraseña de 32 caracteres alfanuméricos |
| Contenedor | Lightsail, servicio `returns-api`, Micro, escala 1 (10 $/mes) |
| Imagen | `alexroca7/returns-api:v1`, en Docker Hub, repositorio **público**, `linux/amd64`, sin secretos |
| URL pública | En la consola: Lightsail → Containers → `returns-api` → **Public domain**. Es HTTPS con certificado de Amazon |
| Variables de entorno del contenedor | `DATABASE_URL` y `API_KEY`, puestas en la consola de Lightsail |
| Dónde están los secretos | En el gestor de contraseñas (app Contraseñas): `returns-api API_KEY producción`, `Docker Hub · token subir-imagen` y `Lightsail · base de datos venison`. **Nunca en el repositorio ni en la imagen** |
| Coste | ~25 $/mes en total, se cobre o no uso |

Verificación del 2026-11-01 sobre la URL pública:
- `GET /health` sin clave: 200.
- `GET /orders/1`, `POST /returns/eligibility` y `POST /returns` sin clave: 401.
- `GET /docs`: 200 (abierto a propósito).
- `POST /returns/eligibility` con la clave de producción y el pedido 1: 200, `eligible: true`, `code: ok`.
  Eso demuestra que el contenedor llega a la base y lee los datos del seed.

## 1. Lo que hay que saber de tu cuenta (plan gratuito)

- El plan gratuito dura **6 meses o hasta gastar los créditos** (100 $ al registrarte, hasta 100 $ más por completar
  actividades), lo que ocurra antes.
- Al terminar, AWS **suspende la cuenta**. Tienes 90 días para pasar al plan de pago; si no, **borra la cuenta y sus datos**.
  Al pasar al plan de pago se conservan los créditos que queden. No se puede volver atrás.
- Las fuentes se contradicen en cuándo caducan los créditos (6 o 12 meses). Mira la fecha real en la consola, en
  Billing.
- El plan gratuito no es para datos sensibles. Aquí los datos son ficticios, así que no hay problema.
- Algunos servicios requieren el plan de pago. En la lista oficial de servicios permitidos aparecen RDS, Lightsail, ECS,
  ECR, Elastic Load Balancing, Elastic Beanstalk y Lambda. **AWS App Runner no aparece.** Fargate y NAT Gateway no se
  nombran. La lista dice qué servicios entran, pero no siempre qué tamaños o funciones concretas, así que la consola
  puede avisarte de algo que aquí no figura.
- Con un presupuesto de 100 $, lo que importa es el **coste mensual**: 25 $/mes agotan los créditos en unos 4 meses,
  y 40 $/mes en unos 2,5 meses.

## 2. Comparativa

Los precios de Lightsail vienen de su página oficial. Los de Fargate, ALB y RDS **no se pudieron leer de la página
oficial**: son estimaciones con fuentes de terceros y hay que confirmarlas en el
[Calculador de precios de AWS](https://calculator.aws/) antes de elegir.

| | A. App Runner | B. Lightsail (contenedor + base gestionada) | C. ECS Express Mode + RDS | D. Elastic Beanstalk + RDS |
|---|---|---|---|---|
| ¿Se puede usar? | **No**: cerrado a clientes nuevos desde el 30-abr-2026 | Sí, Lightsail está en la lista del plan gratuito | Sí: ECS, ECR, ELB y RDS están en la lista. Fargate no se nombra | Sí, Beanstalk está en la lista |
| Coste mensual aprox. | — | **~25 $** (contenedor Micro 10 $ + base 15 $) | **~40 $** (Fargate ~9 + ALB ~16 + RDS ~12 + disco ~2) | **~40 $** (instancia EC2 ~7 + ALB ~16 + RDS ~14) |
| URL HTTPS sin dominio propio | — | **Sí**, incluida | Sí, según AWS (formato de la URL sin confirmar) | **No**: HTTPS exige certificado, y eso exige dominio propio y balanceador |
| ¿Docker en tu Mac? | — | **Sí**: se construye en tu Mac y se publica en Docker Hub | **Sí**: imagen en ECR | No (subes un zip) |
| Pasos aprox. | — | ~12 | ~18 (roles IAM, red, ECR, RDS, servicio) | ~14 más dominio y certificado |
| Qué puede salir mal | — | Conexión privada contenedor–base sin documentar (ver 3.2); Docker; el contenedor se cobra aunque esté parado | Roles IAM y redes para un principiante; coste mayor; Fargate sin confirmar en el plan gratuito | Sin dominio no hay HTTPS; hay una instancia EC2 que mantener; coste mayor |

También existe **Lambda + URL de función + RDS**: URL HTTPS incluida, sin Docker y coste cercano a 12–14 $ (sobre todo la base). Lo descarto
porque obliga a cambiar el código (adaptador para FastAPI), a empaquetar `psycopg` para Linux desde un Mac arm64 y a
meter la base en una red privada. Para un principiante es lo más fácil de que se atasque. No lo he investigado a fondo.

Fuentes: [precios de Lightsail](https://aws.amazon.com/lightsail/pricing/),
[aviso de App Runner](https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html),
[ECS Express Mode](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html),
[servicios del plan gratuito](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html),
[términos del plan gratuito](https://aws.amazon.com/free/terms/),
[precios de Elastic Beanstalk](https://aws.amazon.com/elasticbeanstalk/pricing/),
[precios de RDS PostgreSQL](https://aws.amazon.com/rds/postgresql/pricing/).

## 3. Lightsail (contenedor + base PostgreSQL gestionada): lo que se hizo

Se eligió B por ser la más simple, la más barata y con precio fijo, y la única donde la URL HTTPS viene incluida sin
comprar un dominio. La alternativa seria es C: es lo que AWS recomienda como sustituto de App Runner y deja la base
privada, pero cuesta más y tiene bastantes más piezas.

### 3.1 Cambio de plan respecto al plan original

El plan original usaba un usuario IAM, `aws login` y el plugin `lightsailctl` para subir la imagen. Se cambió por
**Docker Hub como repositorio público** y Lightsail descarga la imagen desde ahí. Es más corto, pero cualquiera puede
descargar la imagen. Contiene solo el código de `app/` y las librerías, y **ningún secreto**: la configuración llega por
variables de entorno en la consola de Lightsail. Se comprobó antes de publicarla (ver 3.3, fase 1).

Consecuencias de ese cambio:
- Se entra a la consola de AWS con la cuenta raíz: conviene tener su MFA activado.
- La AWS CLI está instalada en el Mac pero no se usa.
- Tu Mac es **arm64**: la imagen se construye para `linux/amd64`. La documentación de Lightsail no dice si acepta arm64,
  así que se mantuvo amd64.

### 3.2 La red entre el contenedor y la base

La documentación de Lightsail explica cómo conectar un contenedor a la base usando el **endpoint público** de la base, y
no documenta que un contenedor alcance una base en modo privado.

**Resultado:** el contenedor conecta por el endpoint público y la base quedó con el **modo público activado**. No se
probó a desactivarlo. La documentación del modo público no menciona ninguna lista de IPs permitidas, así que la única
protección es la contraseña. Con datos ficticios es aceptable en una demo. Si hace falta base privada de verdad, la
alternativa es la opción C. La contraseña de PostgreSQL en Lightsail no puede llevar `/`, `"`, `@` ni espacios.

### 3.3 Pasos que se siguieron

**Fase 1: imagen en Docker Hub**
1. Construir la imagen: `docker build --platform linux/amd64 -t returns-api:test .` desde `api/`. Probarla en local con
   `docker run` y variables de entorno de prueba, y comprobar con `curl` que `/health` da 200 y el resto 401.
2. Comprobar que no lleva secretos: ningún archivo `.env*` dentro, y los valores reales de tu `.env` no aparecen en los
   archivos de la imagen. `api/.dockerignore` excluye `.env` y variantes.
3. Etiquetarla `alexroca7/returns-api:v1`. En Docker Hub: crear el repositorio `returns-api` **público** y un token de
   acceso con permisos de lectura y escritura.
4. `docker login -u alexroca7` (con el token como contraseña), `docker push alexroca7/returns-api:v1`, y comprobar que
   es público con `docker logout` y `docker pull --platform linux/amd64 alexroca7/returns-api:v1`.

**Fase 2: base de datos (Lightsail → Databases → Create database)**
5. Región por defecto (Estocolmo), PostgreSQL, **Specify login credentials** con un usuario administrador y una
   contraseña alfanumérica de 32 caracteres, **Specify the master database name**, plan Standard de 15 $.
   Esperar a que el estado pase a **Available**.

**Fase 3: cargar esquema y seed**
6. `venison-db` → pestaña **Networking** → activar **Public mode** (pasa por **Modifying** y vuelve a **Available**).
7. Conectar desde el Mac con `psql "host=ENDPOINT port=5432 dbname=postgres user=USUARIO sslmode=require"`. El endpoint
   está en la pestaña **Connect**.
8. Averiguar el nombre real de la base: `SELECT datname FROM pg_database WHERE NOT datistemplate;` y cambiarse a ella
   con `\c NOMBRE`.
9. Con la base seleccionada: `\i db/schema.sql`, `\i db/seed.sql` (el seed es seguro aquí porque la base está vacía) y
   comprobar `SELECT (SELECT count(*) FROM customers), (SELECT count(*) FROM orders), (SELECT count(*) FROM returns);`.
   Resultado esperado: 5, 11 y 1.

**Fase 4: contenedor (Lightsail → Containers → Create container service)**
10. Región Estocolmo (la misma que la base), **Power Micro**, **Scale 1**, **Create a deployment** → **Specify a custom
    deployment**:
    - **Container name:** `returns-api`. **Source image:** `alexroca7/returns-api:v1`.
    - **Open ports:** `8000`, HTTP.
    - **Environment variables:** `API_KEY` y `DATABASE_URL` con la forma
      `postgresql://USUARIO:CONTRASEÑA@ENDPOINT:5432/dbvenison?sslmode=require`.
    - Endpoint público: **Endpoint container** `returns-api`, puerto `8000`, **Health check path** `/health`.
    - Nombre del servicio `returns-api`. Esperar a **Running** (el despliegue pasa a **Active**).

**Fase 5: verificación**
11. Con `curl` sobre la URL pública: `/health` sin clave (200), un endpoint protegido sin clave (401) y
    `POST /returns/eligibility` con la clave (200, `ok`). La clave se guarda en una variable sin mostrarla con
    `read -s KEY`.

### 3.4 Qué puede salir mal y cómo se detecta

| Problema | Cómo se nota | Qué hacer |
|---|---|---|
| El nombre de la base no es el que esperabas | `psql` da `FATAL: database "venison" does not exist`. **Pasó**: la base se llamaba `dbvenison` | Conectar a `dbname=postgres`, listar con `SELECT datname FROM pg_database WHERE NOT datistemplate;` y usar ese nombre también en `DATABASE_URL` |
| `\l` da `column d.daticulocale does not exist` | **Pasó**: `psql` 16 con servidor 18 | No es grave: usar la consulta de arriba en lugar de `\l` |
| Una consulta SQL "no hace nada" | El prompt cambia de `=>` a `->` | Falta el `;` final. Los comandos con `\` no lo necesitan |
| `password authentication failed` | **Pasó una vez**: un pegado fallido (la Terminal no muestra lo que pegas) | Volver a copiar la contraseña desde el gestor y repetir |
| No aparece selector de región | **Pasó**: la consola ya estaba en Estocolmo | Usar esa región para todo; el contenedor debe coincidir con la base |
| El contenedor no conecta a la base | `/health` responde 200 pero `/orders/1` con clave da 500; lo explica el log (**Deployments** → **Open log**) | Revisar `DATABASE_URL`, el nombre de la base, el modo público y `sslmode=require` |
| La imagen no arranca en Lightsail | El despliegue queda en **Failed** | Casi siempre es la arquitectura: reconstruir con `--platform linux/amd64` |
| El despliegue tarda o se queda en "desplegando" | La comprobación de salud falla | Comprobar que la ruta `/health` y el puerto 8000 coinciden |
| Costes que siguen aunque no uses nada | Billing | El contenedor se cobra aunque esté desactivado y la base aunque esté parada: **hay que borrarlos** |
| Se agotan los créditos | Alerta de presupuesto | Pasar al plan de pago o borrar los recursos |

### 3.5 Subir una versión nueva de la API

1. Desde `api/`: `docker build --platform linux/amd64 -t alexroca7/returns-api:v2 .` (usa una etiqueta nueva cada vez).
2. Repetir el escaneo de secretos de la fase 1, `docker login -u alexroca7` y `docker push alexroca7/returns-api:v2`.
3. En Lightsail: Containers → `returns-api` → **Deployments** → modificar el despliegue y cambiar **Source image** a
   `alexroca7/returns-api:v2` → **Save and deploy**. (Los nombres de los botones pueden variar.)

### 3.6 Apagar todo

A finales de noviembre, para dejar de pagar:
1. Lightsail → Containers → `returns-api` → borrar el servicio.
2. Lightsail → Databases → `venison-db` → borrar la base. Parar no basta: ambos se cobran mientras existan.
3. Docker Hub: borrar el token `subir-imagen` y, si quieres, el repositorio `returns-api`.
4. Billing: comprobar que no queda ningún cargo.

## 4. Decisiones tomadas (2026-11-01)

- La base queda **pública con contraseña fuerte**; no se probó el modo privado.
- Docker Desktop.
- La demo estará en marcha hasta **finales de noviembre**; después, apagar todo (ver 3.6).
- Imagen en **Docker Hub público** (sin secretos) en lugar de usuario IAM + `lightsailctl`.
