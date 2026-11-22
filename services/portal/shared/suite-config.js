/* SIGA-DSS — configuración del front-end.

   modo:
     "auto"        detecta si existe el servicio core (Suite completa) y, si no,
                   funciona como app independiente con sesión de demostración.
     "suite"       exige el inicio de sesión único de core.
     "standalone"  nunca contacta a core (útil para publicar una app suelta).

   En AWS este archivo puede reemplazarse en el despliegue (S3) sin recompilar
   nada; las páginas solo leen window.SUITE_CONFIG. */
window.SUITE_CONFIG = Object.assign({
  modo: "auto",
  coreApi: "/core/api/v1",
  loginUrl: "/core/ingresar/",
  logoutUrl: "/core/salir/",
  // Módulos con backend propio. Detrás del gateway viven bajo el mismo dominio;
  // en modo independiente (cada app en su puerto) se usan estas URLs.
  modulos: {
    "mapa-calor":   { suite: "/mapa-calor/",   independiente: "http://127.0.0.1:8792/" },
    "estres-malla": { suite: "/estres-malla/", independiente: "http://127.0.0.1:8793/" }
  }
}, window.SUITE_CONFIG || {});
