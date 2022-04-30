import django

SECRET_KEY = "bananas"
LANGUAGE_CODE = "en"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
INSTALLED_APPS = [
    "bananas",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "tests",
]
ROOT_URLCONF = "tests.urls"
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
STATIC_URL = "/static/"
MEDIA_URL = "/media/"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": True,
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.AcceptHeaderVersioning",
    "DEFAULT_VERSION": 1.0,
    "ALLOWED_VERSIONS": [1.0],
}


def pytest_configure(config):
    from django.conf import settings

    settings.configure(
        SECRET_KEY=SECRET_KEY,
        LANGUAGE_CODE=LANGUAGE_CODE,
        DATABASES=DATABASES,
        INSTALLED_APPS=INSTALLED_APPS,
        ROOT_URLCONF=ROOT_URLCONF,
        MIDDLEWARE=MIDDLEWARE,
        STATIC_URL=STATIC_URL,
        MEDIA_URL=MEDIA_URL,
        TEMPLATES=TEMPLATES,
        USE_TZ=USE_TZ,
        DEFAULT_AUTO_FIELD=DEFAULT_AUTO_FIELD,
    )

    django.setup()
