from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('home.urls')),
    path('ocr/', include('ocr.urls')),
    path('reconcile/', include('reconcile.urls')),
    path('followup_scoreboard/', include('followup_scoreboard.urls')),
    path('case_logs/', include('case_logs.urls')),
    path('applications/', include('applications.urls')),
    path('followup_tools/', include('followup_tools.urls')),
    path('accounting/', include('accounting.urls')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
