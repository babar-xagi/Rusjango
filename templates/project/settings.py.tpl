APP_NAME = "{{ project_name }}"
DEBUG = True
SECRET_KEY = "{{ secret_key }}"
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = []

MIDDLEWARE = [
    "rusjango.security.SecurityMiddleware",
]

DATABASE = None
AUTH = None
ADMIN = None
AI = None
WORKER = None
PAYMENTS = None
