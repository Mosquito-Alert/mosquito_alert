from .local import *

ALLOWED_HOSTS += [
    f'{DEFAULT_HOST}.{PROJECT_DOMAIN}',
    f'{API_HOST}.{PROJECT_DOMAIN}'
]