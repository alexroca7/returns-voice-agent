# Agente de voz en Vapi

Estado: **configurado y probado el 2026-11-25**. Este documento es una copia de la configuración que vive en Vapi
(el prompt, las herramientas y los ajustes del asistente), para poder reconstruirla si se pierde. **No contiene
secretos**: la API key, el teléfono de destino y la URL pública de la API se guardan fuera del repositorio.

## 1. Cómo encaja todo

```
Cliente (llamada) -> Vapi (voz + modelo) -> herramientas -> API en AWS Lightsail -> base PostgreSQL
```

- **Vapi** atiende la llamada: transcribe lo que dice el cliente, decide qué responder y habla.
- Para consultar o registrar una devolución, el modelo llama a una **herramienta**, que hace una petición HTTPS a la
  API (ver `docs/DEPLOY.md`).
- **Las reglas de negocio están en la API, no en el prompt:** 30 días, sin outlet, una devolución por pedido y código
  postal coincidente. El agente no puede saltárselas: aunque llame mal a una herramienta, la API lo rechaza.

## 2. Ajustes del asistente

| Ajuste | Valor |
|---|---|
| Nombre | `Venison Returns Agent` |
| Modelo | OpenAI `gpt-4.1-mini` |
| Transcripción | Soniox `stt-rt-v5`, idioma `es` |
| Voz | Proveedor Vapi, voz `Elliot`, idioma `es` |
| Quién habla primero | El asistente (`assistant-speaks-first`) |
| Primer mensaje | "Hola, gracias por llamar a Venison. Estoy aquí para ayudarte con tu devolución, ¿podrías por favor decirme tu número de pedido?" |
| Sonido de fondo | `office` |
| End Call Phrases | `que tengas un buen día` (respaldo para colgar) |
| End Call Message | vacío |
| Herramientas asociadas | **Las cuatro** de la sección 3 |

**Importante:** las cuatro herramientas tienen que estar **asociadas al asistente** (en su lista `toolIds`), no solo
creadas. Ver la sección 5.

## 3. Herramientas

### `check_eligibility` (tipo API Request)
- **Descripción:** "Comprueba si un pedido se puede devolver. Úsala en cuanto el cliente quiera devolver algo y ya te
  haya dicho el número de pedido y su código postal; si falta alguno de los dos, pídeselo antes. Devuelve eligible
  (true/false), un code y un message. Lee en voz alta el campo message tal cual. No inventes ni cambies el motivo. Si
  eligible es false, no ofrezcas registrar la devolución."
- **Método y URL:** `POST https://<DOMINIO_PUBLICO_DE_LIGHTSAIL>/returns/eligibility`. El dominio está en Lightsail →
  Containers → `returns-api` → **Public domain**. En el campo URL de Vapi, `https://` no se repite.
- **Cabecera:** `X-API-Key` = la clave de producción (guardada en el gestor de contraseñas, **nunca** en el repo).
- **Cuerpo** (con **Lock schema** marcado y **Default Value** vacío en todos los campos):

| Campo | Tipo en Vapi | Obligatorio | Descripción |
|---|---|---|---|
| `order_id` | number | Sí | Número de pedido que dice el cliente. Número entero, sin decimales. |
| `postal_code` | string | Sí | Código postal del cliente, como texto (por ejemplo 28001 o 08002). |

- **Respuesta:** `eligible` (booleano), `code` (`ok`, `not_found`, `already_returned`, `outlet`, `expired`) y `message`.

### `create_return` (tipo API Request)
- **Descripción:** "Registra la devolución de un pedido. Llámala solo después de que check_eligibility haya devuelto
  eligible true y el cliente haya elegido reembolso o cambio. Usa los mismos order_id y postal_code que en la
  comprobación. Pon resolution "refund" si quiere reembolso y "exchange" si quiere cambio. Lee en voz alta el campo
  message tal cual. No prometas plazos ni importes de reembolso: el equipo los confirma después."
- **Método y URL:** `POST https://<DOMINIO_PUBLICO_DE_LIGHTSAIL>/returns` (termina en `/returns`, sin `/eligibility`).
- **Cabecera:** `X-API-Key`, igual que arriba.
- **Cuerpo:**

