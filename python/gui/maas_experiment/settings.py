"""
Django settings for maas_experiment project.

Generated by 'django-admin startproject' using Django 2.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

from .application_values import *
from .logging import *

BASE_DIR = BASE_DIRECTORY


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY",'cm_v*vc*8s048%f46*@t7)hb9rtaa@%)#b!s(+$4+iw^tjt=s6')

# Must be set in production!
ALLOWED_HOSTS = ['*']

# The default is false; if it's not true, it will leave a user logged in indefinitely
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# This is the absolute age; navigating won't necessarily tell the system that anything is happening
# and sessions will absolutely end after this time, regardless of what is going on.
# In this case, you will be logged off after 5 minutes even if you were actively working.
# SESSION_COOKIE_AGE = 300

# security.W007: Activate's the browser's XSS filtering to help prevent XSS attacks
SECURE_BROWSER_XSS_FILTER = True

# Whether to use a secure cookie for the session cookie. If this is set to True, the cookie will be marked as
# “secure”, which means browsers may ensure that the cookie is only sent under an HTTPS connection.
# Leaving this setting off isn’t a good idea because an attacker could capture an unencrypted session cookie with a
# packet sniffer and use the cookie to hijack the user’s session.
SESSION_COOKIE_SECURE = not DEBUG

# Whether to use a secure cookie for the CSRF cookie. If this is set to True, the cookie will be marked as “secure”,
# which means browsers may ensure that the cookie is only sent with an HTTPS connection.
CSRF_COOKIE_SECURE = not DEBUG

# Whether to store the CSRF token in the user’s session instead of in a cookie.
# It requires the use of django.contrib.sessions.
#
# Storing the CSRF token in a cookie (Django’s default) is safe, but storing it in the session is common practice
# in other web frameworks and therefore sometimes demanded by security auditors.
CSRF_USE_SESSIONS = not DEBUG

# security.W019: Unless we start serving data in a frame, set to 'DENY'
X_FRAME_OPTIONS = 'DENY'


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'MaaS.apps.MaasConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'maas_experiment.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'maas_experiment.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = CURRENT_TIMEZONE

USE_I18N = True

USE_L10N = True

USE_TZ = True

DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static/")
NGEN_STATIC_ROOT = os.path.join(STATIC_ROOT, "ngen/")
HYDROFABRIC_ROOT = os.path.join(NGEN_STATIC_ROOT, "hydrofabric/")
DATA_CACHE_DIR = os.path.join(STATIC_ROOT, "cache/")
DATA_DOWNLOADS_DIR = os.path.join(DATA_CACHE_DIR, "downloads/")
DATA_UPLOADS_DIR = os.path.join(DATA_CACHE_DIR, "uploads/")
SECRETS_ROOT = '/run/secrets/'


MINIO_HOSTNAME = os.environ.get("OBJECT_STORE_HOSTNAME")
MINIO_PORT = os.environ.get("OBJECT_STORE_PORT")
MINIO_HOST_STRING = "{}:{}".format(MINIO_HOSTNAME, MINIO_PORT)

MINIO_ACCESS_DOCKER_SECRET_NAME = 'object_store_exec_user_name'
MINIO_SECRET_DOCKER_SECRET_NAME: str = 'object_store_exec_user_passwd'

MINIO_ACCESS_FILE = os.path.join(SECRETS_ROOT, MINIO_ACCESS_DOCKER_SECRET_NAME)
MINIO_SECRET_FILE = os.path.join(SECRETS_ROOT, MINIO_SECRET_DOCKER_SECRET_NAME)

# TODO adjust this to be configurable
MINIO_SECURE_CONNECT = False


def ensure_required_environment_variables():
    missing_variables = [
        variable_name
        for variable_name in REQUIRED_ENVIRONMENT_VARIABLES
        if variable_name['name'] not in os.environ.keys()
    ]

    if missing_variables:
        missing_keys = [
            variable['name']
            for variable in missing_variables
        ]

        error("The following required environment variables are missing:")

        for missing_variable in missing_variables:
            error(f"{missing_variable['name']}: {missing_variable['purpose']}")

        raise ValueError(f"The following environment variables have not been set: [{', '.join(missing_keys)}]")


ensure_required_environment_variables()

