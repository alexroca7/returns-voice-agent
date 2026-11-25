# Visión de negocio: por qué un agente de voz para devoluciones

Este documento recoge el lado **cliente y negocio** del proyecto: qué problema resuelve, para quién, qué decisiones de
diseño se tomaron y por qué, cómo se mediría si funciona y qué riesgos tiene. El lado técnico está en
[docs/DEPLOY.md](DEPLOY.md) y [docs/VAPI.md](VAPI.md).

> Es un proyecto de demostración con una tienda ficticia (Venison). Las **métricas** de la sección 5 son una propuesta
> de cómo medir el éxito: **todavía no se han medido**. No hay cifras reales de ahorro ni de uso.

## 1. El problema

Una tienda online recibe, entre sus llamadas de atención al cliente, muchas sobre **devoluciones**. Son llamadas muy
repetitivas: el cliente quiere saber si puede devolver algo y cómo, y casi siempre la respuesta depende de unas pocas
reglas (el plazo, si el producto es de outlet, si ya hay una devolución abierta).

Eso genera tres costes:
- **Para el cliente:** esperas y horarios limitados para algo que debería ser inmediato.
- **Para el equipo:** personas dedicadas a aplicar las mismas reglas una y otra vez, en lugar de resolver los casos
  difíciles.
- **Para el negocio:** respuestas distintas según quién atienda y devoluciones registradas a mano, con errores.

## 2. La propuesta

Un agente de voz que atiende la llamada, **comprueba las reglas con los datos reales del pedido** y **registra la
devolución** si procede. Cuando algo se sale del guion, **pasa la llamada a una persona**.

| Para quién | Qué gana |
|---|---|
| **El cliente** | Respuesta inmediata, a cualquier hora y sin esperas |
| **El equipo de atención** | Menos llamadas repetitivas; las devoluciones llegan ya registradas y con motivo |
| **El negocio** | Reglas aplicadas siempre igual, trazabilidad de cada devolución y atención que escala sin contratar proporcionalmente |

## 3. Alcance: poco y bien hecho

El agente hace **una sola cosa**: gestionar devoluciones. Es una decisión deliberada, porque un caso de uso pequeño se
puede construir, probar y explicar de punta a punta. Dentro de ese caso:

**Lo que hace:** identifica al cliente con su número de pedido y su código postal, comprueba si el pedido se puede
devolver, deja elegir reembolso o cambio, pregunta el motivo y registra la solicitud.

**Lo que no hace, a propósito:**
- **No aprueba reembolsos ni promete plazos o importes.** Registra una solicitud; la confirma el equipo.
- **No hace excepciones** a la política. Si el cliente las pide, se las explica con amabilidad.
- **No resuelve casos raros.** Ante un fallo técnico o si el cliente lo pide, pasa con una persona.

## 4. Las reglas de negocio y su razón

Vienen de la política de [docs/politica.md](politica.md):

| Regla | Qué protege al negocio |
|---|---|
| Hasta **30 días** desde el pedido | Un plazo claro y el mismo para todos |
| **Outlet** no se devuelve | Respeta la condición de venta del producto rebajado |
| **Una devolución por pedido** | Evita duplicados y abusos |
| Se identifica con **pedido + código postal** | Una comprobación mínima de que quien llama conoce el pedido |
| **Reembolso o cambio**, a elección del cliente | Da al cliente una salida y recoge su preferencia |
| **No se prometen plazos** de reembolso | El agente no se compromete a algo que no controla |

**Dónde viven estas reglas:** en la **API**, no en el prompt del agente. Una regla escrita en un prompt no se puede
garantizar, porque un modelo puede equivocarse o dejarse convencer. En el código, se cumple siempre. En las pruebas
se vio: el agente llegó a pedir registrar una devolución fuera de lugar y la API no guardó nada.

## 5. Decisiones de experiencia de voz

Cada decisión se tomó probando llamadas reales y mirando qué fricción generaba:

