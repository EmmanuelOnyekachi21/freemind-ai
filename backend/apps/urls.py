from django.urls import path, include

urlpatterns = [
    # The 'users' app will be accessed at /api/users/
    path('auth/', include('apps.users.urls')),

    # The 'chat' app will be accessed at /api/chat/
    path('chat/', include('apps.chat.urls')),

    # The 'interventions' app will be accessed at /api/interventions/
    # path('interventions/', include('apps.interventions.urls')),

    # ... and so on for 'screening', 'search', etc.
]