from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def healthcheck(request):
    return JsonResponse({"status": "ok", "service": "nexus-framework"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('nexus.api_urls')),
    path('', healthcheck),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
