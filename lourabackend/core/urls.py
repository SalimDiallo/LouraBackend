from django.urls import path

# Exemple de vue basique pour tester l'URL routing
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok", "message": "core API up!"})

urlpatterns = [
    path('', health_check, name='health_check'),
]

