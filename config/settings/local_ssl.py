from .local import *  # noqa: F403

ALLOWED_HOSTS += [f"{DEFAULT_HOST}.{PROJECT_DOMAIN}", f"{API_HOST}.{PROJECT_DOMAIN}"]  # noqa: F405
