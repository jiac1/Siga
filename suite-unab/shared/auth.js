/* Suite UNAB — capa de autenticación (placeholder)
   NOTA IMPORTANTE: esto es un stub para el MVP de tesis. No es seguridad real:
   solo guarda un flag en localStorage. Está aislado en este único archivo a
   propósito, para que reemplazarlo por SSO institucional real (fase 2) no
   requiera tocar el resto de la Suite ni de las apps integradas. */
(function () {
  const KEY = "suite-unab-session";

  window.SuiteAuth = {
    isLoggedIn() {
      return localStorage.getItem(KEY) !== null;
    },
    getUser() {
      try { return JSON.parse(localStorage.getItem(KEY)); }
      catch { return null; }
    },
    login(nombre) {
      localStorage.setItem(KEY, JSON.stringify({ nombre, ts: Date.now() }));
    },
    logout() {
      localStorage.removeItem(KEY);
      window.location.href = SuiteAuth._rootPath("login.html");
    },
    /* Calcula la ruta relativa a la raíz de la suite (index.html/login.html)
       según cuántos niveles bajo /apps/ esté la página actual. */
    _rootPath(file) {
      const depth = (window.SUITE_APP_DEPTH || 0);
      return "../".repeat(depth) + file;
    },
    /* Redirige a login si no hay sesión. Llamar al inicio de cada página protegida. */
    requireLogin() {
      if (!this.isLoggedIn()) {
        window.location.href = this._rootPath("login.html");
      }
    }
  };
})();
