# backend/yourapp/views.py
from rest_framework import viewsets, mixins, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model, authenticate, login
from rest_framework.authtoken.models import Token

from api.models import Order, Driver, Vehicle, Shipment, City
from api.serializers import (
    OrderSerializer,
    DispatcherOrderSerializer,
    UserSerializer,
    DriverSerializer,
    VehicleSerializer,
    LoginSerializer,
    CitySerializer,
    DispatcherAcceptSerializer, DispatcherRejectSerializer
)

from .permissions import IsClient, IsDispatcher

User = get_user_model()

# class RegistrationViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
#     serializer_class = UserRegistrationSerializer
#     permission_classes = []

# class LoginViewSet(viewsets.ViewSet):
#     # Можно использовать стандартный obtain_auth_token, но если нужен кастом:
#     @action(detail=False, methods=['post'], permission_classes=[])
#     def post(self, request):
#         # предполагаем, что передаются email и password
#         from django.contrib.auth import authenticate
#         email = request.data.get('email')
#         password = request.data.get('password')
#         user = authenticate(request, username=email, password=password)
#         if not user:
#             return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
#         token, created = Token.objects.get_or_create(user=user)
#         return Response({'token': token.key})

class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'username': user.username,
            'role': user.role,
            'first_name': user.first_name,
            'last_name': user.last_name
        }, status=status.HTTP_201_CREATED)

class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'email': user.email,
                'username': user.username,
                'role': user.role,
                'first_name': user.first_name,
                'last_name': user.last_name
            })
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)


class ClientOrderViewSet(viewsets.GenericViewSet,
                         mixins.CreateModelMixin,
                         mixins.ListModelMixin,
                         mixins.RetrieveModelMixin):
    serializer_class = OrderSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsClient]

    def get_queryset(self):
        return Order.objects.filter(client=self.request.user)

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

class DispatcherOrderViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    #serializer_class = DispatcherOrderSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsDispatcher]
    queryset = Order.objects.all()

    def get_serializer_class(self):
        if self.action == 'accept':
            return DispatcherAcceptSerializer
        elif self.action == 'reject':
            return DispatcherRejectSerializer
        return DispatcherOrderSerializer

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        order = self.get_object()
        if order.status != Order.StatusChoices.PENDING:
            return Response({'error': 'Order not pending'}, status=status.HTTP_400_BAD_REQUEST)
        # ожидаем в body: driver (PK) и vehicle (PK)
        driver_id = request.data.get('driver')
        vehicle_id = request.data.get('vehicle')
        try:
            driver = Driver.objects.get(pk=driver_id)
            vehicle = Vehicle.objects.get(pk=vehicle_id)
        except (Driver.DoesNotExist, Vehicle.DoesNotExist):
            return Response({'error': 'Driver or Vehicle not found'}, status=status.HTTP_400_BAD_REQUEST)
        # Проверяем availability и лицензии:
        if not driver.is_available or not vehicle.is_available:
            return Response({'error': 'Driver or Vehicle not available'}, status=status.HTTP_400_BAD_REQUEST)
        # После проверок:
        order.status = Order.StatusChoices.CONFIRMED
        order.dispatcher = request.user
        order.save()
        # создаём Shipment
        Shipment.objects.create(order=order, driver=driver, vehicle=vehicle)
        # отмечаем их как занятые
        driver.is_available = False
        driver.save()
        vehicle.is_available = False
        vehicle.save()
        return Response({'status': Order.status})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        order = self.get_object()
        if order.status != Order.StatusChoices.PENDING:
            return Response({'error': 'Order not pending'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = Order.StatusChoices.CANCELLED
        order.dispatcher = request.user
        order.save()
        return Response({'status': Order.status})
    

class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsDispatcher]

class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsDispatcher]

class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, (IsDispatcher | IsClient)]
    # для клиента только GET

