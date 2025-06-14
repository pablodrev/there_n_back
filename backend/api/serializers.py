# backend/yourapp/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .models import Order, City, Driver, Vehicle, Shipment, CustomUser

User = get_user_model()

## Users

# class UserRegistrationSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True)
#     class Meta:
#         model = User
#         fields = ('email', 'username', 'password', 'role', 'first_name', 'last_name')
#     def create(self, validated_data):
#         password = validated_data.pop('password')
#         user = User(**validated_data)
#         user.set_password(password)
#         user.save()
#         # При желании: автоматически создать профиль, если нужны дополнительные модели
#         from rest_framework.authtoken.models import Token
#         Token.objects.create(user=user)
#         return user

# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ('id', 'email', 'username', 'role', 'first_name', 'last_name')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'password', 'role', 'first_name', 'last_name')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        Token.objects.create(user=user)
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


## Orders

class OrderSerializer(serializers.ModelSerializer):
    # Для клиента: только создание и просмотр
    class Meta:
        model = Order
        fields = ('order_id', 'weight', 'volume', 'status', 'city_from', 'city_to', 'created_at')
        read_only_fields = ('order_id', 'status', 'created_at')

    def create(self, validated_data):
        # client будет установлен в ViewSet.perform_create
        return super().create(validated_data)

class DispatcherOrderSerializer(serializers.ModelSerializer):
    # Поля для диспетчера: можно видеть client, city_from, city_to, weight, volume, status, driver, vehicle
    client = UserSerializer(read_only=True)
    class Meta:
        model = Order
        fields = (
            'order_id', 'client', 'weight', 'volume',
            'status', 'city_from', 'city_to',
            'dispatcher', 'created_at',
        )
        read_only_fields = (
            'order_id', 'client', 'weight', 'volume',
            'city_from', 'city_to', 'dispatcher', 'created_at'
        )

    def validate(self, data):
        order = self.instance
        # Разрешаем менять статус только из Pending в Confirmed/Cancelled
        if order:
            old_status = order.status
            new_status = data.get('status', old_status)
            if old_status == Order.StatusChoices.PENDING:
                if new_status not in [Order.StatusChoices.CONFIRMED, Order.StatusChoices.CANCELLED, Order.StatusChoices.PENDING]:
                    raise serializers.ValidationError("Invalid status transition")
            else:
                raise serializers.ValidationError("Status cannot be changed once not Pending")
        return data

class DispatcherAcceptSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()
    driver = serializers.UUIDField()
    vehicle = serializers.CharField(max_length=9)
    arrival_time = serializers.DateTimeField()
    price = serializers.DecimalField(max_digits=10, decimal_places=3)


class DispatcherRejectSerializer(serializers.Serializer):
    order_id = serializers.UUIDField()

class DispatcherDeliverSerializer(serializers.Serializer):
    shipment_id = serializers.UUIDField()

class DispatcherDelaySerializer(serializers.Serializer):
    shipment_id = serializers.UUIDField()

class DriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = '__all__'
        read_only_fields = ('driver_id', 'is_available')


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'
        read_only_fields = ('is_available',)

class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = (
            'city_id',
            'city_name',
            'latitude',
            'longitude'
        )
        read_only_fields = ('city_id',)

class DispatcherShipmentSerializer(serializers.ModelSerializer):
    driver = DriverSerializer(read_only=True)
    class Meta:
        model =  Shipment
        fields = '__all__'
        read_only_fields = (
            'shipment_id', 'order', 'driver',
            'vehicle', 'price', 'arrival_time', 'review_rating',
            'review_text', 'review_created_at'
        )

class ClientShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model =  Shipment
        fields = '__all__'
        read_only_fields = (
            'shipment_id', 'order', 'driver',
            'vehicle', 'price', 'arrival_time', 'status'
        )

