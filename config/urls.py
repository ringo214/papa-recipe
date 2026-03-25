from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('recipes.urls')), # 👈 ここでアプリの案内所を1回だけ呼ぶ
    path('', include('recipes.urls')), # 👈 これがないと recipes の中身が見つかりません！
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)