/* SIGA-DSS — selector de malla existente (evita tener que descargar y
   volver a subir la malla de tu carrera cuando ya está cargada en la Suite).
   Uso:
     SuiteMallaPicker.open({
       basePath: "../../shared/mallas/",   // dónde están index.json y <slug>.json
       onSelect: (data) => { ... }         // recibe el JSON completo de la carrera
     });
   Es un widget "vanilla" sin dependencias, pensado para poder copiarse tal
   cual a una app que corra en otro origen (como estres-malla, que es Django
   y no puede enlazar directo a /shared/ en desarrollo local). */
(function () {
  let _indexCache = null;

  async function open({ basePath, onSelect }) {
    const backdrop = document.createElement("div");
    backdrop.className = "mp-backdrop";
    backdrop.innerHTML = `
      <div class="mp-modal" role="dialog" aria-modal="true" aria-label="Elegir malla existente">
        <div class="mp-head">
          <div>
            <h3>Elegir malla existente</h3>
            <p>Usa la malla de una carrera ya cargada en la Suite, sin subir un archivo.</p>
          </div>
          <button class="mp-close" aria-label="Cerrar">&#10005;</button>
        </div>
        <div class="mp-search"><input type="search" placeholder="Buscar carrera…" aria-label="Buscar carrera"></div>
        <div class="mp-list">Cargando…</div>
      </div>`;
    document.body.appendChild(backdrop);

    const close = () => backdrop.remove();
    backdrop.querySelector(".mp-close").onclick = close;
    backdrop.addEventListener("click", (e) => { if (e.target === backdrop) close(); });
    document.addEventListener("keydown", function esc(e) {
      if (e.key === "Escape") { close(); document.removeEventListener("keydown", esc); }
    });

    const listEl = backdrop.querySelector(".mp-list");
    const searchEl = backdrop.querySelector("input");

    let items;
    try {
      if (!_indexCache) {
        _indexCache = await fetch(basePath + "index.json").then(r => r.json());
      }
      items = _indexCache;
    } catch (e) {
      listEl.innerHTML = `<div class="mp-empty">No se pudo cargar el catálogo de mallas.</div>`;
      return;
    }

    function render(filter) {
      const f = (filter || "").trim().toLowerCase();
      const shown = items.filter(c => !f || c.nombre.toLowerCase().includes(f));
      if (!shown.length) {
        listEl.innerHTML = `<div class="mp-empty">Sin resultados para "${filter}".</div>`;
        return;
      }
      listEl.innerHTML = shown.map(c => `
        <button class="mp-card" data-slug="${c.slug}">
          <span class="badge">${c.badge}</span>
          <h4>${c.nombre}</h4>
          <div class="meta">${c.nCursos} asignaturas · ${c.nSemestres} semestres · ${c.totalCreditos || 0} créditos</div>
        </button>`).join("");
      listEl.querySelectorAll(".mp-card").forEach(card => {
        card.onclick = async () => {
          card.disabled = true;
          try {
            const data = await fetch(basePath + card.dataset.slug + ".json").then(r => r.json());
            close();
            onSelect(data);
          } catch (e) {
            card.disabled = false;
            alert("No se pudo cargar esa malla. Intenta de nuevo.");
          }
        };
      });
    }
    render("");
    searchEl.addEventListener("input", () => render(searchEl.value));
    searchEl.focus();
  }

  window.SuiteMallaPicker = { open };
})();
