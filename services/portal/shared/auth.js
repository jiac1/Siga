/* Suite UNAB — autenticación del front-end estático.

   Modo suite: la sesión real vive en el servicio core (cookie HttpOnly
   `suite_sso`, invisible para JS). Aquí solo se consulta /auth/me y se guarda
   una copia NO sensible del perfil (nombre, institución, módulos) para pintar
   la interfaz sin esperar a la red.

   Modo independiente: si core no existe (app publicada sola), se mantiene la
   sesión de demostración original basada en localStorage. No es seguridad:
   las apps estáticas procesan los archivos del usuario en su propio navegador
   y no exponen datos del servidor.

   API pública (compatible con el prototipo):
     SuiteAuth.ready            -> Promise<{modo, usuario}>
     SuiteAuth.getUser()        -> {nombre, email, organizacion, modulos} | null
     SuiteAuth.isLoggedIn()
     SuiteAuth.login(nombre)    (solo modo independiente)
     SuiteAuth.logout()
     SuiteAuth.requireLogin({modulo})
     SuiteAuth.modo()           -> "suite" | "standalone" (tras ready)          */
(function () {
  const CFG = window.SUITE_CONFIG || { modo: "auto", coreApi: "/core/api/v1",
    loginUrl: "/core/ingresar/", logoutUrl: "/core/salir/" };
  const KEY = "suite-unab-session";
  let modoActual = null;

  function raiz(archivo) {
    return "../".repeat(window.SUITE_APP_DEPTH || 0) + archivo;
  }
  function leer() {
    try { return JSON.parse(localStorage.getItem(KEY)); } catch (e) { return null; }
  }
  function guardar(perfil) {
    try { localStorage.setItem(KEY, JSON.stringify(perfil)); } catch (e) { /* modo privado */ }
  }
  function borrar() {
    try { localStorage.removeItem(KEY); } catch (e) { /* modo privado */ }
  }

  async function detectar() {
    if (CFG.modo === "standalone") return { modo: "standalone", usuario: leer() };
    try {
      const r = await fetch(CFG.coreApi + "/auth/me", {
        credentials: "include", headers: { Accept: "application/json" }, cache: "no-store"
      });
      if (r.ok) {
        const u = await r.json();
        const perfil = {
          nombre: u.nombre, email: u.email, rol: u.rol,
          organizacion: u.organizacion ? u.organizacion.nombre : "",
          modulos: u.modulos || [], suite: true, ts: Date.now()
        };
        guardar(perfil);
        return { modo: "suite", usuario: perfil };
      }
      if (r.status === 401 || r.status === 403) {
        const previo = leer();
        if (previo && previo.suite) borrar();   // la sesión SSO expiró
        return { modo: "suite", usuario: null };
      }
    } catch (e) { /* sin red o sin core: modo independiente */ }
    if (CFG.modo === "suite") return { modo: "suite", usuario: null };
    const local = leer();
    return { modo: "standalone", usuario: local && !local.suite ? local : null };
  }

  const ready = detectar().then((res) => { modoActual = res.modo; return res; });

  function irALogin() {
    if (modoActual === "suite") {
      const next = encodeURIComponent(location.pathname + location.search);
      location.href = CFG.loginUrl + "?next=" + next;
    } else {
      location.href = raiz("login.html");
    }
  }

  function bloquear(modulo) {
    const capa = document.createElement("div");
    capa.setAttribute("role", "alertdialog");
    capa.style.cssText = "position:fixed;inset:0;z-index:2000;background:rgba(16,35,56,.82);display:flex;" +
      "align-items:center;justify-content:center;padding:16px;font-family:Segoe UI,system-ui,sans-serif";
    capa.innerHTML = '<div style="background:#fff;border-radius:14px;max-width:440px;padding:28px">' +
      '<h2 style="margin:0 0 8px;font-size:19px;color:#102338">Módulo no habilitado</h2>' +
      '<p style="color:#566276;line-height:1.5;margin:0 0 16px">Tu institución no tiene licencia para este módulo ' +
      '(<b>' + modulo + '</b>) o tu rol no permite usarlo.</p>' +
      '<a href="' + raiz("index.html") + '" style="background:#102338;color:#fff;text-decoration:none;' +
      'padding:10px 16px;border-radius:8px;font-weight:600">Volver a mis aplicaciones</a></div>';
    document.body.appendChild(capa);
  }

  window.SuiteAuth = {
    ready,
    modo() { return modoActual; },
    isLoggedIn() { return leer() !== null; },
    getUser() { return leer(); },
    login(nombre) {
      guardar({ nombre: nombre, suite: false, ts: Date.now() });
    },
    logout() {
      const eraSuite = (leer() || {}).suite || modoActual === "suite";
      borrar();
      location.href = eraSuite ? CFG.logoutUrl : raiz("login.html");
    },
    _rootPath: raiz,
    /* Protege la página. Si hay copia local se muestra de inmediato y la
       sesión se confirma en segundo plano. */
    requireLogin(opciones) {
      const modulo = opciones && opciones.modulo;
      ready.then(({ modo, usuario }) => {
        if (!usuario) return irALogin();
        if (modo === "suite" && modulo && usuario.modulos.indexOf(modulo) === -1) {
          const pintar = () => bloquear(modulo);
          if (document.body) pintar(); else document.addEventListener("DOMContentLoaded", pintar);
        }
      });
    }
  };
})();