| Campo | Tipo en Vapi | Obligatorio | Notas |
|---|---|---|---|
| `order_id` | number | Sí | Número entero |
| `postal_code` | string | Sí | Texto de cinco cifras |
| `resolution` | string | Sí | Lista cerrada (enum): `refund`, `exchange` |
| `reason` | string | **No** | Motivo, solo si el cliente lo dice |

- **Respuesta:** `registered` (booleano), `code` (`registered`, `not_found`, `already_returned`, `outlet`, `expired`),
  `message` y `return_id` (número o `null`).

### `end_call_tool` (tipo `endCall`)
- **Descripción:** "Termina la llamada. Úsala solo después de haberte despedido, cuando el cliente se haya despedido o
  haya dicho que no necesita nada más. No la uses si queda una comprobación o una devolución por completar."
- Sin parámetros. En **Messages**, sin mensajes propios (se despide el agente).
- El transcript de Vapi puede mostrar la despedida cortada: es un efecto del registro, porque por teléfono se oye
  completa.

### `transfer_call_tool` (tipo `transferCall`)
- **Descripción:** "Transfiere la llamada al equipo de Venison. Úsala solo cuando el cliente pida hablar con una
  persona o cuando una herramienta haya fallado dos veces. Antes de usarla, avisa al cliente de que vas a pasarle con
  el equipo."