| Decisión | Por qué |
|---|---|
| Pedir **primero el pedido y luego el código postal**, una pregunta cada vez | Es más fácil de contestar por teléfono |
| **No confirmar los datos la primera vez** | Repetirlos siempre añadía una pregunta sin aportar valor |
| Confirmarlos **solo si no se encuentra el pedido** | Es cuando ayuda de verdad a detectar un error de reconocimiento de voz |
| El número de pedido se dice **completo** ("once") y el código postal **cifra a cifra** | Es como la gente lo dice y lo entiende por teléfono |
| Mensajes **ya redactados** en la API, listos para leer | Respuestas coherentes y sin depender de la improvisación del modelo |
| Si el pedido no existe **o** el código postal no coincide, **la misma respuesta** | No se revela qué pedidos existen |
| Pasar con una persona cuando el cliente lo pide | Respeta que algunos clientes prefieren hablar con alguien |
| Reconocer que es un **asistente virtual** si se le pregunta | Transparencia con el cliente |

## 6. Cómo se mediría el éxito (propuesta, sin medir todavía)

| Métrica | Qué dice | De dónde saldría |
|---|---|---|
| **Llamadas resueltas sin persona** | Si el agente cumple su objetivo | Registros de llamadas de Vapi |
| **Tasa de transferencia a una persona** | Cuántos casos se escapan del guion | Registros de Vapi |
| **Duración media de la llamada** | Eficiencia frente a una llamada con una persona | Vapi |
| **Devoluciones registradas** frente a **rechazadas por la API** | Si los clientes llegan con casos válidos | Tabla `returns` y registros de la API |
| **Peticiones `not_found`** | Si el reconocimiento de voz falla con los números | Registros de la API |
| **Satisfacción del cliente** | Si la experiencia es buena | Encuesta breve tras la llamada |
| **Coste por llamada** frente a una persona | El argumento económico | Facturación de Vapi y de AWS, y el coste del equipo |

## 7. Riesgos y cómo se mitigan

| Riesgo | Mitigación actual | Qué haría falta en producción |
|---|---|---|
| El agente se equivoca al elegir una acción | Las reglas están en la API, que repite las comprobaciones | Más pruebas con distintas voces y acentos, y un modelo mayor |
| Suplantación: identificarse solo con pedido y código postal es débil | Es una demo con datos ficticios | Verificar al cliente, por ejemplo con un código por SMS |
| Datos personales y grabaciones de llamadas | Los datos de la demo son ficticios | Cumplir la normativa de protección de datos: minimizar, informar al cliente y limitar la conservación |
| Caída de la API o de un proveedor | Si una herramienta falla, el agente avisa y pasa con una persona | Monitorización, avisos y un plan de contingencia |
| Dependencia de proveedores (voz, modelo, nube) | Arquitectura por piezas separadas | Poder sustituir una pieza sin rehacer el resto |
| Coste por minuto de llamada | Alcance pequeño | Medir el coste real y compararlo con la atención humana |

## 8. Cómo se adoptaría en un negocio real

1. **Piloto acotado:** derivar una pequeña parte de las llamadas de devoluciones al agente, con transferencia siempre
   disponible, y medir las métricas de la sección 6.
2. **Conectar con los pedidos reales:** hoy los pedidos son datos de demostración. En un negocio real, la API leería
   los pedidos del sistema de la tienda y escribiría las devoluciones donde las gestione el equipo.
3. **Dar visibilidad al equipo:** un panel o aviso con las devoluciones registradas y su estado (la tabla ya prevé
   `pending`, `approved` y `rejected`).
4. **Ampliar con cuidado:** solo después de que el primer caso sea sólido, añadir otros, como seguimiento de pedidos o
   cambios de talla. Mejor poco y fiable que mucho y flojo.

## 9. Qué demuestra este proyecto

Que se puede llevar una idea de negocio concreta de punta a punta: entender el problema, **traducir una política a
reglas comprobables**, construir una API con ellas, probarla de forma automática, desplegarla en la nube y conectarla
a un agente de voz, midiendo en cada paso qué funciona y qué no.
