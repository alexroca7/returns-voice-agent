# Plan de despliegue en AWS

Estado: **solo plan**. No se ha creado nada en AWS. Investigado el 2026-11-01 en la documentación de AWS.

Objetivo: la API FastAPI + una base de datos PostgreSQL en AWS, con una URL HTTPS, usando servicios gestionados
(sin Kubernetes ni servidor propio). Tú haces los clics en la consola web; yo preparo los archivos y te guío.

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
| ¿Docker en tu Mac? | — | **Sí**: la imagen se sube desde tu máquina | **Sí**: imagen en ECR | No (subes un zip) |
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

## 3. Recomendación: B, Lightsail (contenedor + base PostgreSQL gestionada)

Es la más simple, la más barata y con precio fijo, y la única donde la URL HTTPS viene incluida sin comprar un dominio.
La alternativa seria es C: es lo que AWS recomienda como sustituto de App Runner y deja la base privada, pero cuesta
más y tiene bastantes más piezas.

### 3.1 Lo que necesita instalar tu Mac

- **Docker** (Docker Desktop u OrbStack): no lo tienes instalado.
- **AWS CLI v2** y el plugin **lightsailctl** (para subir la imagen): no los tienes instalados.
- `psql` y `uv` ya están.
- Tu Mac es **arm64**: la imagen se construye para `linux/amd64` (`docker buildx build --platform linux/amd64`). Hay que
  confirmar en la consola de Lightsail qué arquitectura usan los contenedores.

### 3.2 Riesgo principal: la red entre el contenedor y la base

La documentación de Lightsail explica cómo conectar un contenedor a la base usando el **endpoint público** de la base.
No he encontrado documentado que un contenedor alcance una base en modo privado. Por tanto:

1. Para cargar `schema.sql` y `seed.sql` desde tu Mac, la base tendrá que estar en modo público (temporalmente).
2. Después probaremos a ponerla en modo privado. Si el contenedor sigue conectando, perfecto.
3. Si no conecta, la base queda pública, protegida solo por usuario y contraseña. Con datos ficticios es aceptable
   en una demo, pero hay que usar una contraseña larga y aleatoria. Si prefieres base privada de verdad, la
   alternativa es C.

### 3.3 Pasos

Fase 0, preparación (sin coste):
1. Activar MFA en el usuario raíz y crear una alerta de presupuesto en Billing (por ejemplo 20 $/mes).
2. Anotar la fecha de caducidad de los créditos (Billing) y elegir región: **Europa (Irlanda)** si Lightsail la ofrece.
3. Instalar Docker, AWS CLI v2 y lightsailctl. Yo te doy los comandos.

Fase 1, base de datos (consola, ~15 $/mes desde aquí):
4. Lightsail → Databases → PostgreSQL, plan Standard (1 GB). Contraseña larga y aleatoria.
5. Activar acceso público de forma temporal y copiar el endpoint.
6. Cargar `db/schema.sql` y `db/seed.sql` con `psql` desde tu Mac. El seed es seguro aquí porque la base está vacía.

Fase 2, imagen (yo preparo los archivos):
7. Crear `api/Dockerfile` y `api/.dockerignore`. `.env` nunca debe entrar en la imagen.
8. Construir la imagen y probarla en local con `docker run` y tu `.env`.

Fase 3, contenedor (consola, +10 $/mes):
9. Lightsail → Containers → crear servicio Micro, escala 1.
10. Subir la imagen con `aws lightsail push-container-image` y crear el despliegue: puerto 8000,
    comprobación de salud en `/health`, variables `DATABASE_URL` (con `?sslmode=require`) y `API_KEY`, y activar el
    endpoint público. Las variables se ven en la consola de Lightsail: no pongas ahí nada que no sea esto.

Fase 4, verificación:
11. Con `curl` sobre la URL HTTPS: `/health` sin clave, 401 sin clave, y los 7 casos de elegibilidad con clave.
    Probar el botón Authorize en `/docs`.
12. Probar a poner la base en privado (ver 3.2) y repetir el paso 11.

### 3.4 Qué puede salir mal y cómo se detecta

| Problema | Cómo se nota | Qué hacer |
|---|---|---|
| El contenedor no conecta a la base | `/health` responde 200 pero `/orders/1` da 500; lo explica el log del contenedor en la consola | Revisar `DATABASE_URL`, el modo público/privado y `sslmode=require` |
| La imagen no arranca en Lightsail | El despliegue queda en "fallido" | Casi siempre es la arquitectura: reconstruir con `--platform linux/amd64` |
| El despliegue tarda o se queda en "desplegando" | La comprobación de salud falla | Comprobar que la ruta `/health` y el puerto 8000 coinciden |
| Costes que siguen aunque no uses nada | Billing | El contenedor se cobra aunque esté desactivado y la base aunque esté parada: **hay que borrarlos** |
| Se agotan los créditos | Alerta de presupuesto | Pasar al plan de pago o borrar los recursos |

### 3.5 Apagar todo

Cuando termines la demo, borra el servicio de contenedores y la base en la consola de Lightsail. Parar no basta.

## 4. Antes de empezar (decisiones tuyas)

- ¿Aceptas la base **pública con contraseña fuerte** si la conexión privada no funciona, o prefieres ir directo a C?
- ¿Prefieres Docker Desktop u OrbStack (más ligero)? Ambos valen.
- ¿Cuánto tiempo necesitas la demo en marcha? Define si vale la pena para ti pagar 25 $/mes.
