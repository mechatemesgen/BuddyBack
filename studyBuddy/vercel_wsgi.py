import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "studyBuddy.settings")  # change to your actual settings module

app = get_wsgi_application()
