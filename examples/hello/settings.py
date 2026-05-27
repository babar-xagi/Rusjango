APP_NAME = "hello"
DEBUG = True
SECRET_KEY = "dev-only-insecure-key-change-in-production"
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "apps.school",
]
MIDDLEWARE = [
    "rusjango.security.SecurityMiddleware",
]

DATABASE = {
    "ENGINE": "sqlite",
    "NAME": "db.sqlite3",
    "ASYNC": True,
}
AUTH = None
ADMIN = None
AI = None
WORKER = None
PAYMENTS = None
