from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import (
    ClientOrderViewSet, DispatcherOrderViewSet,
    DriverViewSet, VehicleViewSet,
    RegisterView, LoginView,
    CityViewSet,
    DispatcherShipmentViewSet,
    ClientShipmentViewSet
)
from rest_framework.authtoken import views as drf_auth_views
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from drf_spectacular.utils import extend_schema

router = DefaultRouter()

router.register(r'client/orders', ClientOrderViewSet, basename='client-orders')
router.register(r'dispatcher/orders', DispatcherOrderViewSet, basename='dispatcher-orders')
router.register(r'drivers', DriverViewSet)
router.register(r'vehicles', VehicleViewSet)
router.register(r'cities', CityViewSet)
router.register(r'dispatcher/shipments', DispatcherShipmentViewSet, basename='dispatcher-shipments')
router.register(r'client/shipments', ClientShipmentViewSet, basename='client-shipments')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', LoginView.as_view(), name='login'),
    #path('api-token-auth/', drf_auth_views.obtain_auth_token),
    # Swagger:
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

