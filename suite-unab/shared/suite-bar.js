/* Suite UNAB — inyecta la barra superior compartida sin tocar el HTML/CSS/JS
   propio de cada app integrada. Requiere que la página incluya antes:
     <script>window.SUITE_APP_DEPTH = 2;</script>   // niveles bajo /apps/
     <link rel="stylesheet" href="RUTA/tokens.css">
     <link rel="stylesheet" href="RUTA/suite-bar.css">
     <script src="RUTA/auth.js"></script>
   y luego este script, pasando el nombre visible de la app:
     <script src="RUTA/suite-bar.js" data-app="Malla curricular"></script> */
(function () {
  const thisScript = document.currentScript;
  const appName = thisScript.getAttribute("data-app") || "Suite UNAB";
  const root = (depth => "../".repeat(depth))(window.SUITE_APP_DEPTH || 0);
  const user = window.SuiteAuth ? window.SuiteAuth.getUser() : null;

  const bar = document.createElement("div");
  bar.id = "suite-bar";
  bar.innerHTML = `
    <div class="suite-bar-left">
      <a class="suite-bar-brand" href="${root}index.html">
        <span class="dot"></span>Suite UNAB
      </a>
      <span class="suite-bar-sep">/</span>
      <span class="suite-bar-app">${appName}</span>
    </div>
    <div class="suite-bar-right">
      ${user ? `<span class="suite-bar-user">${user.nombre}</span>` : ""}
      <a class="suite-bar-link" href="${root}index.html">Inicio</a>
      <a class="suite-bar-link" href="#" id="suite-bar-logout">Salir</a>
    </div>
  `;
  document.body.insertBefore(bar, document.body.firstChild);

  const logout = bar.querySelector("#suite-bar-logout");
  if (logout) {
    logout.addEventListener("click", (e) => {
      e.preventDefault();
      if (window.SuiteAuth) window.SuiteAuth.logout();
    });
  }
})();
