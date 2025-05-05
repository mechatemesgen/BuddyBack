"""
ASGI config for studyBuddy project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""


import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from chat_gp.consumers import ChatConsumer  # Corrected to match your chat_gp app
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studyBuddy.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter([
        path('ws/chat/<int:group_id>/', ChatConsumer.as_asgi()),
    ]),
})