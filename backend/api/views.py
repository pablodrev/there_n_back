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
    DispatcherAcceptSerializer, DispatcherRejectSerializer,
    DispatcherShipmentSerializer, ClientShipmentSerializer
)

from .permissions import IsClient, IsDispatcher

User = get_user_model()

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
        # Проверяем availability:
        if not driver.is_available or not vehicle.is_available:
            return Response({'error': 'Driver or Vehicle not available'}, status=status.HTTP_400_BAD_REQUEST)
        arrival_time = request.data.get('arrival_time')
        price = request.data.get('price')
        # После проверок:
        order.status = Order.StatusChoices.CONFIRMED
        order.dispatcher = request.user
        order.save()
        # создаём Shipment
        Shipment.objects.create(order=order, driver=driver, vehicle=vehicle, arrival_time=arrival_time, price=price)
        # отмечаем их как занятые
        driver.is_available = False
        driver.save()
        vehicle.is_available = False
        vehicle.save()
        return Response({'status': order.status})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        order = self.get_object()
        if order.status != Order.StatusChoices.PENDING:
            return Response({'error': 'Order not pending'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = Order.StatusChoices.CANCELLED
        order.dispatcher = request.user
        order.save()
        return Response({'status': order.status})

class DispatcherShipmentViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    serializer_class = DispatcherShipmentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsDispatcher]

    def get_queryset(self):
        orders = Order.objects.filter(dispatcher=self.request.user)
        return Shipment.objects.filter(order__in=orders)
    
    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        shipment = self.get_object()
        if shipment.status != Shipment.StatusChoices.IN_PROGRESS:
            return Response({'error': f"Разрешено обновлять только доставки со статусом {Shipment.StatusChoices.IN_PROGRESS}"},
                            status=status.HTTP_400_BAD_REQUEST)
        shipment.status = Shipment.StatusChoices.DELIVERED
        shipment.save(update_fields=['status'])

        driver = shipment.order.driver
        driver.is_available = True
        driver.save(update_fields=['is_available'])

        vehicle = shipment.order.vehicle
        vehicle.is_available = True
        vehicle.save(update_fields=['is_available'])
        return Response({'status': shipment.status})

    @action(detail=True, methods=['post'])
    def delay(self, request, pk=None):
        shipment = self.get_object()
        if shipment.status != Shipment.StatusChoices.IN_PROGRESS:
            return Response({'error': f"Разрешено обновлять только доставки со статусом {Shipment.StatusChoices.IN_PROGRESS}"},
                            status=status.HTTP_400_BAD_REQUEST)
        shipment.status = Shipment.StatusChoices.DELAYED
        shipment.save()
        return Response({'status': shipment.status})
    

    # def partial_update(self, request, *args, **kwargs):
    #     # Разрешено менять только статус
    #     data = request.data
    #     if set(data.keys()) - {'status'}:
    #         return Response({'detail': 'Можно обновлять только status'}, status=status.HTTP_400_BAD_REQUEST)

    #     instance = self.get_object()
    #     new_status = request.data.get('status')
    #     valid = dict(Shipment.StatusChoices.choices).keys()
    #     if new_status not in valid:
    #         return Response({"status": "Недопустимый статус."},
    #                         status=status.HTTP_400_BAD_REQUEST)
    #     if instance.status != Shipment.StatusChoices.IN_PROGRESS:
    #         return Response({"status": f"Разрешено менять только доставки со статусом {Shipment.StatusChoices.IN_PROGRESS}"},
    #                         status=status.HTTP_400_BAD_REQUEST)
    #     instance.status = new_status
    #     instance.save(update_fields=['status'])
    #     return Response(self.get_serializer(instance).data)


class ClientShipmentViewSet(viewsets.GenericViewSet,
                            mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin):
    serializer_class = ClientShipmentSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsClient]

    def get_queryset(self):
        orders = Order.objects.filter(client=self.request.user)
        return Shipment.objects.filter(order__in=orders)
    
    def partial_update(self, request, *args, **kwargs):
        # Оставление отзыва
        data = request.data
        if set(data.keys()) - {'review_rating', 'review_text'}:
            return Response({'detail': 'Можно обновлять только review_rating и review_text.'}, status=status.HTTP_400_BAD_REQUEST)
        
        instance = self.get_object()
        if instance.status != Shipment.StatusChoices.DELIVERED:
            return Response({'detail': 'Добавлять отзывы можно только к выполненным доставкам.'}, status=status.HTTP_400_BAD_REQUEST)

        return super().partial_update(request, *args, **kwargs)
    
    

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

    def get_permissions(self):
        # для клиента только GET
        if self.action in ["list", "retrieve"]:
            permission_classes =  [(IsDispatcher | IsClient)]
        else:
            permission_classes = [IsDispatcher]
        return [perm() for perm in permission_classes]

