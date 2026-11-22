/* =========================================================================
   Convalidación UNAB — modo "malla de origen" y envío de la solicitud.

   1) El postulante elige su universidad y carrera de origen desde el
      catálogo de la Suite (27 mallas oficiales de universidades de Santiago)
      y marca las asignaturas que aprobó. Sin PDF.
   2) El puntaje combina el motor por contenidos original con conceptos
      curriculares curados y similitud de nombres (port exacto del motor del
      servidor: services/core/convalidaciones/motor.py).
   3) Si la Suite está conectada, la solicitud se envía a la Dirección de
      Carrera (servicio core) y el postulante recibe un folio.

   Depende de funciones del motor definidas en convalidacion.html:
   tokenizar, quitarAcentos, evaluar, nivelDe, esc, toast, $.
   ========================================================================= */
(function () {
  const RUTA_DATOS = "../../shared/data/";
  const UMBRAL_REVISION_NOMBRE = 0.35;
  const PESO_CONCEPTO = 0.9, PESO_NOMBRE = 0.7, PESO_CONTENIDO = 0.3, PENALIZACION_NIVEL = 0.6;

  const estado = { modo: "catalogo", indice: null, malla: null, conceptos: null, reglas: [] };

  /* ---- Normalización y conceptos (idéntico al servidor) ---------------- */
  const RE_SUFIJOS = /\s+para\s+(ingenieria|informatica|obras civiles)(\s+(electrica|en minas|informatica))?\b/g;
  function normalizarNombre(n) {
    let s = quitarAcentos(String(n || "").toLowerCase());
    s = s.replace(/\([^)]*\)/g, " ").replace(RE_SUFIJOS, " ").replace(/[^a-z0-9ñ/, ]/g, " ");
    return s.replace(/\s+/g, " ").trim().replace(/^[ ,]+|[ ,]+$/g, "");
  }
  function conceptosDe(nombre) {
    const n = normalizarNombre(nombre), out = new Set();
    for (const [clave, patrones] of estado.reglas) if (patrones.some((p) => p.test(n))) out.add(clave);
    return out;
  }
  function similitudNombres(a, b, idf) {
    const ta = new Set(tokenizar(normalizarNombre(a))), tb = new Set(tokenizar(normalizarNombre(b)));
    if (!ta.size || !tb.size) return 0;
    let tope = 1; for (const v of idf.values()) if (v > tope) tope = v;
    const peso = (t) => (idf.has(t) ? idf.get(t) : tope);
    let comun = 0, sa = 0, sb = 0;
    for (const t of ta) { sa += peso(t); if (tb.has(t)) comun += peso(t); }
    for (const t of tb) sb += peso(t);
    return (2 * comun) / (sa + sb);
  }
  function puntajePorNombre(concepto, sim, contenido) {
    const porConcepto = concepto ? PESO_CONCEPTO + (1 - PESO_CONCEPTO) * sim : 0;
    return Math.max(porConcepto, PESO_NOMBRE * sim + PESO_CONTENIDO * contenido);
  }

  /* Evaluación combinada: misma semántica que motor.evaluar_asignatura(). */
  function evaluarCombinado(nombre, texto, indice) {
    const ranking = evaluar(((nombre || "") + " " + (texto || "")).trim(), indice);
    const cOrigen = conceptosDe(nombre), nOrigen = nivelDe(nombre);
    for (const r of ranking) {
      const cDestino = r.asig._conceptos || (r.asig._conceptos = conceptosDe(r.asig.nombre));
      const comun = [...cOrigen].some((c) => cDestino.has(c));
      const sim = similitudNombres(nombre, r.asig.nombre, indice.idf);
      r.score = Math.max(r.score, puntajePorNombre(comun, sim, r.score));
      const nDestino = nivelDe(r.asig.nombre);
      if (nOrigen != null && nDestino != null && nOrigen !== nDestino) r.score *= PENALIZACION_NIVEL;
      if (comun && !r.matched.length) r.matched = [...cOrigen].filter((c) => cDestino.has(c));
    }
    ranking.sort((a, b) => b.score - a.score);
    return ranking;
  }

  /* ---- Carga del catálogo ------------------------------------------------ */
  async function cargarJSON(ruta) {
    const r = await fetch(RUTA_DATOS + ruta);
    if (!r.ok) throw new Error("HTTP " + r.status + " " + ruta);
    return r.json();
  }
  async function iniciarCatalogo() {
    const [indice, conceptos] = await Promise.all([
      cargarJSON("universidades/index.json"), cargarJSON("convalidacion/conceptos.json")]);
    estado.indice = indice;
    estado.conceptos = conceptos;
    estado.reglas = Object.entries(conceptos.conceptos).map(([k, c]) => [k, c.patrones.map((p) => new RegExp(p))]);
    const selU = $("selUni");
    const unis = [...new Map(indice.map((m) => [m.sigla, m.universidad])).entries()]
      .sort((a, b) => a[1].localeCompare(b[1], "es"));
    selU.innerHTML = '<option value="">Selecciona tu universidad…</option>' +
      unis.map(([s, n]) => `<option value="${esc(s)}">${esc(n)}</option>`).join("") +
      '<option value="__otra">Mi universidad no está en la lista</option>';
  }

  function poblarCarrerasOrigen() {
    const sigla = $("selUni").value, selC = $("selCarreraOrigen");
    estado.malla = null; pintarMalla();
    $("otraUni").hidden = sigla !== "__otra";
    selC.disabled = !sigla || sigla === "__otra";
    const carreras = estado.indice.filter((m) => m.sigla === sigla);
    selC.innerHTML = '<option value="">Selecciona tu carrera…</option>' +
      carreras.map((m) => `<option value="${esc(m.slug)}">${esc(m.carrera)}${m.plan ? " · " + esc(m.plan) : ""}</option>`).join("");
    if (sigla === "__otra") toast("Usa la opción «Subir programas en PDF» para evaluar con tus programas de asignatura.");
    actualizarBoton();
  }

  async function elegirCarreraOrigen() {
    const slug = $("selCarreraOrigen").value;
    estado.malla = slug ? await cargarJSON("universidades/" + slug + ".json") : null;
    pintarMalla();
  }

  function pintarMalla() {
    const cont = $("mallaOrigen"), fuente = $("fuenteOrigen");
    if (!estado.malla) { cont.innerHTML = ""; fuente.innerHTML = ""; actualizarBoton(); return; }
    const m = estado.malla;
    fuente.innerHTML = `Fuente oficial: <a href="${esc(m.fuente.url)}" target="_blank" rel="noopener">${esc(m.universidad)}</a>` +
      ` · consultada el ${esc(m.fuente.consultado)}${m.regimen !== "semestral" ? " · régimen " + esc(m.regimen) : ""}`;
    const etiqueta = m.regimen && m.regimen.indexOf("trimestral") === 0 ? "Trimestre" : "Semestre";
    cont.innerHTML = m.semestres.map((s) => {
      const asigs = s.asignaturas.filter((a) => !a.generico);
      if (!asigs.length) return "";
      return `<fieldset class="sem"><legend>${etiqueta} ${s.numero}
          <button type="button" class="sem-todo" data-sem="${s.numero}">marcar hasta aquí</button></legend>` +
        asigs.map((a) => `<label class="asig"><input type="checkbox" value="${esc(a.id)}" data-sem="${s.numero}">
          <span>${esc(a.nombre)}${a.codigo ? ` <small>${esc(a.codigo)}</small>` : ""}</span></label>`).join("") +
        "</fieldset>";
    }).join("");
    cont.querySelectorAll("input[type=checkbox]").forEach((c) => c.addEventListener("change", actualizarBoton));
    cont.querySelectorAll(".sem-todo").forEach((b) => b.addEventListener("click", () => {
      const tope = Number(b.dataset.sem);
      cont.querySelectorAll("input[type=checkbox]").forEach((c) => { c.checked = Number(c.dataset.sem) <= tope; });
      actualizarBoton();
    }));
    actualizarBoton();
  }

  function asignaturasMarcadas() {
    if (!estado.malla) return [];
    const ids = new Set([...document.querySelectorAll("#mallaOrigen input:checked")].map((c) => c.value));
    return estado.malla.semestres.flatMap((s) => s.asignaturas).filter((a) => ids.has(a.id))
      .map((a) => ({ nombre: a.nombre, texto: "", archivo: null, catalogoId: a.id }));
  }

  /* ---- Cambio de modo ---------------------------------------------------- */
  function cambiarModo(modo) {
    estado.modo = modo;
    document.querySelectorAll(".modo-tab").forEach((t) => {
      const on = t.dataset.modo === modo;
      t.classList.toggle("on", on); t.setAttribute("aria-selected", String(on));
    });
    $("panelCatalogo").hidden = modo !== "catalogo";
    $("stepPDF").hidden = modo !== "pdf";
    actualizarBoton();
  }

  /* ---- Envío a la Dirección de Carrera ---------------------------------- */
  function slugCarreraUnab(nombre) {
    return "unab-" + String(nombre).normalize("NFKD").replace(/[̀-ͯ]/g, "")
      .toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  }

  async function coreDisponible() {
    const cfg = window.SUITE_CONFIG;
    if (!cfg || cfg.modo === "standalone") return false;
    try {
      const r = await fetch(cfg.coreApi + "/modulos", { headers: { Accept: "application/json" } });
      return r.ok;
    } catch (e) { return false; }
  }

  async function bloqueEnvio(evals, carrera, cont) {
    if (!(await coreDisponible())) return;
    const p = leerPostulante();
    const caja = document.createElement("section");
    caja.className = "envio";
    if (!p) {
      caja.innerHTML = `<h3>¿Quieres que la Dirección de Carrera revise tu caso?</h3>
        <p>Para enviar una solicitud formal primero debes identificarte.</p>
        <a class="btn" href="index.html">Identificarme</a>`;
      cont.appendChild(caja);
      return;
    }
    caja.innerHTML = `<h3>Enviar solicitud a la Dirección de Carrera</h3>
      <p>Enviaremos tu pre-evaluación a la Dirección de Carrera de <b>${esc(carrera)}</b>.
      Recibirás un folio para consultar el estado. Se usarán tus datos solo para gestionar esta solicitud.</p>
      <button type="button" class="btn" id="btnEnviar">Enviar solicitud</button>
      <div class="envio-res" id="envioRes" aria-live="polite"></div>`;
    cont.appendChild(caja);
    $("btnEnviar").addEventListener("click", async () => {
      const btn = $("btnEnviar"); btn.disabled = true; btn.textContent = "Enviando…";
      const cuerpo = {
        tipo_documento: p.tipoDoc, documento: p.documento, nombres: p.nombres, apellidos: p.apellidos,
        correo: p.correo, telefono: p.telefono || "", consentimiento: !!p.consentimiento,
        carrera_destino: slugCarreraUnab(carrera),
        carrera_origen: estado.modo === "catalogo" && estado.malla ? estado.malla.slug : null,
        institucion_origen_texto: estado.modo === "pdf" ? ($("otraUniTexto") ? $("otraUniTexto").value : "") : "",
        certificado_verificacion: (typeof certVerif !== "undefined" && certVerif) || {},
        asignaturas: evals.map(({ prog, nota }) => ({
          nombre: prog.nombre, texto: (prog.texto || "").slice(0, 8000),
          nota: nota ? nota.nota.toFixed(1) : null, aprobada: nota ? !!nota.aprobado : null
        }))
      };
      try {
        const r = await fetch(window.SUITE_CONFIG.coreApi + "/convalidaciones/solicitudes", {
          method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify(cuerpo)
        });
        const datos = await r.json();
        if (!r.ok) throw new Error(datos.detail || JSON.stringify(datos));
        $("envioRes").innerHTML = `<div class="folio">Solicitud registrada · folio <b>${esc(datos.folio)}</b></div>
          <p>Te enviamos un comprobante a ${esc(p.correo)}. La Dirección de Carrera revisará cada asignatura.</p>`;
        btn.textContent = "Enviada";
      } catch (e) {
        console.error(e);
        $("envioRes").textContent = "No se pudo enviar la solicitud. Intenta nuevamente en unos minutos.";
        btn.disabled = false; btn.textContent = "Reintentar";
      }
    });
  }

  window.ConvalCatalogo = {
    estado, iniciarCatalogo, poblarCarrerasOrigen, elegirCarreraOrigen, asignaturasMarcadas,
    cambiarModo, evaluarCombinado, bloqueEnvio,
    umbralRevision: () => (estado.modo === "catalogo" ? UMBRAL_REVISION_NOMBRE : UMBRAL_REVISION)
  };
})();
