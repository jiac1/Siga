from . import conf


def suite(request):
    """Expone a las plantillas lo necesario para dibujar la barra común."""
    return {
        "suite": {
            "activa": conf.suite_activa(),
            "modo": conf.modo(),
            "modulo": conf.modulo(),
            "modulo_nombre": conf.modulo_nombre(),
            "portal_url": conf.portal_url(),
            "logout_url": conf.logout_url(),
            "usuario": getattr(request, "suite_user", None),
        }
    }
