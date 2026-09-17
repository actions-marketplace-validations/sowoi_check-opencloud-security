"""The Spanish translation of :mod:`webapp.locales.en`."""

from __future__ import annotations

MESSAGES: dict[str, str] = {
    # ---------------------------------------------------------------- site
    # ------------------------------------------------ el área de operación
    "admin.title": "Área de operación",
    "admin.description": "Estado del servicio, datos de referencia y el registro de auditoría.",
    "admin.kicker": "Operación",
    "admin.tabs.aria": "Área de operación",
    "admin.tabs.overview": "Resumen",
    "admin.tabs.configuration": "Configuración",
    "admin.tabs.rules": "Reglas",
    "admin.config.title": "Configuración",
    "admin.config.lede": "Todas las variables COS_WEB_* que lee este servicio y sus valores efectivos actuales.",
    "admin.config.scope": "Estos son los ajustes efectivos de este proceso web al iniciarse. OpenCloud y el proceso de análisis tienen su propia configuración. Para las credenciales solo se indica si están definidas.",
    "admin.config.source.environment": "Definida",
    "admin.config.source.default": "Predeterminado",
    "admin.config.secret.set": "Definida (valor oculto)",
    "admin.config.unset": "No definida",
    "admin.config.default": "Valor predeterminado documentado:",
    "admin.config.unknown.kicker": "Revise la ortografía",
    "admin.config.unknown.heading": "Variables que este servicio no lee",
    "admin.config.unknown.lede": "Estos nombres llevan el prefijo COS_WEB_ pero no corresponden a ningún ajuste, así que no cambian nada. Una errata aquí deja en vigor el valor predeterminado. No se muestran los valores.",
    "admin.config.group.storage": "Almacenamiento y workers",
    "admin.config.group.scanning": "Cómo se ejecuta un escaneo",
    "admin.config.group.targets": "Qué se puede escanear",
    "admin.config.group.limits": "Límites de frecuencia y protección contra abusos",
    "admin.config.group.approval": "Aprobación de objetivos",
    "admin.config.group.network": "Dirección pública, proxy e indexación",
    "admin.config.group.reference": "Datos de versiones y avisos",
    "admin.config.group.interfaces": "Documentación de la API y endpoint para agentes",
    "admin.config.group.mcp_auth": "Inicio de sesión en el endpoint para agentes",
    "admin.config.group.admin": "Área del operador",
    "admin.config.group.audit": "Registro de auditoría",
    "admin.config.group.protection": "Borrado, firmas y cifrado",
    "admin.config.group.frontend": "Frontend",
    "admin.rules.title": "Reglas en vigor",
    "admin.rules.lede": "Cómo se decide una calificación y qué reglas aplica este despliegue a las solicitudes, con los valores vigentes.",
    "admin.rules.scope": "Leído de la configuración con la que arrancó este proceso y de las constantes que usa el código que las aplica, así que una regla listada aquí es una que el servicio aplica ahora mismo. Nada en esta página nombra un objetivo ni a un visitante.",
    "admin.rules.on": "Aplicada",
    "admin.rules.off": "Desactivada",
    "admin.rules.variables": "Definida por",
    "admin.rules.rating.kicker": "Notas",
    "admin.rules.rating.heading": "Cómo se califica una instancia",
    "admin.rules.rating.lede": "La calificación es del propio escáner; este servicio solo la muestra. Estas son las reglas que aplica a cada análisis aquí.",
    "admin.rules.rating.scale": "La escala",
    "admin.rules.rating.caps": "Lo que una comprobación fallida puede hacer con la nota",
    "admin.rules.rating.version.title": "La versión fija la nota de partida",
    "admin.rules.rating.version.body": "El estado de soporte de la línea de versiones y cada aviso publicado que afecta a la versión deciden dónde empieza una nota. Las comprobaciones fallidas solo pueden limitarla.",
    "admin.rules.rating.overrides.title": "Fin de soporte y canal de versiones",
    "admin.rules.rating.shared.title": "Un techo por gravedad",
    "admin.rules.rating.extra.title": "Las comprobaciones adicionales cuentan para la nota",
    "admin.rules.rating.extra.body": "La seguridad del transporte, las cabeceras y el resto de comprobaciones adicionales limitan la nota como las de refuerzo, no solo aparecen en el informe.",
    "admin.rules.rating.waivers.title": "Exenciones que puede elegir un visitante",
    "admin.rules.rating.waivers.body": "{count} comprobaciones de refuerzo pueden eximirse en el formulario. Una comprobación eximida deja de limitar la nota y sigue en el informe, marcada; el fin de soporte no puede eximirse.",
    "admin.rules.rating.track.title": "Canal de versiones",
    "admin.rules.rating.track.body": "Sin elegir en el formulario, el canal es {track}. El canal cambia cómo se califica una versión, nunca con qué intensidad se sondea la instancia.",
    "admin.rules.rating.reference.title": "Datos de referencia para calificar",
    "admin.rules.rating.reference.body": "{advisories} avisos en la base de datos; calendario de versiones con fecha {schedule}.",
    "admin.rules.rating.more": "La <a href=\"/grades\">página de notas</a> explica cada nota a los visitantes en los mismos términos.",
    "admin.rules.group.submissions": "Límites de envío",
    "admin.rules.group.submissions.lede": "Con qué frecuencia puede preguntar un cliente, y cómo se comporta el servicio con carga.",
    "admin.rules.group.probe": "Bloqueo por sondeo",
    "admin.rules.group.probe.lede": "Límites para solicitudes repetidas a destinos que no se pueden analizar.",
    "admin.rules.group.targets": "Qué se puede analizar",
    "admin.rules.group.targets.lede": "Se comprueba antes de conectar nada, y de nuevo en cada redirección.",
    "admin.rules.group.scanner": "Con qué intensidad se sondea un host",
    "admin.rules.group.scanner.lede": "Los ajustes con los que se ejecuta cada análisis de este despliegue. Ninguna solicitud puede modificarlos.",
    "admin.rules.group.operator": "Credenciales y acciones del operador",
    "admin.rules.group.operator.lede": "Límites para las pocas llamadas que necesitan una credencial o pulsan un botón.",
    "admin.rules.rule.client_limit.title": "Límite por cliente",
    "admin.rules.rule.client_limit.body": "Como máximo {limit} envíos por cliente cada {window}. Una dirección IPv4 es un cliente; un cliente IPv6 es su /{ipv6}.",
    "admin.rules.rule.daily_cap.title": "Límite diario",
    "admin.rules.rule.daily_cap.body": "Como máximo {limit} envíos por cliente cada {window}, además del límite por cliente.",
    "admin.rules.rule.target_cooldown.title": "Espera por objetivo",
    "admin.rules.rule.target_cooldown.body": "La misma instancia puede analizarse una vez cada {cooldown}, pregunte quien pregunte.",
    "admin.rules.rule.batch.title": "Tamaño del lote",
    "admin.rules.rule.batch.body": "Un lote lleva como máximo {limit} objetivos, y cada uno cuenta contra todos los límites.",
    "admin.rules.rule.queue.title": "La sobrecarga hace cola",
    "admin.rules.rule.queue.body": "Se ejecutan {workers} análisis a la vez; los demás envíos esperan en orden y nunca se rechazan por carga.",
    "admin.rules.rule.agent_wait.title": "Límite de reintentos automáticos",
    "admin.rules.rule.agent_wait.body": "MCP y los flujos esperan por sí mismos un Retry-After de hasta {wait}, con un máximo de {attempts} intentos. Si la espera es mayor, devuelven la respuesta a quien llama.",
    "admin.rules.rule.probe_block.title": "Bloqueo tras avisos repetidos",
    "admin.rules.rule.probe_block.body": "{limit} avisos en {window} bloquean la red del cliente durante {block}.",
    "admin.rules.rule.probe_escalation.title": "Los bloqueos repetidos se alargan",
    "admin.rules.rule.probe_escalation.body": "Una red bloqueada de nuevo dentro de {repeat} tras su último bloqueo espera {factor} veces más cada vez: {steps}.",
    "admin.rules.rule.probe_network.title": "El bloqueo cubre una red",
    "admin.rules.rule.probe_network.body": "Un bloqueo se aplica a la /{ipv4} IPv4 y la /{ipv6} IPv6 del cliente, para que la siguiente dirección no pueda esquivarlo.",
    "admin.rules.rule.strike_scans.title": "Un análisis que no encuentra OpenCloud es un aviso",
    "admin.rules.rule.strike_scans.body": "status.php no respondió, no devolvió JSON, nombró otro producto, o el análisis agotó el tiempo. El mismo host de nuevo es otro aviso; un análisis terminado nunca lo es.",
    "admin.rules.rule.strike_refusals.title": "Un objetivo rechazado es un aviso",
    "admin.rules.rule.strike_refusals.body": "Cuenta un envío rechazado por aquello a lo que apunta; una errata o un nombre que no resuelve no cuenta:",
    "admin.rules.refusal.blocked": "una dirección que este despliegue excluye",
    "admin.rules.refusal.internal": "un nombre local o interno",
    "admin.rules.refusal.not_approved": "una instancia que el modo de aprobación no ha aprobado",
    "admin.rules.refusal.private": "una dirección privada, de loopback o de enlace local",
    "admin.rules.refusal.unstable": "un nombre cuyas consultas no coinciden",
    "admin.rules.refusal.wildcard_dns": "un nombre DNS comodín o de rebinding",
    "admin.rules.rule.private_addresses.title": "Solo direcciones públicas",
    "admin.rules.rule.private_addresses.body": "Cada dirección a la que resuelve un nombre debe ser pública; una respuesta privada rechaza el objetivo. Además de los rangos privados, también se rechazan estos:",
    "admin.rules.rule.internal_names.title": "Nombres locales y endpoints de metadatos",
    "admin.rules.rule.internal_names.body": "Rechazados por nombre además de por dirección:",
    "admin.rules.rule.wildcard_dns.title": "Nombres DNS comodín y de rebinding",
    "admin.rules.rule.wildcard_dns.body": "Los nombres bajo estos servicios apuntan donde diga su escritura. La dirección de detrás puede analizarse escribiéndola directamente:",
    "admin.rules.rule.dns_consistency.title": "Un nombre debe resolver igual dos veces",
    "admin.rules.rule.dns_consistency.body": "Un nombre enviado se consulta dos veces y se rechaza si las respuestas no comparten ninguna dirección; se comprueban todas las de ambas.",
    "admin.rules.rule.redirects.title": "Se comprueba cada redirección",
    "admin.rules.rule.redirects.body": "Una redirección se resuelve y comprueba igual que el objetivo enviado antes de seguirla. El análisis solo se conecta a direcciones que han superado la comprobación.",
    "admin.rules.rule.exclusions.title": "Exclusiones",
    "admin.rules.rule.exclusions.body": "{count} entradas excluidas procedentes del entorno y de la pestaña de resumen.",
    "admin.rules.rule.allowed_hosts.title": "Hosts exentos de la protección",
    "admin.rules.rule.allowed_hosts.body": "Estos nombres se saltan las reglas de dirección pública. Las exclusiones siguen aplicándose:",
    "admin.rules.rule.approval.title": "Modo de aprobación",
    "admin.rules.rule.approval.body": "Solo se analizan instancias aprobadas; lo demás se rechaza con 403. {count} entradas listadas; registro DNS de aprobación: {record}.",
    "admin.rules.rule.stop_when_not_opencloud.title": "Una petición para un host que no es OpenCloud",
    "admin.rules.rule.stop_when_not_opencloud.body": "Una respuesta de status.php que no es OpenCloud termina el análisis, sin reintentar por HTTPS sin verificar ni por HTTP simple.",
    "admin.rules.rule.single_address.title": "Una dirección por análisis",
    "admin.rules.rule.single_address.body": "Un nombre con varias direcciones se analiza en una de ellas, nunca en cada nodo de un grupo.",
    "admin.rules.rule.no_port_scan.title": "Sin puertos adicionales",
    "admin.rules.rule.no_port_scan.body": "Solo se contacta el puerto enviado; los puertos de depuración no se sondean.",
    "admin.rules.rule.load.title": "Carga por análisis",
    "admin.rules.rule.load.body": "Como máximo {concurrency} peticiones simultáneas, cada una con {timeout}; un análisis completo se detiene tras {job}.",
    "admin.rules.rule.purge_attempts.title": "Intentos con la credencial de borrado",
    "admin.rules.rule.purge_attempts.body": "{limit} credenciales erróneas por cliente en {window}, después se rechaza hasta que termina la ventana. Las correctas nunca cuentan.",
    "admin.rules.rule.admin_refresh.title": "Botones de actualización",
    "admin.rules.rule.admin_refresh.body": "Cada actualización de datos de referencia puede pulsarse una vez cada {cooldown}.",
    "admin.docs.kicker": "Documentación de operación",
    "admin.docs.source": "Desde <code>{file}</code> en el repositorio, en inglés.",
    "admin.band": "Área de operación - sesión iniciada como {user}",
    "admin.band.signout": "Cerrar sesión",
    "admin.lede": "Consulte el estado del servicio y los datos de referencia, o ejecute manualmente las actualizaciones diarias del proceso de trabajo.",
    "admin.noscript": (
        "Los valores de arriba los rellena JavaScript. Sin él, recarga la "
        "página para ver los actuales; los dos botones siguen funcionando."
    ),
    "admin.state.kicker": "Ahora",
    "admin.state.heading": "Estado del servicio",
    "admin.state.lede": "Recuentos actuales y límites configurados. Aquí no se puede acceder a los detalles de análisis individuales ni a las direcciones de los clientes.",
    "admin.state.worker": "Worker",
    "admin.state.worker.up": "En marcha",
    "admin.state.worker.down": "No responde",
    "admin.state.worker.unknown": "No se puede saber",
    "admin.state.store.down": (
        "El almacén no responde: no se puede leer la señal de vida"
    ),
    "admin.state.queue": "{depth} en cola, {workers} workers",
    "admin.state.ratelimit": "Límite de peticiones",
    "admin.state.ratelimit.value": "{limit} por {window}s",
    "admin.state.cooldown.value": "{seconds}s por destino",
    "admin.state.guard": "Protección contra abusos",
    "admin.state.guard.value": "{active} redes bloqueadas",
    "admin.state.guard.week": "últimos 7 días: {blocks} bloqueos, {strikes} avisos, {daily} límites diarios alcanzados",
    "admin.state.guard.off": "Bloqueo por sondeo desactivado",
    "admin.state.schedule": "Calendario de versiones",
    "admin.state.advisories": "Avisos",
    "admin.state.checked": "comprobado {when}",
    "admin.state.checked.failed": (
        "comprobado {when}: el último intento no se pudo descargar"
    ),
    "admin.state.checked.rejected": (
        "comprobado {when}: las comprobaciones rechazaron el último intento"
    ),
    "admin.state.refresh.off": "la actualización diaria está desactivada",
    "admin.state.ago.minutes": "hace {minutes} min",
    "admin.state.ago.hours": "hace {hours} h",
    "admin.state.ago.days": "hace {days} d",
    "admin.state.never": "nunca",
    "admin.state.unknown": "desconocido",
    "admin.state.age.seconds": "Leído hace {seconds}s",
    "admin.state.age.minutes": "Leído hace {minutes}m",
    "admin.state.age.waiting": "Esperando la primera lectura",
    "admin.state.stale": "El servicio no ha respondido recientemente. Los valores mostrados son los últimos disponibles y pueden estar desactualizados.",
    "admin.state.refresh": "Leer de nuevo",
    "admin.state.copy": "Copiar diagnóstico",
    "admin.state.copy.done": "Copiado",
    "admin.state.copy.failed": "No se ha podido copiar",
    "admin.surfaces.kicker": "Exposición",
    "admin.surfaces.heading": "Qué ofrece esta instalación",
    "admin.surfaces.lede": (
        "Los ajustes con los que arrancó este proceso, los mismos que indica "
        "el documento de diagnóstico. Ninguno cambia sin reiniciar, así que "
        "ninguno se consulta periódicamente."
    ),
    "admin.surfaces.on": "Activado",
    "admin.surfaces.off": "Desactivado",
    "admin.surfaces.mcp": "Punto de acceso para agentes en /mcp",
    "admin.surfaces.mcp.guarded": (
        "Se exige un token del emisor configurado."
    ),
    "admin.surfaces.mcp.open": (
        "No se exige ningún token: cualquier agente que llegue hasta él puede "
        "ocupar los workers de este servicio."
    ),
    "admin.surfaces.docs": "Páginas de API navegables en /docs",
    "admin.surfaces.docs.contract": (
        "Desactivarlas oculta las páginas, no el contrato: /openapi.json, "
        "/arazzo.json y /.well-known/ai.json siguen siendo públicos."
    ),
    "admin.surfaces.indexed": "Localizable por los buscadores",
    "admin.surfaces.private": "Análisis de direcciones de red privadas",
    "admin.surfaces.private.found": (
        "Permitido en una instalación que pide ser indexada: quien encuentre "
        "este servicio puede apuntarlo a la red en la que está."
    ),
    "admin.surfaces.private.estate": (
        "Permitido, que es justo para lo que sirve una instalación que "
        "analiza su propia red."
    ),
    "admin.surfaces.encrypt": "Resultados cifrados en reposo",
    "admin.surfaces.audit": "Registro de auditoría",
    "admin.surfaces.audit.file": (
        "Se escribe en un archivo que sobrevive al contenedor."
    ),
    "admin.surfaces.audit.memory": (
        "Un anillo de {count} registros en la memoria de este proceso, y nada "
        "en disco."
    ),
    "admin.surfaces.targets": "Direcciones analizadas registradas en claro",
    "admin.exclusions.kicker": "Exclusiones",
    "admin.exclusions.heading": "Direcciones que este servicio no analizará",
    "admin.exclusions.lede": (
        "Una entrada surte efecto desde la siguiente petición, en todos los "
        "procesos y sin reiniciar - y un análisis que ya esperaba en la cola "
        "se rechaza en lugar de ejecutarse. Nada de aquí hace que este "
        "servicio analice algo: la lista solo rechaza."
    ),
    "admin.exclusions.add.label": "Nombre de host, dominio .sufijo, dirección o rango CIDR",
    "admin.exclusions.add.placeholder": "opencloud.example.com",
    "admin.exclusions.add.action": "Excluir",
    "admin.exclusions.add.hint": (
        "Un dominio escrito con un punto inicial excluye también todo lo que "
        "haya bajo él. Un rango se comprueba contra todas las direcciones a "
        "las que resuelve un nombre de host."
    ),
    "admin.exclusions.remove": "Retirar",
    "admin.exclusions.empty": "En esta instalación no hay nada excluido.",
    "admin.exclusions.source.configured": "Desde el entorno",
    "admin.exclusions.updated": "Modificado aquí por última vez el {when}.",
    "admin.exclusions.durability": (
        "Las entradas añadidas aquí viven en Redis, que esta instalación "
        "puede vaciar. Las que deban perdurar van en COS_WEB_BLOCKED_TARGETS, "
        "donde no pueden retirarse desde esta página."
    ),
    "admin.exclusions.unreadable": (
        "El almacén no respondió, así que las exclusiones no pueden leerse "
        "ni cambiarse ahora mismo. Siguen vigentes: un análisis que no puede "
        "comprobarlas se rechaza, no se ejecuta."
    ),
    "admin.blocklist.error.shape": (
        "Eso no es una entrada. Indique un nombre de host, un dominio que "
        "empiece por punto, una dirección o un rango CIDR."
    ),
    "admin.blocklist.error.configured": (
        "Esa entrada viene de COS_WEB_BLOCKED_TARGETS. Quítela allí y "
        "reinicie, para que la instalación y esta lista no se contradigan."
    ),
    "admin.blocklist.error.full": (
        "Esta lista está llena. Pase las entradas permanentes a "
        "COS_WEB_BLOCKED_TARGETS."
    ),
    "admin.blocklist.error.long": (
        "Esa entrada es más larga de lo que puede ser un nombre de host, así "
        "que nada de lo que pretenda designar llegaría a este servicio."
    ),
    "admin.outcome.excluded": "Excluida. Se rechaza desde la siguiente petición.",
    "admin.outcome.withdrawn": "Retirada. Puede volver a analizarse.",
    "admin.actions.kicker": "Datos de referencia",
    "admin.actions.heading": "Actualizar los datos de referencia",
    "admin.actions.lede": (
        "Las mismas dos actualizaciones que el worker ejecuta a diario, con las "
        "mismas reglas: un calendario al que le falta una línea de versiones se "
        "rechaza, una base de avisos solo puede añadir entradas y una descarga "
        "fallida no cambia nada."
    ),
    "admin.actions.schedule": "Sincronizar el calendario",
    "admin.actions.schedule.hint": "Vuelve a leer la página de ciclo de vida publicada.",
    "admin.actions.advisories": "Buscar avisos",
    "admin.actions.advisories.hint": "Pregunta al feed de avisos por entradas nuevas.",
    "admin.outcome.updated": "Actualizado. El documento nuevo está en uso.",
    "admin.outcome.unchanged": "Ya estaba al día - nada ha cambiado.",
    "admin.outcome.rejected": (
        "Rechazado: los datos descargados no han pasado las comprobaciones, así que "
        "siguen en uso los datos anteriores."
    ),
    "admin.outcome.failed": "No se ha podido descargar. Nada ha cambiado.",
    "admin.outcome.disabled": "Esa actualización está desactivada en la configuración de esta instalación.",
    "admin.outcome.cooldown": "Acaba de ejecutarse. Inténtalo en {seconds}s.",
    "admin.probe.action": "Probar las fuentes",
    "admin.probe.hint": (
        "Lee ambas fuentes e informa de qué haría con ellas una actualización. "
        "No se guarda nada."
    ),
    "admin.probe.schedule": "Calendario de versiones: {answer}",
    "admin.probe.advisories": "Avisos: {answer}",
    "admin.probe.usable": "leído, y una actualización lo aceptaría",
    "admin.probe.rejected": "leído, pero las comprobaciones lo rechazarían",
    "admin.probe.unreadable": "no se ha podido leer - inalcanzable, o ya no tiene la forma esperada",
    "admin.probe.disabled": "sin comprobar - esa actualización está desactivada",
    "admin.search.kicker": "Índice de búsqueda",
    "admin.search.heading": "Sigue siendo válido el índice publicado",
    "admin.search.lede": (
        "El índice se construye al publicar una versión y se entrega en solo "
        "lectura, así que esta vista informa en lugar de reconstruir. Compara "
        "las páginas, los idiomas y la versión para la que se generó - no el "
        "cuerpo del texto, que solo el generador puede extraer."
    ),
    "admin.search.fresh": "Al día",
    "admin.search.stale": "Desactualizado",
    "admin.search.unknown": "No se puede saber",
    "admin.search.detail.ok": "Todas las páginas e idiomas están indexados para esta versión.",
    "admin.search.detail.release": "Generado para {built}, en ejecución {running}.",
    "admin.search.detail.missing": "Sin indexar: {list}.",
    "admin.search.detail.extra": (
        "Indexado pero ya no se sirve: {list}."
    ),
    "admin.search.detail.unstamped": (
        "El índice no dice para qué versión se generó, así que solo se han "
        "podido comparar sus páginas y sus idiomas."
    ),
    "admin.search.detail.changed": "{count} títulos o resúmenes han cambiado desde que se generó.",
    "admin.search.detail.unreadable": "No se ha podido leer el índice.",
    "admin.search.remedy": (
        "Una versión publicada siempre incluye un índice generado para ella, "
        "así que esta compilación no es una versión tal como se publicó - "
        "normalmente una imagen o un paquete construido desde un checkout "
        "entre versiones. Despliegue una versión publicada, o regenere el "
        "índice en ese checkout y vuelva a construir lo que despliega:"
    ),
    "admin.search.remedy.commit": (
        "No hace falta confirmar nada a mano: cada pull request a main "
        "regenera el índice y lo confirma en su rama."
    ),
    "admin.search.fix": (
        "Cada pull request a main y el flujo de publicación regeneran el "
        "índice y lo confirman. Aquí no hay nada que pulsar."
    ),
    "admin.audit.kicker": "Auditoría",
    "admin.audit.heading": "Registro de auditoría",
    "admin.audit.lede": "Solicitudes, rechazos y límites alcanzados en tiempo real. La conexión se abre al activar la vista en directo.",
    "admin.audit.privacy": (
        "Una dirección de cliente es un HMAC truncado bajo una sal que guarda "
        "este proceso, y nada permite volver de ahí a una dirección. Esta vista "
        "no puede mostrar más de lo que el registro ya decidió anotar."
    ),
    "admin.audit.replicas": (
        "Esta instalación no mantiene un fichero de auditoría, así que estos "
        "registros vienen de la memoria del único proceso que ha respondido - "
        "con más de una réplica, eso es una parte del registro y no todo."
    ),
    "admin.audit.follow": "Ver en directo",
    "admin.audit.stop": "Detener",
    "admin.audit.clear": "Vaciar",
    "admin.audit.empty": "Todavía nada.",
    "admin.audit.closed": (
        "La conexión ha alcanzado su límite de {minutes} minutos y el servicio "
        "la ha cerrado. Hasta ahí no se ha perdido nada; «Ver en directo» abre otra."
    ),
    "admin.audit.disabled": (
        "Esta instalación no mantiene un registro de auditoría, así que no hay "
        "nada que seguir. COS_WEB_AUDIT_LOG lo activa."
    ),
    "admin.audit.state.off": "Sin seguimiento en directo",
    "admin.audit.state.live": "En directo",
    "admin.audit.state.reconnecting": "Reconectando",
    "admin.audit.state.unsupported": "No compatible con este navegador",
    "admin.audit.state.closed": "Cerrada por el servicio",
    "admin.audit.state.disabled": "No se mantiene",
    "site.og_image_alt": (
        "OpenCloud Security Scan: comprueba una instancia en busca de "
        "vulnerabilidades conocidas, medidas de refuerzo faltantes y "
        "cabeceras de seguridad débiles"
    ),
    # ------------------------------------------------------- header chrome
    "chrome.skip_to_content": "Saltar al contenido",
    "chrome.brand": "Análisis de seguridad para OpenCloud",
    "chrome.menu": "Menú",
    "chrome.nav.primary": "Principal",
    "chrome.nav.secondary": "Secundaria",
    "chrome.search.label": "Buscar en la documentación",
    "chrome.search.placeholder": "Buscar",
    "chrome.theme.toggle": "Cambiar el tema de color",
    "chrome.back_to_top": "Volver arriba",
    "nav.new_scan": "Nuevo análisis",
    "nav.how_it_works": "Cómo funciona",
    "nav.grades": "Calificaciones",
    "nav.catalogue": "Catálogo",
    "nav.docs": "Documentación",
    "nav.search": "Buscar",
    "nav.compare": "Comparar",
    "nav.api": "API",
    "nav.privacy": "Privacidad",
    "nav.about": "Acerca de",
    # --------------------------------------------------- language switcher
    "lang.region": "Idioma",
    "lang.label": "Idioma de la página",
    "lang.apply": "Cambiar idioma",
    "lang.note": "El análisis en sí no cambia; solo esta página se traduce.",
    # ------------------------------------------------------------- footer
    "footer.note.title": "Acerca de este servicio",
    "footer.note.body": "Este servidor analiza la dirección que indique. Los resultados están disponibles durante {minutes} minutos y después caducan. El servicio utiliza <code>check-opencloud-security</code>, sin necesidad de una cuenta y sin rastreadores ni herramientas de analítica.",
    "footer.note.run_yourself": "Ejecutar localmente",
    "footer.version.title": "La versión del escáner que produjo estos resultados",
    "footer.version.label": "Backend v{version}",
    "footer.legal.scope": "<strong>Esta comprobación no es exhaustiva y una buena nota no es un certificado.</strong> Lee la versión declarada, los avisos de seguridad correspondientes, TLS, las cabeceras y la configuración pública, incluidas las cuentas de demostración documentadas. Una buena nota significa que nada de eso falló, no que la instancia sea segura. No evalúa los archivos privados, el sistema operativo, las copias de seguridad, los permisos de las cuentas ni la red. Utilice el informe como complemento de sus otras revisiones; nunca es una auditoría de seguridad ni una prueba de penetración.",
    "footer.legal.trademark": (
        "Este es un proyecto comunitario independiente. No está afiliado a "
        "OpenCloud GmbH y la empresa ni lo recomienda ni lo respalda. "
        "&ldquo;OpenCloud&rdquo;, el logotipo de OpenCloud y todas las marcas "
        "asociadas son propiedad de sus respectivos titulares y se usan aquí "
        "únicamente para indicar qué software comprueba esta herramienta."
    ),
    # --------------------------------------------------- the contents list
    "toc.heading": "En esta página",
    "toc.aria": "En esta página",
    # --------------------------------------------------------- cross-links
    "pagenav.kicker": "Sigue leyendo",
    "pagenav.aria": "Más sobre este servicio",
    "pagenav.how.title": "Cómo funciona el análisis",
    "pagenav.how.blurb": (
        "Qué se comprueba, y los cuatro pasos entre el botón y la calificación."
    ),
    "pagenav.grades.title": "Qué significan las calificaciones",
    "pagenav.grades.blurb": (
        "Cada nivel de A+ a F, qué frena una calificación y cómo mejorarla."
    ),
    "pagenav.catalogue.title": "Qué comprueba el escáner",
    "pagenav.catalogue.blurb": (
        "Cada indicador de refuerzo, cabecera y comprobación TLS, y cada "
        "vulnerabilidad conocida - independiente de un análisis concreto."
    ),
    "pagenav.docs.title": "Documentación de la CLI",
    "pagenav.docs.blurb": "Instala, configura y automatiza el escáner desde una terminal.",
    "pagenav.api.title": "Analizar desde un script o un agente",
    "pagenav.api.blurb": (
        "La API JSON, los límites de uso razonable, el esquema OpenAPI y el "
        "endpoint MCP."
    ),
    "pagenav.privacy.title": "Qué conserva este servidor",
    "pagenav.privacy.blurb": (
        "En memoria, durante {minutes} minutos, y qué queda fuera del registro."
    ),
    "pagenav.about.title": "Acerca de OpenCloud",
    "pagenav.about.blurb": (
        "La plataforma que esto comprueba, y por qué este proyecto es "
        "independiente de ella."
    ),
    "pagenav.cta.title": "Analizar una instancia",
    "pagenav.cta.blurb": "Vuelve al formulario. Tarda unos segundos, sin registro.",
    # ---------------------------------------------------------------- 404
    "notfound.title": "Aquí no hay nada",
    "notfound.description": (
        "La dirección no existe, o el análisis al que apuntaba ya ha expirado."
    ),
    "notfound.kicker": "No encontrado",
    "notfound.lede": "Esta página no existe o el resultado ha caducado. Los resultados están disponibles durante {minutes} minutos. Inicie un nuevo análisis para obtener un informe actualizado.",
    "notfound.action": "Ejecutar un nuevo análisis",
    # ------------------------------------------------------- landing page
    "index.title": "Analizar una instancia de OpenCloud",
    "index.description": "Compruebe las vulnerabilidades conocidas, las medidas de protección que faltan, las cabeceras de seguridad y las actualizaciones disponibles de una instancia de OpenCloud. Gratis y sin registro.",
    "index.eyebrow": "Independiente &middot; recursos alojados en este servidor &middot; resultados temporales",
    "index.headline": "¿Qué seguridad ofrece su <em class=\"swash\">instancia de OpenCloud</em>?",
    "index.lede": "Introduzca la dirección de una instancia de OpenCloud que tenga permiso para comprobar. El escáner revisa los ajustes públicos, las cabeceras HTTP y la versión del software, y asigna una nota de <strong>A+</strong> a <strong>F</strong>.",
    "index.form.kicker": "Solicitud de análisis",
    "index.form.hint": "Unos segundos &middot; sin registro",
    "index.error.self_host": "Disculpe la espera. Estos límites permiten que el servicio siga disponible para todos. También puede ejecutar el escáner de código abierto en su equipo tantas veces como necesite:",
    "index.field.label": "Dirección de la instancia",
    "index.field.title": (
        "La dirección base de la instancia: un nombre de host, un puerto "
        "opcional y una subcarpeta simple opcional. Sin consultas, "
        "fragmentos, parámetros, escapes ni recorridos de ruta."
    ),
    "index.field.hint": "Basta con el nombre de host; se utiliza <code>https://</code> si no se indica un esquema. Se admite una subcarpeta sencilla como <code>/opencloud</code>. No se aceptan consultas, fragmentos, parámetros ni cambios de directorio. Analice solo instancias públicas para las que tenga autorización.",
    "index.field.invalid": (
        "No es una dirección válida: un nombre de host, un puerto opcional y "
        "una subcarpeta simple - sin consultas, fragmentos ni parámetros."
    ),
    "index.submit": "Iniciar análisis",
    "index.submit.busy": "Iniciando análisis…",
    "index.track.label": "Canal de publicación",
    "index.track.hint": "Permite comprobar si la versión sigue teniendo soporte y recomendar una actualización adecuada.",
    "index.format.label": "Mostrar",
    "index.format.dashboard": "Un panel",
    "index.format.json": "El JSON en bruto",
    "index.format.hint": "Ambos provienen del mismo análisis.",
    "index.waivers.summary": "Ignorar comprobaciones específicas (opcional)",
    "index.waivers.selected": "Ignorar comprobaciones específicas ({count} seleccionadas)",
    "index.remember.summary": "Ajustes de su último análisis en este navegador: {track} · {format} · {waivers}.",
    "index.remember.waivers.none": "ninguna comprobación exceptuada",
    "index.remember.waivers.one": "1 comprobación exceptuada",
    "index.remember.waivers.many": "{count} comprobaciones exceptuadas",
    "index.remember.apply": "Volver a usarlos",
    "index.remember.forget": "Olvidarlos",
    "index.waivers.hint": "Un hallazgo excluido sigue visible en el informe, pero no reduce la nota. Las exclusiones solo se aplican a comprobaciones fallidas.",
    "index.waivers.search.label": "Filtrar comprobaciones",
    "index.waivers.search.placeholder": "Buscar por nombre...",
    "index.waivers.search.empty": "Ninguna comprobación coincide con la búsqueda.",
    "index.assurance.aria": "Cómo trata este servicio los datos",
    "index.assurance.airgapped.title": "Sin recursos externos",
    "index.assurance.airgapped.body": "Las fuentes, los scripts y las imágenes se sirven desde aquí, sin CDN ni herramientas de analítica.",
    "index.assurance.nostore.title": "Almacenamiento temporal",
    "index.assurance.nostore.body": (
        "El resultado vive en memoria y se elimina en cuanto expira."
    ),
    "index.assurance.noaccount.title": "No se necesita registro",
    "index.assurance.noaccount.body": "Inicie un análisis sin crear una cuenta ni facilitar una dirección de correo.",
    "index.assurance.ephemeral.title": "Enlaces con caducidad",
    "index.assurance.ephemeral.body": (
        "El enlace deja de funcionar {minutes} minutos después del análisis."
    ),
    # -------------------------------------------- release tracks and waivers
    "track.auto.label": "Detectar automáticamente",
    "track.auto.description": (
        "Deducir el canal a partir de la versión que reporta la instancia."
    ),
    "track.rolling.label": "Rolling",
    "track.rolling.description": "Una nueva versión aproximadamente cada tres semanas.",
    "track.production.label": "Production",
    "track.production.description": (
        "Compatible durante unos seis meses. La opción habitual."
    ),
    "track.lts.label": "LTS",
    "track.lts.description": "Compatible durante dos años.",
    "waivers.group.hardening": "Refuerzo",
    "waivers.group.headers": "Cabeceras",
    "waivers.group.checks": "Comprobaciones",
    # ------------------------------------------------------------ severity
    "severity.critical": "crítica",
    "severity.high": "alta",
    "severity.medium": "media",
    "severity.low": "baja",
    # ------------------------------------------------------------ category
    "category.transport": "Transporte y TLS",
    "category.cookies": "Cookies",
    "category.headers": "Cabeceras de seguridad",
    "category.authentication": "Autenticación y cuentas",
    "category.sharing": "Uso compartido y enlaces",
    "category.exposure": "Exposición de red",
    "category.embedding": "Incrustación",
    "category.lifecycle": "Versión y ciclo de vida",
    "category.proxy": "Proveedor de identidad y proxy",
    # --------------------------------------------------------- grade scale
    "grade.5.headline": "No se ha encontrado nada",
    "grade.5.meaning": (
        "La versión está actualizada para su canal, ningún aviso de seguridad "
        "coincide con ella, y todas las comprobaciones que el análisis pudo "
        "ejecutar se superaron."
    ),
    "grade.5.improve": "Mantenga la instancia actualizada en su canal y repita el análisis después de cambiar el proxy inverso o la configuración de acceso.",
    "grade.4.headline": "Hay una actualización pendiente",
    "grade.4.meaning": (
        "Existe una versión de parche más reciente en la misma línea de "
        "versiones. No se sabe que la instalada tenga ningún problema; "
        "simplemente no es la más reciente."
    ),
    "grade.4.improve": "Instale la actualización recomendada para su rama de versiones.",
    "grade.3.headline": "Una línea de versiones por detrás",
    "grade.3.meaning": (
        "La instancia ejecuta una línea más antigua que la actual para su "
        "canal. Puede que todavía tenga soporte, pero ya no es donde llegan "
        "primero las correcciones."
    ),
    "grade.3.improve": "Actualice a la rama recomendada dentro de su canal. El informe indica la versión adecuada.",
    "grade.2.headline": "Hay avisos de seguridad que coinciden con esta versión",
    "grade.2.meaning": (
        "La versión instalada aparece en la base de datos de avisos de "
        "seguridad. Ninguno de los avisos coincidentes está calificado como "
        "crítico o alto, que es la única razón por la que esto no es más bajo."
    ),
    "grade.2.improve": "Instale la versión corregida para su rama. Un mismo aviso de seguridad puede tener correcciones distintas según la rama.",
    "grade.1.headline": "Coincide un aviso crítico o alto",
    "grade.1.meaning": "Al menos una vulnerabilidad conocida de la versión instalada tiene una gravedad alta o crítica.",
    "grade.1.improve": "Instale la versión corregida indicada en el informe y siga las instrucciones del aviso de seguridad.",
    "grade.0.headline": "Sin soporte",
    "grade.0.meaning": "Esta rama ya no recibe correcciones de seguridad. Obtiene una F, con independencia de los demás hallazgos o exclusiones.",
    "grade.0.improve": "Cambie a una rama con soporte. El calendario de versiones indica los canales disponibles y sus fechas de fin de soporte.",
    # ---------------------------------------------------------- grades page
    "grades.title": "Qué significan las calificaciones",
    "grades.description": (
        "A+, A, C, D, E y F: qué dice cada calificación sobre una instancia de "
        "OpenCloud, qué la frena, y el camino más corto hasta la siguiente."
    ),
    "grades.kicker": "La escala",
    "grades.lede": "La nota tiene en cuenta el soporte de la versión instalada, las vulnerabilidades conocidas y las comprobaciones fallidas. Esta página explica la nota inicial, los límites que imponen los hallazgos y los cambios que pueden mejorarla.",
    "grades.scale.kicker": "Seis niveles",
    "grades.scale.heading": "La escala, de mejor a peor",
    "grades.scale.intro": (
        "La escala <strong>0-5</strong> y sus letras son las que "
        "<code>scan.nextcloud.com</code> hizo familiares, conservadas "
        "deliberadamente para que un umbral, un gráfico o una regla de alerta "
        "existentes sigan teniendo el mismo significado. Por eso tampoco "
        "existe la <strong>B</strong>: la escala la omite, e inventar una aquí "
        "haría que dos números significasen la misma calificación."
    ),
    "grades.row.prefix": "Calificación {label}: ",
    "grades.row.score": "{rating} de 5",
    "grades.row.improve": "Para mejorar:",
    "grades.caps.kicker": "El techo",
    "grades.caps.heading": "Qué puede hacerle a una calificación una comprobación fallida",
    "grades.caps.intro": (
        "La versión establece la calificación de partida. Las comprobaciones "
        "fallidas no pueden elevarla; solo pueden frenarla, y hasta qué punto "
        "depende de la gravedad de la peor que haya fallado:"
    ),
    "grades.caps.at_best": "como máximo",
    "grades.caps.shared": "Los hallazgos de la misma gravedad imponen el mismo límite a la nota. Si quedan tres de gravedad media, corregir solo uno no elimina ese límite. El plan incluye los tres pasos e indica cuándo mejoraría la nota.",
    "grades.caps.rules": "Dos reglas tienen prioridad. <strong>El fin del soporte siempre determina la nota</strong>: una versión sin soporte recibe <strong>F</strong>, aunque se apliquen excepciones. <strong>Una versión más reciente que la de su canal declarado no se considera obsoleta</strong>; el informe indica que va por delante de ese canal.",
    "grades.improve.kicker": "El camino más corto",
    "grades.improve.heading": "Corregir los problemas detectados",
    "grades.improve.intro": "Cada informe incluye la información necesaria para planificar las correcciones:",
    "grades.improve.plan": "<strong>Un plan de corrección por prioridad.</strong> Cada paso indica qué cambiar y la nota que se podría alcanzar tras completar ese paso y todos los anteriores.",
    "grades.improve.release": "<strong>Una versión concreta para actualizar.</strong> El informe indica qué versión corrige la vulnerabilidad <em>en su rama de versiones</em>, respetando el canal elegido.",
    "grades.improve.explained": (
        "<strong>Cada comprobación fallida, explicada.</strong> Qué se midió, "
        "por qué importa y cómo corregirlo, con un enlace a la documentación "
        "de OpenCloud para el ajuste correspondiente."
    ),
    "grades.improve.waiver": "<strong>Exclusiones para los hallazgos que acepta.</strong> Siguen visibles, pero dejan de limitar la nota. Una exclusión solo se aplica a una comprobación fallida y no puede cambiar la nota de una versión sin soporte.",
    "grades.improve.rerun": "Repita el análisis tras realizar los cambios para comprobar qué problemas se han corregido.",
    "grades.limits.kicker": "Alcance",
    "grades.limits.heading": "Lo que una buena calificación no es",
    "grades.limits.body": "Una <strong>A+</strong> significa que las comprobaciones que determinan la nota no detectaron problemas. No cubre los archivos privados, el sistema operativo, las copias de seguridad ni los permisos de las cuentas. Revise también esos aspectos. Consulte <a href=\"/how-it-works\">cómo funciona el análisis</a> para conocer su alcance y sus límites.",
    # -------------------------------------------------------------- catalogue
    "catalogue.title": "Qué comprueba el escáner",
    "catalogue.description": (
        "Cada indicador de refuerzo, cabecera de seguridad, comprobación TLS y "
        "vulnerabilidad conocida que este escáner puede reportar, "
        "independiente de un resultado de análisis concreto."
    ),
    "catalogue.kicker": "Referencia",
    "catalogue.lede": "Consulte las comprobaciones disponibles y los avisos de seguridad utilizados para evaluar una versión. Este catálogo describe el alcance de la herramienta sin analizar ninguna instancia.",
    "catalogue.checks.kicker": "Comprobaciones",
    "catalogue.checks.heading": "Cada comprobación, por categoría",
    "catalogue.checks.lede": (
        "Agrupadas por tema en lugar de por gravedad - la gravedad depende de "
        "la instancia analizada, así que no se muestra aquí."
    ),
    "catalogue.checks.not_configurable": "no configurable",
    "catalogue.advisories.kicker": "Vulnerabilidades",
    "catalogue.advisories.heading": "Vulnerabilidades conocidas",
    "catalogue.advisories.lede": (
        "Cada vulnerabilidad de la base de datos contra la que se evalúa un "
        "análisis, actualizada a diario desde el feed público."
    ),
    "catalogue.advisories.empty.tag": "Ninguna conocida",
    "catalogue.advisories.empty.body": (
        "La base de datos de vulnerabilidades está actualmente vacía."
    ),
    "catalogue.advisories.fixed_in": "Corregido en {version}",
    "catalogue.advisories.unfixed": "Aún no hay corrección publicada",
    # -------------------------------------------------- how the scan works
    "how.title": "Cómo funciona el análisis",
    "how.description": (
        "Qué comprueba este escáner en una instancia de OpenCloud, y qué "
        "ocurre entre pulsar el botón y leer la calificación."
    ),
    "how.kicker": "El método",
    "how.lede": "El escáner se conecta directamente a la dirección indicada y evalúa las respuestas. Examina la información accesible sin una cuenta y utiliza sus datos de versiones y vulnerabilidades para evaluar el software instalado.",
    "how.tests.heading": "Qué se comprueba",
    "how.tests.version.title": "Versión y ciclo de vida",
    "how.tests.version.body": (
        "Qué versión se ejecuta, si todavía recibe correcciones de seguridad, "
        "y si algún aviso publicado coincide con ella. Una versión que ya "
        "alcanzó su fin de vida útil es una F, por muy bien que esté todo lo "
        "demás."
    ),
    "how.tests.transport.title": "Transporte y cabeceras",
    "how.tests.transport.body": (
        "La accesibilidad por HTTPS, el certificado y su vida útil restante, "
        "las versiones de TLS ofrecidas, y las cabeceras de seguridad que "
        "realmente se envían a un navegador: HSTS, CSP, protección contra "
        "framing y de tipo de contenido."
    ),
    "how.tests.hardening.title": "Refuerzo y exposición",
    "how.tests.hardening.body": (
        "Autenticación básica, política de contraseña y caducidad de enlaces "
        "públicos, reglas de contraseñas, listado de directorios, endpoints "
        "expuestos y cualquier cosa que anuncie la versión al mundo."
    ),
    "how.pipeline.kicker": "El proceso",
    "how.pipeline.heading": "De la solicitud al resultado",
    "how.pipeline.lede": "Cada análisis sigue estas cuatro etapas.",
    "how.pipeline.step1": "<strong>Se valida la dirección.</strong> Las direcciones privadas, locales y de metadatos de la nube se rechazan antes de establecer una conexión.",
    "how.pipeline.step2": "<strong>El análisis recibe un identificador aleatorio.</strong> Permite acceder al resultado. No existe una lista pública de análisis.",
    "how.pipeline.step3": "<strong>El análisis entra en la cola.</strong> El número de análisis simultáneos es limitado. Si todos los procesos están ocupados, el análisis espera y la página muestra su posición en la cola.",
    "how.pipeline.step4": "<strong>El resultado caduca.</strong> Después de {minutes} minutos ya no se puede consultar mediante su identificador.",
    "how.faq.kicker": "Preguntas",
    "how.faq.heading": "Preguntas frecuentes",
    "how.faq.q1": "¿Es este el software oficial de OpenCloud?",
    "how.faq.a1": (
        "No. Este es un proyecto comunitario independiente, no afiliado a "
        "OpenCloud GmbH y que la empresa ni recomienda ni respalda. "
        '"OpenCloud" y su logotipo son marcas de sus respectivos titulares, '
        "usadas aquí únicamente para indicar qué software comprueba esta "
        "herramienta."
    ),
    "how.faq.q2": "¿Una buena calificación significa que una instancia es segura?",
    "how.faq.a2": "No. El análisis comprueba la versión declarada, los avisos de seguridad correspondientes y la configuración visible desde fuera, además de las credenciales de demostración publicadas. No evalúa los archivos privados, el sistema operativo, las copias de seguridad ni los permisos de las cuentas. El informe complementa su revisión de seguridad, pero no sustituye una auditoría ni una prueba de penetración.",
    "how.faq.q3": "¿Cuánto tiempo se conserva el resultado?",
    "how.faq.a3": (
        "Solo en memoria, durante {minutes} minutos, y luego desaparece. Sin "
        "cuentas, sin analítica, sin rastreadores - el resto está en "
        '<a href="/privacy">qué conserva este servidor</a>.'
    ),
    "how.faq.q4": "¿Hay un límite de frecuencia?",
    "how.faq.a4": (
        "Sí, por visitante y por objetivo analizado, para que ni un visitante "
        "ocupado acapare la cola ni la misma instancia se analice una y otra "
        "vez seguidas. Las cifras exactas de este despliegue están en la "
        '<a href="/api#api-limits">página de la API</a>.'
    ),
    "how.faq.q5": "¿Puedo analizar sin límite de frecuencia?",
    "how.faq.a5": "Sí. Puede ejecutar la herramienta de código abierto con <a href=\"/cli\">un comando de Docker</a> en su equipo. Los límites de este servicio web no se aplican allí.",
    "how.faq.q6": "¿Un escaneo me indica si hay una actualización de OpenCloud pendiente?",
    "how.faq.a6": "Sí. La versión declarada se contrasta con los datos de versiones disponibles, teniendo en cuenta su soporte y su canal. La sección <a href=\"/documentation/reference#update-check\">Comprobación de actualizaciones</a> explica cómo se obtiene la recomendación.",
    # --------------------------------------------------------------- privacy
    "privacy.title": "Qué conserva este servidor",
    "privacy.description": (
        "Qué se almacena mientras se ejecuta un análisis, durante cuánto "
        "tiempo, y qué registra y qué no registra el registro operativo."
    ),
    "privacy.kicker": "Privacidad",
    "privacy.lede": "Los resultados están disponibles durante {minutes} minutos y después caducan.",
    "privacy.retention.kicker": "Retención",
    "privacy.retention.heading": "Mientras un análisis está activo",
    "privacy.retention.body": "La dirección de destino, las excepciones elegidas y el resultado se guardan con el identificador aleatorio del análisis durante {minutes} minutos. Después caducan. El registro operativo normal solo recoge ese identificador y los eventos de creación, inicio y finalización. Los límites de uso utilizan una huella unidireccional de la dirección del cliente. El operador puede configurar además un registro de auditoría independiente.",
    "privacy.uploads.kicker": "Informes subidos",
    "privacy.uploads.heading": "Informes subidos para comparar",
    "privacy.uploads.body": "El archivo subido se lee en memoria para calcular la comparación. No se conservan su contenido ni su nombre. La comparación permanece disponible mediante un identificador aleatorio durante {minutes} minutos para que pueda volver a abrirla o compartirla. Después caduca y no puede reconstruirse a partir del archivo descartado.",
    "privacy.self_host": "El mismo analizador está disponible como programa de línea de comandos y biblioteca de Python. Al ejecutarlo localmente, su equipo se conecta directamente a la instancia.",
    # ----------------------------------------------------------- legal notice
    "legal.title": "Aviso legal",
    "legal.description": (
        "Identificación del prestador, datos de contacto y advertencias de "
        "responsabilidad del operador de esta instalación."
    ),
    "legal.kicker": "Aviso legal",
    "legal.lede": (
        "Identificación del prestador conforme al derecho alemán, para el "
        "operador de esta instalación."
    ),
    "legal.english_notice": (
        "Este aviso es el texto legal del propio operador y solo está "
        "disponible en inglés. La página que lo rodea está traducida; el texto "
        "de abajo no."
    ),
    # ----------------------------------------------------------------- about
    "about.title": "Acerca de OpenCloud y de este escáner",
    "about.description": (
        "Qué es OpenCloud, quién lo desarrolla, y por qué este escáner es un "
        "proyecto comunitario independiente."
    ),
    "about.kicker": "Acerca de",
    "about.lede": "OpenCloud permite almacenar, sincronizar y compartir archivos. Este escáner independiente comprueba los ajustes de seguridad de una instancia que son visibles desde el exterior.",
    "about.platform.kicker": "La plataforma",
    "about.platform.heading": "Acerca de OpenCloud",
    "about.platform.body": "<a href=\"https://opencloud.eu/\" rel=\"noopener noreferrer\">OpenCloud</a> es una plataforma de código abierto para almacenar, sincronizar y compartir archivos. Sus guías de administración están en <a href=\"https://docs.opencloud.eu/\" rel=\"noopener noreferrer\">docs.opencloud.eu</a>.",
    "about.platform.independent": (
        "Este escáner es un proyecto comunitario independiente. No está "
        "afiliado a OpenCloud GmbH y la empresa ni lo recomienda ni lo "
        "respalda. &ldquo;OpenCloud&rdquo;, el logotipo de OpenCloud y todas "
        "las marcas asociadas son propiedad de sus respectivos titulares."
    ),
    "about.project.kicker": "El proyecto",
    "about.project.heading": "Acerca de este escáner",
    "about.project.body": "Los resultados proceden de <code>check-opencloud-security</code>, un complemento de monitorización con su propia biblioteca de análisis. Puede utilizarlo mediante esta web o ejecutarlo en su equipo.",
    "about.project.origin": "<strong>Massoud Ahmed</strong> creó este proyecto para comprobar los canales de versiones, la configuración y las instalaciones de OpenCloud con una herramienta que los administradores pueden ejecutar en sus propios equipos. <a href=\"{project}\" rel=\"noopener noreferrer\">El código fuente y las contribuciones están en GitHub</a>.",
    # ------------------------------------------------------------------- API
    "api.title": "Analizar desde un script o un agente",
    "api.description": (
        "La API JSON detrás del formulario: cómo enviar un análisis, "
        "consultarlo, qué se niega este servidor a dejar decidir a quien lo "
        "llama, y todo lo que el software necesita para manejarlo: OpenAPI, "
        "flujos de trabajo Arazzo y el endpoint MCP."
    ),
    "api.kicker": "La API",
    "api.lede": "La API JSON permite iniciar análisis, consultar su progreso y descargar los resultados. Los scripts y agentes utilizan el mismo servicio y tienen los mismos límites que el formulario del navegador.",
    "api.submit.kicker": "Enviar y consultar",
    "api.submit.heading": "Enviar y consultar",
    "api.submit.body": (
        "Un envío responde <code>202</code> con el identificador del "
        "análisis; al consultarlo se obtiene <code>queued</code>, "
        "<code>running</code> o el resultado terminado, y <code>404</code> "
        "una vez ha expirado. Solo se leen cuatro campos: la dirección, las "
        "comprobaciones a exceptuar, el canal de publicación y el formato de "
        "salida. Cualquier otra cosa en el cuerpo, sobre todo la concurrencia "
        "y los tiempos de espera, se rechaza: la intensidad con la que este "
        "servidor analiza no es decisión de quien lo llama."
    ),
    "api.limits.kicker": "Uso razonable",
    "api.limits.heading": "Uso razonable",
    "api.limits.enforced": "Esta instalación permite {client} solicitudes por dirección cada {window} minuto(s), con {cooldown}. Si se supera un límite, devuelve <code>429</code> y una cabecera <code>Retry-After</code>.",
    "api.limits.cooldown": "un análisis por objetivo cada {minutes} minuto(s)",
    "api.limits.no_cooldown": "sin tiempo de espera por objetivo",
    "api.limits.daily": "Como máximo {count} análisis por red al día.",
    "api.limits.probe": "Una red cuyos análisis no dejan de encontrar algo que no es OpenCloud queda en pausa un tiempo.",
    "api.limits.none": "Este despliegue no establece ningún límite de frecuencia.",
    "api.limits.self_host": "También puede ejecutar el analizador en su equipo sin estos límites: <a href=\"{project}\" rel=\"noopener noreferrer\">código fuente en GitHub</a>.",
    "api.schema.kicker": "El esquema",
    "api.schema.heading": "El esquema",
    "api.schema.body": (
        "Los documentos legibles por máquina son siempre públicos, en este "
        'despliegue y en cualquier otro: la <a href="/openapi.json">'
        "descripción OpenAPI 3.1</a> de cada operación, y los "
        '<a href="/arazzo.json">flujos de trabajo Arazzo 1.0.1</a> que '
        "indican cómo se combinan esas operaciones para enviar un análisis, "
        "esperarlo y recoger el resultado."
    ),
    "api.schema.docs_on": (
        'Ambos se pueden explorar aquí como <a href="/docs">Swagger UI</a> y '
        '<a href="/redoc">ReDoc</a>, servidos desde este servidor como todo '
        "lo demás; nada se obtiene de ningún otro sitio."
    ),
    "api.schema.docs_off": (
        "Los visores interactivos (Swagger UI en <code>/docs</code>, ReDoc "
        "en <code>/redoc</code>) están desactivados en este despliegue; un "
        "operador los activa con <code>COS_WEB_ENABLE_DOCS=true</code>."
    ),
    # ------------------------------------------------- API, for agents
    "api.agents.kicker": "Agentes de IA",
    "api.agents.heading": "Empieza desde una sola dirección",
    "api.agents.intro": "Los agentes pueden consultar las operaciones de la API y los flujos de análisis en los documentos públicos que figuran a continuación, sin necesidad de una cuenta.",
    "api.agents.discovery": (
        '<strong>Descubrimiento</strong>: <a href="/.well-known/ai.json">'
        "/.well-known/ai.json</a> nombra todo lo que sigue, con URLs "
        "absolutas. Empieza aquí."
    ),
    "api.agents.openapi": (
        '<strong>OpenAPI</strong>: <a href="/openapi.json">/openapi.json</a>, '
        "cada operación con sus códigos de estado reales y las formas de sus "
        "respuestas."
    ),
    "api.agents.arazzo": (
        '<strong>Flujos de trabajo Arazzo</strong>: <a href="/arazzo.json">'
        "/arazzo.json</a>, el ciclo de vida de un análisis: enviar, "
        "consultar, detectar la finalización, exportar."
    ),
    "api.agents.mcp": (
        "<strong>MCP</strong>: <code>{url}</code>, un endpoint de Model "
        "Context Protocol sobre HTTP en streaming. Herramientas: "
        "<code>scan_instance</code>, <code>scan_instances</code>, "
        "<code>get_scan_result</code>, <code>plan_remediation</code>, "
        "<code>export_scan</code> y <code>erase_instance_data</code>. "
        "<code>scan_instance</code> realiza toda la tarea (envío, espera y "
        "resultado) en una sola llamada. Los prompts nombran las tareas "
        "mismas, como <code>audit_instance</code>, que audita una instancia y "
        "redacta el plan de corrección, y "
        "<code>review_transport_security</code>, que solo examina el "
        "certificado y el saludo TLS. Responde al protocolo en lugar de a un "
        "navegador, así que es una dirección para configurar más que una "
        "página para abrir."
    ),
    "api.agents.summary": "OpenAPI define las operaciones disponibles; Arazzo describe cómo combinarlas para realizar un análisis. Ambos documentos se generan a partir del código del servicio.",
    "api.agents.summary_mcp": "OpenAPI define las operaciones, Arazzo describe los flujos de trabajo y MCP los ofrece como herramientas para agentes. Todos utilizan la misma implementación del servicio.",
    "api.webmcp.kicker": "En el navegador",
    "api.webmcp.heading": "Usa la página como herramienta",
    "api.webmcp.intro": (
        "Un navegador compatible con el "
        '<a href="https://webmachinelearning.github.io/webmcp/" '
        'rel="noopener noreferrer">borrador de WebMCP</a> puede descubrir las '
        "acciones de la página abierta. No hace falta configurar otro cliente."
    ),
    "api.webmcp.landing": (
        "En la página de inicio, <code>scan_opencloud_security</code> pone un "
        "análisis en cola. Su esquema contiene los canales de versión, formatos "
        "de salida y excepciones que ofrece esa página."
    ),
    "api.webmcp.result": (
        "En una página de resultados, <code>get_scan_result</code> lee el análisis "
        "actual y <code>export_scan_report</code> descarga JSON, CSV, SARIF o PDF "
        "para el uuid que ya se está viendo."
    ),
    "api.webmcp.boundary": (
        "Cada herramienta del navegador llama a la misma API JSON con "
        "<code>Accept: application/json</code>. Se mantienen la protección SSRF, "
        "los límites, la espera por objetivo, la cola y el aislamiento por uuid."
    ),
    "api.webmcp.support": (
        "WebMCP todavía es un borrador y los navegadores sin soporte lo ignoran. "
        "Al desactivar MCP en este despliegue también desaparecen las herramientas "
        "del navegador."
    ),
    "api.clients.kicker": "Configuración",
    "api.clients.heading": "Configurar un cliente de agente",
    "api.clients.intro": "Configure el cliente con la URL del punto de acceso y el transporte HTTP streamable. Si el operador exige autenticación, también deberá iniciar sesión.",
    "api.clients.body": (
        "Encontrará configuraciones completas para Claude Code, Claude "
        "Desktop, GitHub Copilot en VS Code y en la CLI, Cursor, Zed y "
        "Windsurf, para este despliegue o para el suyo propio, en "
        '<a href="{project}/blob/main/docs/mcp.md" '
        'rel="noopener noreferrer">la guía de MCP</a>.'
    ),
    "api.rules.kicker": "Las reglas",
    "api.rules.heading": "Las mismas reglas que para todos",
    "api.rules.body": "Los agentes siguen los mismos procesos y límites. El análisis es asíncrono y su UUID permite consultar el resultado. Ante un <code>429</code>, respete el tiempo de espera indicado. Para revisar muchas instancias de forma habitual, puede <a href=\"{project}\" rel=\"noopener noreferrer\">ejecutar el analizador localmente</a>.",
    # -------------------------------- Docker one-liners, on /documentation
    "cli.lede": "Ejecute el escáner en su equipo para controlar el análisis y evitar los límites de este servicio. Los comandos siguientes utilizan el mismo escáner que este sitio.",
    "cli.oneliner.kicker": "El comando de una línea",
    "cli.oneliner.heading": "Un comando, nada instalado",
    "cli.oneliner.body": "El comando muestra la nota, el estado del soporte, los avisos de seguridad aplicables y las comprobaciones fallidas. Su código de salida de Nagios permite usarlo en monitorización, scripts, CI o tareas cron. El análisis se ejecuta en el contenedor y se conecta directamente a su instancia.",
    "cli.json.kicker": "Como JSON",
    "cli.json.heading": "El documento de resultado completo",
    "cli.json.body": (
        "Cada número de una página de resultados sale de este documento, "
        'incluido el bloque <code>addresses</code> detrás de la línea '
        "<strong>Resuelto a</strong>: las direcciones IPv4 e IPv6 a las que "
        "apuntaba el nombre mientras se ejecutaba el análisis."
    ),
    "cli.private.kicker": "Red interna",
    "cli.private.heading": "Las instancias que este sitio no analizará",
    "cli.private.body": "Ejecute el analizador de línea de comandos desde un equipo que pueda acceder a su instancia interna. Admite direcciones privadas y nombres DNS internos. Los servicios públicos restringen esos destinos para impedir el acceso a sus propias redes internas.",
    "cli.nodocker.kicker": "¿Sin Docker?",
    "cli.nodocker.heading": "Sin contenedor",
    "cli.nodocker.body": "El analizador también está disponible en PyPI. Utilice <code>uv</code> para ejecutarlo cuando lo necesite o <code>pipx</code> para instalarlo en un entorno Python aislado.",
    # ------------------------------------------------ CLI documentation index
    "docs.index.title": "Documentación de la CLI",
    "docs.index.description": "Instalación, uso y configuración de check-opencloud-security, con guías para su administración.",
    "docs.index.kicker": "Documentación",
    "docs.index.heading": "Utilizar el analizador desde el terminal",
    "docs.index.lede": "Instale el escáner, ejecute la primera comprobación y configúrelo para un uso periódico. Las guías de <code>docs/</code> explican la monitorización, la CI, el despliegue y las comprobaciones detrás de cada hallazgo.",
    "docs.index.toc.quickstart": "Inicio rápido",
    "docs.index.toc.commands": "Comandos",
    "docs.index.toc.options": "Opciones útiles",
    "docs.index.toc.configuration": "Configuración",
    "docs.index.toc.monitoring": "Monitorización",
    "docs.index.toc.guides": "Guías completas",
    "docs.index.quickstart.kicker": "Inicio rápido",
    "docs.index.quickstart.heading": "Una comprobación, sin instalar nada",
    "docs.index.quickstart.container": "También puede utilizar la imagen publicada. Ejecuta el mismo complemento y devuelve el mismo código de salida de Nagios/Icinga:",
    "docs.index.quickstart.note": (
        "El complemento se comunica directamente con la instancia. No envía "
        "la dirección a este sitio web ni a ningún servicio remoto de "
        "veredictos."
    ),
    "docs.index.commands.kicker": "Dos puntos de entrada",
    "docs.index.commands.heading": "El veredicto y el documento de resultado",
    "docs.index.commands.plugin": (
        "El complemento de monitorización: una línea de alerta, datos de "
        "rendimiento y los códigos de salida estándar <strong>OK</strong>, "
        "<strong>WARNING</strong>, <strong>CRITICAL</strong> y "
        "<strong>UNKNOWN</strong>."
    ),
    "docs.index.commands.scanner": (
        "La biblioteca del escáner como CLI: el documento de resultado JSON "
        "completo para un script, una canalización o una investigación "
        "puntual."
    ),
    "docs.index.options.kicker": "Las opciones del día a día",
    "docs.index.options.heading": "Opciones útiles",
    "docs.index.option.host": (
        "Nombre de host, IP o URL; separados por comas para varias instancias."
    ),
    "docs.index.option.check_hardening": (
        "Incluye las medidas de refuerzo faltantes y las cabeceras de seguridad."
    ),
    "docs.index.option.release_track": (
        "<code>rolling</code>, <code>production</code>, <code>lts</code> o "
        "<code>auto</code>."
    ),
    "docs.index.option.ignore_hardening": (
        "Acepta un hallazgo sin borrar su evidencia; repetible y admite "
        "comodines."
    ),
    "docs.index.option.debug": (
        "Explica de dónde partió la calificación y qué la frenó."
    ),
    "docs.index.option.insecure": (
        "Omite la verificación del certificado para una instancia que controlas."
    ),
    "docs.index.option.thresholds": "Defina los umbrales de puntuación para los estados de monitorización.",
    "docs.index.option.format": "Imprime la salida de Nagios o texto de Prometheus.",
    "docs.index.option.baseline": (
        "Alerta solo sobre hallazgos nuevos o peores que en la ejecución anterior."
    ),
    "docs.index.option.webhook": (
        "Notifica a otro sistema cuando se alcanza el estado configurado."
    ),
    "docs.index.options.manual": (
        "<code>check-opencloud-security --help</code> es el manual "
        'instalado. La <a href="{project}#cli-usage" '
        'rel="noopener noreferrer">tabla completa de opciones</a> incluye '
        "cada valor predeterminado y su variable de entorno <code>COS_</code>."
    ),
    "docs.index.configuration.kicker": "Una sola dirección",
    "docs.index.configuration.heading": "Configuración y prioridad",
    "docs.index.configuration.intro": (
        "Los ajustes pueden provenir de un archivo YAML o JSON, del entorno o "
        "de la línea de comandos. El orden es siempre:"
    ),
    "docs.index.precedence.aria": "Prioridad de configuración, de mayor a menor",
    "docs.index.precedence.cli": "Opción de la CLI",
    "docs.index.precedence.cli.note": "la respuesta explícita para esta ejecución",
    "docs.index.precedence.env": "Entorno",
    "docs.index.precedence.env.note": (
        "<code>COS_*</code>, útil en contenedores y servicios"
    ),
    "docs.index.precedence.file": "Archivo de configuración",
    "docs.index.precedence.file.note": "los valores predeterminados duraderos del operador",
    "docs.index.precedence.default": "Valor predeterminado incorporado",
    "docs.index.precedence.default.note": (
        "la respuesta segura cuando no se especificó nada"
    ),
    "docs.index.configuration.wizard": "Deja que el asistente escriba el primer archivo:",
    "docs.index.configuration.note": (
        "Un archivo que termina en <code>.json</code> es JSON; cualquier "
        "otra extensión es YAML. Los secretos pueden vivir en archivos "
        "separados en lugar de en la línea de comandos."
    ),
    "docs.index.monitoring.kicker": "Ponlo a trabajar",
    "docs.index.monitoring.heading": (
        "Monitorización, automatización y varias instancias"
    ),
    "docs.index.monitoring.nagios": (
        "<strong>Nagios o Icinga:</strong> usa directamente la salida del "
        "complemento; el peor umbral configurado determina el código de "
        "salida."
    ),
    "docs.index.monitoring.fleet": (
        "<strong>Varias instancias:</strong> pasa una lista de hosts "
        "separados por comas, o usa un archivo de configuración por "
        "instancia en cuanto sus ajustes diverjan."
    ),
    "docs.index.monitoring.prometheus": (
        "<strong>Prometheus:</strong> usa <code>--format=prometheus</code> "
        "una vez, o expón el exportador incorporado con "
        "<code>--prometheus-listen-port</code>."
    ),
    "docs.index.monitoring.ci": "<strong>CI:</strong> utilice el mismo comando en su flujo de trabajo. El código de salida permite hacer fallar el trabajo según la política configurada.",
    "docs.index.monitoring.scheduled": (
        "<strong>Comprobaciones programadas:</strong> systemd, cron, "
        "Kubernetes y el rol de Ansible usan todos el mismo flujo de CLI y "
        "configuración."
    ),
    "docs.index.guides.kicker": "Desde el repositorio",
    "docs.index.guides.heading": "Guías completas para operadores",
    "docs.index.guides.lede": (
        "Cada documento fuente tiene aquí su propia página HTML, generada a "
        "partir del Markdown del repositorio y comprobada en CI para "
        "detectar desviaciones."
    ),
    # --------------------------------------------------- generated guide pages
    "docs.guide.kicker": "Documentación de la CLI",
    "docs.guide.english_notice": "Esta guía está disponible en inglés, alemán, francés y español. Se muestra la versión inglesa para el idioma seleccionado.",
    "docs.guide.toc.heading": "En esta página",
    "docs.guide.toc.aria": "En esta página",
    # ---------------------------------------------------------------- compare
    "compare.title": "Comparar dos análisis",
    "compare.description": (
        "Compare dos análisis finalizados de la misma instancia y vea qué se "
        "ha corregido, qué es nuevo y qué sigue abierto."
    ),
    "compare.eyebrow": "¿Funcionaron las correcciones?",
    "compare.heading": "Comparar dos análisis",
    "compare.lede": "Introduzca los UUID de un análisis anterior y uno posterior. Ambos resultados deben estar disponibles. Si el anterior ha caducado, utilice un informe descargado en el formulario siguiente.",
    "compare.form.baseline": "Análisis anterior",
    "compare.form.current": "Análisis posterior",
    "compare.form.placeholder": "El UUID de la dirección de una página de resultado",
    "compare.form.submit": "Comparar",
    "compare.form.hint": (
        "El UUID es la parte que sigue a <code>/scan/</code> en la dirección "
        "de una página de resultado. Es toda la autorización sobre ese "
        "resultado, así que trátelo como una contraseña."
    ),
    "compare.error.unknown.baseline": (
        "El análisis anterior es desconocido o ha caducado. Aquí no se puede "
        "buscar: analice la instancia de nuevo y compare los dos resultados "
        "más recientes."
    ),
    "compare.error.unknown.current": (
        "El análisis posterior es desconocido o ha caducado. Aquí no se puede "
        "buscar: analice la instancia de nuevo y compare los dos resultados "
        "más recientes."
    ),
    "compare.error.unfinished.baseline": (
        "El análisis anterior aún no ha terminado. Abra su página de "
        "resultado, espere a que acabe y vuelva a comparar."
    ),
    "compare.error.unfinished.current": (
        "El análisis posterior aún no ha terminado. Abra su página de "
        "resultado, espere a que acabe y vuelva a comparar."
    ),
    "compare.error.same": (
        "Ambos campos nombran el mismo análisis, así que no hay nada que "
        "comparar. Analice la instancia de nuevo y compare el UUID nuevo con "
        "este."
    ),
    "compare.error.different_targets": "Los dos análisis corresponden a instancias distintas, por lo que no se comparan. Compare dos análisis de la misma instancia.",
    "compare.verdict.kicker": "Entre los dos análisis",
    "compare.verdict.improved": "Ha mejorado",
    "compare.verdict.unchanged": "No ha cambiado nada",
    "compare.verdict.regressed": "Ha empeorado",
    "compare.rating.up": "La nota ha subido {points} punto(s).",
    "compare.rating.down": "La nota ha bajado {points} punto(s).",
    "compare.rating.same": "La nota no ha cambiado. Aun así, puede haber hallazgos corregidos: varios hallazgos pueden imponer el mismo límite. Las listas siguientes muestran los cambios.",
    "compare.side.baseline": "Anterior",
    "compare.side.current": "Posterior",
    "compare.side.target": "Instancia",
    "compare.side.version": "Versión",
    "compare.side.scanned": "Analizada",
    "compare.side.unknown": "No determinado",
    "compare.side.open": "Abrir este resultado",
    "compare.introduced.heading": "Hallazgos nuevos ({count})",
    "compare.introduced.none": "No hay nada nuevo desde el análisis anterior.",
    "compare.resolved.heading": "Hallazgos resueltos ({count})",
    "compare.resolved.none": (
        "No ha desaparecido nada de lo que estaba abierto en el análisis "
        "anterior."
    ),
    "compare.unchanged.heading": "Siguen abiertos ({count})",
    "compare.unchanged.none": "No hay nada abierto en ambos análisis.",
    "compare.changes.heading": "Lo que detalla la comparación",
    "compare.changes.category": "Categoría",
    "compare.changes.change": "Cambio",
    "compare.nothing_stored": (
        "Esta comparación se ha calculado a partir de los dos resultados y no "
        "se ha guardado en ninguna parte. Al recargar se vuelve a calcular; si "
        "caduca cualquiera de los dos resultados, ya no se podrá pedir."
    ),
    # ----------------------------------------------------------------- search
    # ---------------------------------------- comparación con un archivo
    "compare.upload.kicker": "Comparar un informe guardado",
    "compare.upload.heading": "Comparar un informe anterior con un análisis",
    "compare.upload.lede": "Suba un informe JSON o CSV descargado anteriormente y compárelo con un análisis de este servicio. Así puede utilizar un resultado anterior aunque su enlace haya caducado.",
    "compare.upload.field.report": "Informe anterior",
    "compare.upload.field.current": "Análisis posterior",
    "compare.upload.field.hint": (
        "El archivo <code>.json</code> o <code>.csv</code> de las descargas de "
        "una página de resultado. Hasta {kilobytes} KB."
    ),
    "compare.upload.submit": "Comparar con este archivo",
    "compare.upload.privacy": (
        "El archivo se lee una vez, en memoria, para calcular la comparación, y "
        "nunca se escribe en disco ni se conserva. La comparación en sí se "
        "guarda {minutes} minutos para que esta página pueda recargarse, y "
        "después también desaparece."
    ),
    "compare.upload.source.kicker": "De dónde viene el lado anterior",
    "compare.upload.source.json": "El informe anterior procede de un archivo JSON subido. No tiene una página de resultados aquí; el archivo se descartó tras leerlo.",
    "compare.upload.source.csv": "El informe anterior procede de un archivo CSV subido. No tiene una página de resultados aquí; el archivo se descartó tras leerlo.",
    "compare.upload.source.dropped": (
        "{count} línea(s) del archivo no llevan los nombres con los que este "
        "escáner nombra sus hallazgos y quedaron fuera de la comparación."
    ),
    "compare.upload.source.missing.httpsEnforced": (
        "El archivo subido no registra si se forzaba HTTPS, así que esa medida "
        "quedó fuera de ambos lados en lugar de adivinarse. Un CSV descargado "
        "antes de esta novedad es uno de esos archivos."
    ),
    "compare.upload.source.missing.update": (
        "El archivo subido no registra si había una actualización pendiente, así "
        "que las actualizaciones pendientes quedaron fuera de ambos lados en "
        "lugar de adivinarse. Un CSV descargado antes de esta novedad es uno de "
        "esos archivos."
    ),
    "compare.upload.expires": (
        "Esta comparación desaparece en unos {minutes} minutos, y el enlace deja "
        "de funcionar. Nada aquí puede reconstruirla: el archivo del que salió ya "
        "no está."
    ),
    "compare.upload.error.missing": "Seleccione el informe JSON o CSV que descargó anteriormente.",
    "compare.upload.error.no_current": "Indique el UUID del análisis con el que desea comparar el informe.",
    "compare.upload.error.empty": "Ese archivo está vacío.",
    "compare.upload.error.too_large": "El archivo supera el tamaño permitido de {kilobytes} KB.",
    "compare.upload.error.unreadable": "No se pudo leer el archivo como JSON ni como CSV. Suba la descarga original sin modificar.",
    "compare.upload.error.not_a_report": (
        "Ese archivo no parece un informe de análisis de este servicio. Lo que se "
        "espera son las descargas de una página de resultado."
    ),
    "compare.upload.error.rate_limit": "Se han subido varios informes desde su red en poco tiempo. Espere un minuto y vuelva a intentarlo.",
    "compare.upload.error.expired": "Este enlace ha caducado. Los resultados de una comparación se conservan durante {minutes} minutos; vuelva a subir el archivo para repetirla.",
    "search.title": "Buscar",
    "search.description": (
        "Busca en la documentación del escáner y en las guías públicas. Los "
        "resultados de análisis nunca se indexan."
    ),
    "search.eyebrow": "Índice estático de la versión",
    "search.heading": "Buscar en el escáner",
    "search.lede": (
        "Solo documentación y guías públicas. El índice se reconstruye con "
        "cada versión; nunca lee el almacén de análisis, las páginas de "
        "resultados, los UUID ni las direcciones enviadas."
    ),
    "search.label": "Buscar en la documentación",
    "search.placeholder": "TLS, Docker, exenciones...",
    "search.submit": "Buscar",
    "search.scope.operator": "Área de operación",
    "search.status.idle": "Introduzca un término de búsqueda.",
    "search.status.results": "{count} resultado(s) en esta versión.",
    "search.status.empty": "Ninguna documentación pública coincide con esa búsqueda.",
    "search.status.error": "La búsqueda no está disponible temporalmente.",
    # The search manifest: the title and summary an index entry carries, as
    # opposed to the words on the page itself.
    "search.page.index.title": "Analizar una instancia de OpenCloud",
    "search.page.index.summary": "Analizar la seguridad pública de una instancia de OpenCloud.",
    "search.page.how.title": "Cómo funciona el escáner",
    "search.page.how.summary": (
        "Qué mide el escáner, qué no puede ver, y cómo se gestionan los "
        "resultados."
    ),
    "search.page.grades.title": "Qué significan las calificaciones",
    "search.page.grades.summary": (
        "La escala de calificación de A+ a F y las correcciones que mejoran "
        "cada nivel."
    ),
    "search.page.catalogue.title": "Qué comprueba el escáner",
    "search.page.catalogue.summary": (
        "Cada indicador de refuerzo, cabecera y comprobación TLS del "
        "escáner, y cada vulnerabilidad conocida."
    ),
    "search.page.documentation.title": "Documentación de la CLI",
    "search.page.documentation.summary": (
        "Inicio rápido de línea de comandos, configuración, monitorización y "
        "guías de despliegue."
    ),
    "search.page.api.title": "API",
    "search.page.api.summary": "Enviar análisis, consultar resultados y descargar informes mediante la API o un agente.",
    "search.page.privacy.title": "Privacidad",
    "search.page.privacy.summary": (
        "Retención de resultados, registro de solicitudes, límites de "
        "frecuencia y política sobre terceros."
    ),
    "search.page.about.title": "Acerca de este proyecto",
    "search.page.about.summary": (
        "Por qué existe este escáner de seguridad independiente para OpenCloud."
    ),
    # ------------------------------------------- what a submission is refused for
    # The API answers the English sentence these translate; a browser reads
    # the translation. The SSRF guard names the identifier, this names the
    # sentence, and neither is derived from the other.
    "error.unsupported_fields": (
        "Este servicio no acepta {fields}. El análisis se ejecuta únicamente "
        "con ajustes del lado del servidor."
    ),
    "error.rate_limit.client": "Se han solicitado muchos análisis desde su red en poco tiempo. Espere un minuto y vuelva a intentarlo.",
    "error.rate_limit.probe": "Varios destinos recientes no eran instancias de OpenCloud accesibles. Los análisis desde su red están suspendidos temporalmente. También puede comprobar su propia instancia con el analizador local.",
    "error.rate_limit.daily": "Se ha alcanzado el límite diario de su red. Vuelva mañana o utilice el analizador local, que no tiene este límite.",
    "error.target.wildcard_dns": (
        "Ese nombre pertenece a un servicio que apunta nombres a cualquier "
        "dirección. Escribe el nombre de host propio de la instancia o su dirección."
    ),
    "error.target.unstable": (
        "Ese nombre de host responde con direcciones distintas en cada consulta, "
        "así que este servicio no puede determinar con certeza qué analizaría."
    ),
    "error.target.not_approved": (
        "Este servicio solo analiza instancias aprobadas para ello. Pide al "
        "operador que la añada o publica el registro DNS que la aprueba."
    ),
    "error.rate_limit.target": "Esta instancia se ha analizado recientemente. Espere unos minutos.",
    "error.target.invalid": "Esa dirección no se puede analizar.",
    "error.target.empty": "Introduzca la dirección de la instancia de OpenCloud.",
    "error.target.too_long": "Esa dirección es demasiado larga.",
    "error.target.characters": (
        "Esa dirección contiene caracteres que un nombre de host no puede tener."
    ),
    "error.target.unparsed": "No se pudo interpretar esa dirección.",
    "error.target.scheme": "Solo se pueden analizar destinos http:// y https://.",
    "error.target.credentials": "No se aceptan credenciales dentro de la dirección.",
    "error.target.address_only": "Introduzca la dirección base, con una subcarpeta sencilla si la necesita. No se aceptan consultas, fragmentos, parámetros ni cambios de directorio.",
    "error.target.port": "Esa dirección tiene un puerto no válido.",
    "error.target.no_host": "Esa dirección no tiene nombre de host.",
    "error.target.hostname_shape": (
        "Eso no es un nombre de host que este servicio pueda analizar."
    ),
    "error.target.unresolved": "Ese nombre de host no se resuelve.",
    "error.target.hostname_long": "Ese nombre de host es demasiado largo.",
    "error.target.internal": "No se pueden analizar direcciones locales ni internas.",
    "error.target.private": (
        "Esa dirección apunta a una red privada, de loopback o de enlace "
        "local, y este servicio no la analizará."
    ),
    "error.target.blocked": (
        "A este servicio se le ha pedido que no analice esa dirección."
    ),
    "error.store_unavailable": (
        "Este servicio no puede leer ahora mismo su propia configuración y "
        "no analizará mientras no sepa qué objetivos debe excluir. "
        "Inténtalo de nuevo dentro de unos minutos."
    ),
    # ----------------------------------------------------------- result page
    "result.title": "Resultados del análisis",
    "result.description": (
        "El resultado de un análisis público, legible únicamente con su "
        "propio identificador."
    ),
    "result.kicker": "Análisis de seguridad",
    "result.heading": "Resultado del análisis",
    "result.track.title": "El canal de publicación contra el que se calificó este análisis",
    "result.track.label": "Canal {track}",
    "result.another": "Analizar otra instancia",
    "result.compare": "Comparar con un análisis anterior",
    "result.tab.queued": "En cola: {target}",
    "result.tab.queued.position": "Puesto {position} en la cola: {target}",
    "result.tab.running": "Analizando: {target}",
    "result.tab.ready": "Informe listo: {target}",
    "result.tab.done": "Nota {label}: {target}",
    "result.tab.failed": "Análisis fallido: {target}",
    "result.compare.offer": (
        "Ya analizaste esta instancia en esta pestaña a las {time}."
    ),
    "result.compare.offer.link": "Ver qué ha cambiado desde entonces",
    "result.progress.kicker": "En curso",
    "result.progress.queued.title": "Esperando un proceso de análisis disponible",
    "result.progress.queued.detail": "Todos los procesos están ocupados. Su análisis mantiene su posición y comenzará cuando quede uno libre.",
    "result.progress.running.title": "Analizando la instancia",
    "result.progress.running.detail": (
        "Leyendo lo que publica la instancia: versión, capacidades, "
        "certificado, cabeceras y los endpoints que expone sin iniciar sesión."
    ),
    "result.progress.step.queued": "En cola",
    "result.progress.step.running": "En ejecución",
    "result.progress.step.done": "Resultado",
    "result.progress.estimate": "La mayoría de los análisis terminan en menos de un minuto.",
    "result.progress.elapsed": "hace {duration}",
    "result.progress.noscript": (
        "Esta página se actualiza sola mediante JavaScript. Sin él, recarga "
        "la página en unos segundos para ver el resultado."
    ),
    "result.progress.queue.position": (
        "Análisis en cola. Posición en la fila: n.º {position} de {length}."
    ),
    "result.progress.queue.next": "Análisis en cola. Eres el siguiente.",
    "result.progress.queue.waiting": "Esperando a que un proceso de análisis lo recoja.",
    "result.progress.done.title": "Informe listo",
    "result.progress.done.detail": "La calificación ya está lista. Abriendo el informe.",
    "result.progress.failed.title": "Análisis finalizado",
    "result.progress.failed.detail": (
        "El análisis no se pudo completar. Abriendo lo que se obtuvo."
    ),
    "result.failed.fallback": "El análisis no se pudo completar.",
    "result.failed.body": "El escáner no pudo obtener información suficiente para asignar una nota. Revise la dirección, confirme que ejecuta OpenCloud y compruebe que la instancia sea accesible desde este servicio.",
    "result.document.kicker": "Documento de resultado",
    "result.document.heading": "Documento de resultado",
    "result.document.lede": (
        "El mismo documento que evalúan la comprobación de línea de comandos "
        "y el complemento de Nagios."
    ),
    "result.verdict.kicker": "Veredicto",
    "result.verdict.heading": "Calificación general",
    "result.verdict.dial": "Calificación {label}, {rating} de 5",
    "result.facts.instance": "Instancia",
    "result.facts.resolved": "Resuelto a",
    "result.facts.ipv6.heading": "Accesibilidad IPv6",
    "result.facts.ipv6.note": (
        "No comprobada - este despliegue no tiene conectividad IPv6 "
        "saliente, así que solo se anota aquí en lugar de penalizar la "
        "instancia."
    ),
    "result.facts.product": "Producto",
    "result.facts.track": "Canal de publicación",
    "result.facts.track.unknown": "desconocido",
    "result.facts.eol_tag": "Fin de vida útil",
    "result.facts.schedule": "Calendario de versiones",
    "result.facts.schedule.stale": (
        "{version} es más reciente que esta copia del calendario de "
        "versiones de OpenCloud, así que el calendario probablemente esté "
        "desactualizado. Esto no se cuenta en contra de la instancia -"
    ),
    "result.facts.schedule.stale_generated": (
        "{version} es más reciente que esta copia del calendario de "
        "versiones de OpenCloud, generada el {generated}, así que el "
        "calendario probablemente esté desactualizado. Esto no se cuenta en "
        "contra de la instancia -"
    ),
    "result.facts.schedule.link": "consulta la página publicada del ciclo de vida",
    "result.facts.signin": "Inicio de sesión",
    "result.facts.signin.external": "Proveedor externo",
    "result.facts.signin.upstream_tag": "upstream",
    "result.facts.signin.version_unavailable": "versión no expuesta",
    "result.facts.signin.advisories": "consultar avisos de seguridad",
    "result.facts.signin.builtin": "Proveedor de identidad integrado",
    "result.facts.signin.none": "No detectado -",
    "result.facts.signin.link": "cómo se configura el inicio de sesión de OpenCloud",
    "result.facts.proxy": "Proxy inverso",
    "result.facts.proxy.detected": "Detectado",
    "result.facts.office": "Office",
    "result.facts.calendar": "Calendario",
    "result.facts.calendar.detected": "Algo responde en la ruta CalDAV",
    "result.facts.newest": "Versión más reciente",
    "result.facts.score": "Puntuación",
    "result.facts.score.value": "{rating} de 5",
    "result.counter.critical": "Crítico",
    "result.counter.warning": "Advertencia",
    "result.counter.info": "Información",
    "result.counter.advisories": "Avisos",
    "result.counter.passed": "Superadas",
    "result.verdict.why": "Por qué esta calificación:",
    "result.verdict.caveat": (
        "Una calificación indica que las comprobaciones de abajo se "
        "superaron, no que la instancia sea segura. Este análisis no es "
        "exhaustivo: solo ve lo que la instancia muestra a un visitante "
        'anónimo. <a href="#scan-limits">Lo que no puede ver</a>.'
    ),
    "result.fix": "Solución:",
    "result.documentation": "Documentación",
    "result.explain.title": "Qué significa esta comprobación",
    "result.plan.kicker": "Plan de corrección",
    "result.plan.heading": "Pasos para alcanzar {label}",
    "result.plan.then": "luego {label}",
    "result.plan.still": "sigue en {label}",
    "result.plan.note": "El plan prioriza los cambios que mejoran la nota. La nota indicada junto a cada paso supone que se ha completado ese paso y todos los anteriores. Los hallazgos de igual gravedad comparten un límite, por lo que pueden hacer falta varias correcciones antes de que la nota mejore.",
    "result.plan.blocked.heading": "Frenando la calificación, y sin solución posible",
    "result.plan.blocked.note": (
        "OpenCloud codifica estos valores de forma fija, así que ningún "
        "ajuste los alcanza. Son la razón por la que el plan anterior se "
        "detiene donde lo hace."
    ),
    "result.eol.alert": (
        "Esta versión ya no recibe correcciones de seguridad. Nada más en "
        "esta página puede elevar la calificación hasta que se actualice."
    ),
    "result.advisories.kicker": "Avisos",
    "result.advisories.heading": "Avisos conocidos para esta versión",
    "result.advisories.lede": (
        "Avisos publicados cuyo rango afectado incluye {version}."
    ),
    "result.advisories.fallback_id": "aviso",
    "result.advisories.unrated": "sin calificar",
    "result.advisories.no_summary": "No se ha publicado ningún resumen.",
    "result.advisories.read": "Leer el aviso",
    "result.findings.kicker": "Hallazgos",
    "result.findings.heading": "Comprobaciones que fallaron",
    "result.findings.lede": (
        "Cada uno limita la calificación al nivel que permite su gravedad. "
        "Corrige primero los críticos: son los que más frenan la puntuación."
    ),
    "result.findings.filter.aria": "Filtrar hallazgos por gravedad",
    "result.findings.filter.active": "Mostrando solo hallazgos de gravedad {severity}.",
    "result.findings.filter.clear": "Mostrar todos los hallazgos",
    "result.findings.allclear.tag": "Todo en orden",
    "result.findings.allclear.body": (
        "Todas las comprobaciones que ejecuta este escáner se superaron en "
        "esta instancia."
    ),
    "result.hardening.kicker": "Refuerzo",
    "result.hardening.heading": "Refuerzos que vale la pena añadir",
    "result.hardening.lede": "Estos ajustes añaden protección frente a riesgos habituales. Revise la explicación y la corrección propuesta para cada uno.",
    "result.hardening.tag": "refuerzo",
    "result.header.tag": "cabecera",
    # ------------------------------------------------- configuration fragment
    "result.fragment.kicker": "La corrección, escrita",
    "result.fragment.heading": "Pegue esto en su configuración",
    "result.fragment.lede": (
        "Los hallazgos de arriba, en la sintaxis del archivo que debe "
        "cambiar. Elija dónde se configura su instancia."
    ),
    "result.fragment.caution": (
        "Lea la línea «Corrección» de cada hallazgo antes de pegar. Estos son "
        "los valores que buscan las comprobaciones, no una revisión de lo que "
        "necesita su despliegue."
    ),
    "result.fragment.picker": "Formato de configuración",
    "result.fragment.file": "Va en {name}.",
    "result.fragment.copy": "Copiar",
    "result.fragment.copied": "Copiado",
    "result.fragment.copy_failed": "No se pudo copiar",
    "result.fragment.nothing": "Ningún hallazgo pendiente puede corregirse en este formato. Utilice {flavours} para la configuración correspondiente.",
    "result.fragment.elsewhere": (
        "Estos se corrigen en otro sitio - corresponden a {flavours}:"
    ),
    "result.fragment.undecided": "Estos hallazgos requieren un ajuste adecuado para su instalación. Siga las instrucciones de corrección de cada uno para determinar el valor.",
    # ------------------------------------------------------------ scan again
    "result.rescan": "Analizar de nuevo",
    "result.rescan.ready": "Esta instancia se puede analizar de nuevo.",
    "result.rescan.wait": "Se podrá analizar de nuevo en {countdown}.",
    "result.rescan.note": "El próximo análisis utiliza el mismo destino, las mismas exclusiones y el mismo canal para poder comparar los resultados. Espere a que termine el intervalo o ejecute el escáner de código abierto sin límites en su equipo:",
    "result.rescan.self_host": "ejecútelo usted mismo",
    "result.excluded.kicker": "Excluido",
    "result.excluded.heading": "Reportado, pero no contabilizado",
    "result.excluded.waived.heading": "Pediste ignorar estos",
    "result.excluded.waived.note": "Siguieron fallando. Simplemente no frenaron la calificación.",
    "result.excluded.unfixable.heading": "Valores fijos en OpenCloud",
    "result.excluded.unfixable.note": "Estos valores están fijados en el código de OpenCloud y no se pueden configurar. Se muestran como referencia y no afectan a la nota.",
    "result.scope.kicker": "Alcance",
    "result.scope.heading": "Lo que este análisis no puede ver",
    "result.scope.body": (
        "Todo lo anterior se leyó sin iniciar sesión, que es precisamente el "
        "objetivo y también el límite. <strong>La ausencia de un hallazgo no "
        "es prueba de seguridad</strong>, y la calificación más alta que "
        "puede dar esta página no es una afirmación de que la instancia sea "
        "segura, solo de que ninguna de las comprobaciones realizadas aquí falló. Categorías "
        "enteras quedan totalmente fuera del alcance de un análisis no "
        "autenticado: el sistema operativo y sus paquetes, el entorno de "
        "ejecución de contenedores, la configuración propia del proxy "
        "inverso, las copias de seguridad y sus restauraciones, el "
        "almacenamiento detrás de la instancia, el manejo de secretos y "
        "claves, las cuentas, las contraseñas y el inicio de sesión "
        "multifactor, los permisos de los recursos compartidos existentes, "
        "la cadena de suministro del software, y cualquier cosa que solo se "
        "muestre a un usuario que ha iniciado sesión. Lo mismo ocurre con "
        "estas dos, que parece que deberían ser visibles y no lo son:"
    ),
    "result.scope.audit": (
        "<strong>Registro de auditoría.</strong> El servicio de auditoría de "
        "OpenCloud solo consume el bus de eventos interno; no publica ningún "
        "endpoint ni aparece en ningún documento no autenticado, así que no "
        "hay forma de determinar desde fuera si se está ejecutando. No se "
        "comprueba."
    ),
    "result.scope.integrations": (
        "<strong>Si una integración de ofimática o calendario está "
        "configurada <em>correctamente</em>.</strong> Esta página solo "
        "informa de que hay un proveedor de aplicaciones registrado, o de "
        "que algo responde en la ruta CalDAV. Las reglas de compartición, "
        "los secretos WOPI y la configuración propia del segundo servicio "
        "viven todos detrás de un inicio de sesión y no se comprueban."
    ),
    "result.tls.kicker": "Transporte",
    "result.tls.heading": "Seguridad del transporte",
    "result.tls.lede": (
        "Lo que dijo la capa TLS antes de intercambiar un solo byte de HTTP. "
        "Los hallazgos anteriores ya valoran esto; aquí está la medición que "
        "hay detrás."
    ),
    "result.tls.protocol": "Protocolo",
    "result.tls.bits": "({bits} bits)",
    "result.tls.deprecated": "Versiones obsoletas",
    "result.tls.deprecated.accepted": "Todavía aceptadas: {list}",
    "result.tls.deprecated.refused": "Rechazadas: {list}",
    "result.tls.chain": "Cadena",
    "result.tls.chain.trusted": "De confianza",
    "result.tls.chain.not_established": "No establecida",
    "result.tls.chain.not_trusted": "No es de confianza",
    "result.tls.chain.incomplete_note": "- sin ruta hasta una raíz pública",
    "result.tls.issued_to": "Emitido para",
    "result.tls.unnamed": "sin nombre",
    "result.tls.issued_by": "Emitido por",
    "result.tls.unknown": "desconocido",
    "result.tls.valid_for": "Válido para",
    "result.tls.validity": "Validez",
    "result.tls.validity.range": "{start} a {end}",
    "result.tls.validity.expired": "- caducó hace {days} día(s)",
    "result.tls.validity.remaining": "- quedan {days} día(s)",
    "result.tls.lifetime": "Emitido por un período de",
    "result.tls.lifetime.days": "{days} día(s)",
    "result.tls.ocsp": "OCSP stapling",
    "result.tls.ocsp.stapled": "Se incluye una respuesta de revocación",
    "result.tls.ocsp.not_stapled": "No se incluye ninguna respuesta de revocación",
    "result.tls.ocsp.undetermined": "No determinado",
    "result.raw.kicker": "Datos en bruto",
    "result.raw.heading": "Detalles técnicos",
    "result.raw.lede": "El documento de resultado completo, tal como lo ve el complemento.",
    "result.raw.summary": "Mostrar el JSON en bruto",
    "result.export.kicker": "Exportar",
    "result.export.heading": "Llévate este resultado",
    "result.export.lede": (
        "El mismo análisis, presentado de cuatro formas distintas. Cada una "
        "se genera cuando la solicitas y desaparece junto con el propio "
        "análisis."
    ),
    "result.export.pdf": "Informe en PDF",
    "result.export.pdf.hint": "Para un ticket, una revisión o una copia impresa.",
    "result.export.csv": "CSV",
    "result.export.csv.hint": "Una fila por hallazgo, para una hoja de cálculo.",
    "result.export.sarif": "SARIF",
    "result.export.sarif.hint": "Para un panel de análisis de código.",
    "result.export.json": "JSON",
    "result.export.json.hint": "El documento en bruto que evalúa el complemento.",
    "result.export.passed.heading": "Lo que ya ha pasado",
    "result.export.passed.note": (
        "Estas comprobaciones salieron limpias, así que no están en el plan de arriba."
    ),
    "result.share.kicker": "Compartir",
    "result.share.heading": "Compartir este informe",
    "result.share.lede": "Copie el enlace o un resumen, o abra un borrador en su cliente de correo. Este servicio no envía el informe por usted.",
    "result.share.warning": "Cualquier persona con este enlace puede leer el informe hasta que caduque. Al publicarlo en un canal, también da acceso a sus participantes y a los servicios de vista previa. Comparta solo el resumen si no desea dar acceso al informe.",
    "result.share.email": "Compartir por correo",
    "result.share.email.hint": "Abre un mensaje preparado en su programa de correo. Solo se envía cuando lo confirme allí.",
    "result.share.email.subject": "Informe de seguridad de OpenCloud para {target}",
    "result.share.email.body": (
        "Este es el informe de seguridad de nuestra instancia de OpenCloud:\n\n"
        "{url}\n\n"
        "Este enlace es lo que da acceso al informe, así que trátalo como una "
        "contraseña. Caduca por sí solo y después la página deja de existir."
    ),
    "result.share.link": "Copiar enlace",
    "result.share.link.hint": (
        "La dirección de esta página. Quien la reciba puede abrir el informe."
    ),
    "result.share.summary": "Copiar resumen",
    "result.share.summary.hint": (
        "Los hallazgos como texto, sin ningún enlace. Lo más seguro para pegar "
        "en un canal de chat."
    ),
    "result.share.summary.body": (
        "Informe de seguridad de OpenCloud - {domain}\n"
        "Nota {label} ({rating} de 5)\n"
        "Críticos {critical} | Avisos {warning} | Info {info} | "
        "Alertas {advisories} | Superados {passed}\n"
        "Medido con check-opencloud-security."
    ),
    "result.share.done": "Copiado",
    "result.share.failed": "No se ha podido copiar",
    "result.share.fallback": "La dirección de este informe:",
    "result.feedback.prompt": "¿Crees que el análisis se ha equivocado?",
    "result.feedback.link": "Informa de un falso positivo o un falso negativo",
    "result.expiry.one": (
        "Esta página caduca en aproximadamente 1 minuto; a partir de "
        "entonces el enlace deja de funcionar y el resultado desaparece."
    ),
    "result.expiry.many": (
        "Esta página caduca en aproximadamente {minutes} minutos; a partir "
        "de entonces el enlace deja de funcionar y el resultado desaparece."
    ),
    "result.expiry.warning.one": "Este informe desaparece en aproximadamente 1 minuto.",
    "result.expiry.warning.many": (
        "Este informe desaparece en aproximadamente {minutes} minutos."
    ),
    "result.expiry.warning.action": "Descargue una copia para conservar el informe",
    "result.expiry.gone": (
        "Este informe ha caducado. El enlace y sus descargas ya no funcionan."
    ),
    # ----------------------------------------- transport facts beside the grade
    "tls.fact.protocol": "Versión de TLS",
    "tls.fact.protocol.detail": "también acepta {list}",
    "tls.fact.expiry": "El certificado caduca",
    "tls.fact.expiry.expired": "caducó hace {days} día(s)",
    "tls.fact.expiry.remaining": "quedan {days} día(s)",
    "tls.fact.chain": "Cadena",
    "tls.fact.chain.incomplete": "Incompleta",
    "tls.fact.chain.incomplete.detail": "sin ruta hasta una raíz pública",
    "tls.fact.chain.untrusted": "No es de confianza",
    "tls.fact.chain.untrusted.detail": "autofirmado, o de una autoridad desconocida",
    "tls.fact.chain.unknown": "No establecida",
    "tls.fact.chain.unknown.detail": "el saludo TLS nunca llegó al certificado",
    "tls.fact.chain.ok": "Completa y de confianza",
}
