from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView  # ✅ required for redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('inventory/', include('inventory.urls')),

    # ✅ Redirect root URL '/' to '/inventory/login/'
    path('', RedirectView.as_view(url='/inventory/login/', permanent=False)),
]