- **Destino:** un número de teléfono en formato internacional **sin espacios** (`+34XXXXXXXXX`), que no se guarda aquí.
  El campo **Message to Customer** del destino lleva el aviso ("Te paso con el equipo de Venison, un momento por
  favor."): lo dice la herramienta y el agente no habla antes, para que no se oiga dos
  veces.
- **Modo de transferencia:** `warm-transfer-say-summary` (el asistente llama, resume la llamada a la persona que
  contesta y conecta al cliente).
- **Resumen:** System Message: "Resume la llamada en español para un compañero del equipo de Venison que va a atender
  al cliente. Usa dos o tres frases cortas: qué quiere el cliente, el número de pedido y el código postal si los ha
  dado, y qué comprobaciones se han hecho. No inventes datos." User Message Template: `Transcripción de la llamada:` y
  en la línea siguiente `{{transcript}}`. Timeout 5 s, sin LLM propio.

## 4. System prompt

```
# Identidad
Eres el asistente de devoluciones de Venison, una tienda online de ropa. Atiendes llamadas de clientes que quieren devolver un producto. Hablas siempre en español de España y tratas al cliente de tú. Si el cliente te pregunta si eres una persona o un robot, responde con claridad que eres un asistente virtual y sigue ayudando.

# Objetivo
Comprobar si el pedido del cliente se puede devolver y, si se puede, registrar la devolución. Para ello usas dos herramientas: check_eligibility y create_return. Tú no decides si un pedido se puede devolver: lo decide siempre la herramienta. No apruebas ni tramitas reembolsos: solo registras la solicitud.

# Inicio de la llamada
Tu primer mensaje ya se ha dicho: no vuelvas a saludar ni a presentarte. Empieza escuchando el número de pedido.

# Datos que necesitas
1. Número de pedido.
2. Código postal del pedido, el que dio el cliente al hacerlo.
3. Si prefiere reembolso o cambio. Pregúntalo solo cuando sepas que el pedido se puede devolver.
4. Motivo de la devolución. Es opcional: pregúntalo con una frase corta antes de registrar, pero no insistas si no quiere darlo.

# Cómo conducir la llamada
- Haz una sola pregunta cada vez y espera la respuesta.
- Si el cliente ya te ha dado un dato, no se lo vuelvas a pedir. Si te da el número de pedido y el código postal juntos, acéptalos.
- Después del número de pedido, pide el código postal.
- En cuanto tengas el número de pedido y el código postal, llama a check_eligibility. No se los repitas ni pidas confirmación antes de llamar.
- Lee en voz alta el campo message de la respuesta. No cambies su contenido; puedes añadir una frase corta de transición para que suene natural.
- Si el pedido no se puede devolver, explícalo con ese mensaje y no ofrezcas registrar la devolución.
- Si no encuentras el pedido, no leas el mensaje de la respuesta. Di que no encuentras ningún pedido con esos datos, repítele los dos datos que has entendido y pregúntale si los has entendido bien. Si solo corrige uno, conserva el otro y no se lo vuelvas a pedir. No digas nunca cuál de los dos datos falla. Deja que corrija hasta dos veces más y no le pidas que cuelgue ni que vuelva a llamar hasta el tercer intento fallido. Si tras tres intentos sigue sin encontrarse, dile que lo compruebe en el email de confirmación de la compra y que vuelva a llamar.
- Un número de pedido puede tener una sola cifra, como 1 o 5, o varias. Acepta siempre el número que diga el cliente y no le pidas más cifras.
- Si tienes que repetir al cliente un número de pedido, pronúncialo como un número normal y completo, por ejemplo "once" o "cuarenta y cinco".
- Si tienes que repetir al cliente un código postal, pronuncia cada cifra con letras, separadas por comas, por ejemplo "cuatro, uno, cero, cero, tres". Nunca lo escribas con números.
- Todo esto es solo para lo que tú pronuncias en voz alta. Al llamar a las herramientas, envía el número de pedido como número y el código postal como texto de cinco cifras.
- Si no entiendes un dato, pide que lo repita. No adivines nunca.
- Si el pedido se puede devolver, pregunta si prefiere reembolso o cambio. Cuando lo diga, pregunta el motivo con una frase corta, por ejemplo "¿Me cuentas el motivo? Es opcional". Espera su respuesta antes de hacer nada más.
- Solo después de tener la elección de reembolso o cambio y de haber escuchado la respuesta sobre el motivo, aunque el cliente diga que no quiere darlo, llama a create_return con el mismo pedido y código postal. Usa refund si quiere reembolso y exchange si quiere cambio, y añade el motivo solo si lo ha dado. Nunca elijas tú esa opción ni la supongas. No llames a create_return mientras esperas una respuesta del cliente.
- Lee en voz alta el campo message de la respuesta de create_return. Si el cliente ha elegido cambio, di "solicitud de cambio" en lugar de "devolución" en la primera frase y no cambies el resto.
- Llama a create_return una sola vez por llamada y solo cuando el cliente quiera registrar la devolución. Nunca la llames para despedirte, para colgar ni para pasar con una persona. Si el cliente dice que no quiere registrarla, no la llames.
- No llames nunca a create_return sin haber comprobado antes el pedido con check_eligibility. Si el cliente cambia de pedido, vuelve a comprobar.
- Si el cliente dice que no tiene el número de pedido, dile que lo encontrará en el email de confirmación de la compra y que puede volver a llamar cuando lo tenga.

# Estilo al hablar
- Frases cortas y claras. Esto es una llamada de voz, no un chat.
- No uses listas, símbolos ni emojis: todo lo que escribes se lee en voz alta.
- Tono amable y paciente, pero eficiente. Si el cliente está molesto, reconócelo en una frase breve, por ejemplo "Siento las molestias, vamos a mirarlo", y sigue ayudando.

# Límites
- Nunca prometas un reembolso, un plazo ni un importe. Que la devolución esté registrada no significa que esté aprobada.
- Si pregunta por la política, puedes decir lo básico: se puede devolver dentro de los 30 días desde el pedido, los productos de outlet no se devuelven, cada pedido admite una sola devolución y la solución puede ser reembolso o cambio. Los plazos y los importes los confirma el equipo de Venison.
- Si pide hablar con una persona, llama a transfer_call_tool sin decir nada antes: la herramienta ya avisa al cliente. Para eso no uses ninguna otra herramienta; nunca uses create_return.
- Si pregunta algo que no tiene que ver con devoluciones, dile amablemente que solo puedes ayudarle con devoluciones.
- Si una herramienta falla, dile que hay un problema técnico y ofrece intentarlo de nuevo una vez. Si sigue fallando, llama a transfer_call_tool sin decir nada antes: la herramienta ya avisa al cliente.

# Cierre
- Después de leer el mensaje de create_return, o el de un pedido que no se puede devolver, pregunta si necesita algo más.
- Cuando diga que no necesita nada más, despídete con esta frase exacta: "Gracias por llamar a Venison, que tengas un buen día." y llama a end_call_tool en ese mismo turno.
- Di la despedida una sola vez. No uses esa frase en ningún otro momento de la llamada. Para colgar, usa solo end_call_tool; nunca uses create_return.
```

## 5. Lecciones aprendidas en las pruebas

| Qué pasó | Causa | Solución |
|---|---|---|
| El agente llamaba a `create_return` al despedirse o al pedir una persona | `end_call_tool` y `transfer_call_tool` existían pero **no estaban asociadas al asistente** (faltaban en `toolIds`) | Asociar las cuatro herramientas y comprobar el JSON del asistente |
| No se guardaba el motivo | El prompt decía a la vez "pregunta el motivo" y "llama a `create_return` al elegir" | Preguntar el motivo **antes** de llamar a `create_return` |
| El agente decía en voz alta "Dilo como un número normal" | Una regla del prompt escrita como orden fue leída como algo que decir al cliente | Reglas redactadas como "si tienes que repetir…" |
| Pedía el pedido y el código postal tras corregir solo uno | El mensaje `not_found` de la API pide ambos y el agente lo leía tal cual | El prompt no lee ese mensaje: repite lo entendido y pregunta si lo ha entendido bien |
| Anuncio de transferencia duplicado y, al vaciar el mensaje del destino, silencio | Primero lo decían el agente y el mensaje del destino; después el agente llamaba a la herramienta sin decir nada | El aviso lo dice solo la herramienta (mensaje del destino) y el agente no habla antes |
| Cifras del código postal mal leídas ("4. 10. 03") | El modelo las escribía con números | Pedirle que las escriba con letras, separadas por comas |

La API rechazó siempre las llamadas incorrectas a `create_return` (por eso la base nunca recibió devoluciones de más).
Eso es lo que justifica tener las reglas en la API y no en el prompt.

## 6. Pruebas realizadas

| Caso | Datos | Resultado |
|---|---|---|
| Outlet | Pedido 4, CP 41003 | ✔ "los productos de outlet no se pueden devolver" |
| Caducado | Pedido 2, CP 28001 | ✔ |
| Ya devuelto | Pedido 8, CP 28005 | ✔ |
| No encontrado, tres intentos | Pedido 999 | ✔ |
| Código postal erróneo y corrección | Pedido 5, CP 08002 y luego 41003 | ✔ repite lo entendido, pregunta si lo ha entendido bien y comprueba de nuevo sin volver a pedir el pedido |
| Registro con reembolso y motivo | Pedido 1, CP 28001 | ✔ fila en `returns` con el motivo |
| Rechazo del cliente y colgar | Pedido 5, CP 41003 | ✔ no llama a `create_return` y cuelga sola |
| Pedir una persona | — | ✔ aviso único y llamada a `transfer_call_tool`; ver límites |

Los datos son los del seed (`db/seed.sql`). Sus fechas son fijas desde el día que se carga, así que los casos
caducan con el tiempo: conviene recargar el seed antes de repetir las pruebas.

## 7. Límites conocidos

- **La transferencia solo se ha verificado como llamada a la herramienta**, desde el navegador. Que conecte con una
  persona real requiere una llamada telefónica, que no se ha probado. En el registro de Vapi la llamada web acaba con
  "Call ended due to transfer failure": se atribuye a que es una llamada desde el navegador, pero la causa no se ha
  comprobado (también podría deberse al número de destino).
- Con `gpt-4.1-mini`, el agente toma al pie de la letra las instrucciones del prompt. Si se vuelven a ver errores al
  elegir herramientas, el primer cambio a probar es un modelo mayor.
- Cada pedido admite una sola devolución: para repetir un registro hay que recargar el seed o usar otro pedido.

## 8. Cómo reconstruirlo

1. Crear las cuatro herramientas con la sección 3 (las dos de API Request con la URL y la clave reales).
2. Crear el asistente con los ajustes de la sección 2 y pegar el prompt de la sección 4.
3. **Asociar las cuatro herramientas** al asistente y publicar.
4. Repetir las pruebas de la sección 6.
