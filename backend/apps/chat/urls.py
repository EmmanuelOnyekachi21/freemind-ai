'''
CHAT URL CONFIGURATION
'''

from django.urls import path
from apps.chat import views

urlpatterns = [
    # Main chat endpoint
    path('', views.send_message, name='send_message'),
    path('history/', views.get_chat_history, name='chat_history'),
    path(
        'history/delete/',
        views.delete_chat_history,
        name='delete_chat_history'
    )
]