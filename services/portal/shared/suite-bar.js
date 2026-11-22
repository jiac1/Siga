/* SIGA-DSS — barra superior compartida, inyectada sin tocar el HTML/CSS/JS
   propio de cada app. Requiere antes:
     <script>window.SUITE_APP_DEPTH = 2;</script>      // niveles bajo la raíz
     <link rel="stylesheet" href="RUTA/tokens.css">
     <link rel="stylesheet" href="RUTA/suite-bar.css">
     <script src="RUTA/suite-config.js"></script>
     <script src="RUTA/auth.js"></script>
   y luego:
     <script src="RUTA/suite-bar.js" data-app="Malla curricular"></script>    */
(function () {
  const thisScript = document.currentScript;
  const appName = thisScript.getAttribute("data-app") || "SIGA-DSS";
  const root = "../".repeat(window.SUITE_APP_DEPTH || 0);

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }

  function pintar(usuario) {
    let bar = document.getElementById("suite-bar");
    if (!bar) {
      bar = document.createElement("div");
      bar.id = "suite-bar";
      document.body.insertBefore(bar, document.body.firstChild);
    }
    const quien = usuario
      ? `<span class="suite-bar-user">${esc(usuario.nombre)}${usuario.organizacion ? " · " + esc(usuario.organizacion) : ""}</span>`
      : "";
    const salir = usuario ? `<a class="suite-bar-link" href="#" id="suite-bar-logout">Salir</a>` : "";
    bar.innerHTML = `
      <div class="suite-bar-left">
        <a class="suite-bar-brand" href="${root}index.html"><span class="dot"></span>SIGA-DSS</a>
        <span class="suite-bar-sep">/</span>
        <span class="suite-bar-app">${esc(appName)}</span>
      </div>
      <div class="suite-bar-right">
        ${quien}
        <a class="suite-bar-link" href="${root}index.html">Inicio</a>
        ${salir}
      </div>`;
    const logout = bar.querySelector("#suite-bar-logout");
    if (logout) {
      logout.addEventListener("click", (e) => {
        e.preventDefault();
        if (window.SuiteAuth) window.SuiteAuth.logout();
      });
    }
  }

  const auth = window.SuiteAuth;
  pintar(auth ? auth.getUser() : null);
  if (auth && auth.ready) auth.ready.then(({ usuario }) => pintar(usuario));
})();
