import uuid
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


class CustomUser(AbstractUser):
    class RoleChoices(models.TextChoices):
        CLIENT = 'client', 'Client'
        DISPATCHER = 'dispatcher', 'Dispatcher'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=RoleChoices.choices)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    def __str__(self):
        return f"{self.email} ({self.role})"


class City(models.Model):
    city_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    city_name = models.CharField(
        max_length=50
    )
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6
    )
    longitude = models.DecimalField(
        max_digits=8, decimal_places=6
    )
    class Meta:
        verbose_name = 'City'
        verbose_name_plural = 'Cities'

    def __str__(self):
        return f"City {self.city_name} at {self.latitude} {self.longitude}"


class Order(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'Pending'
        CANCELLED = 'Cancelled'
        CONFIRMED = 'Confirmed'

    order_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    volume = models.DecimalField(max_digits=10, decimal_places=3)
    status = models.CharField(
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
        limit_choices_to={'role': CustomUser.RoleChoices.CLIENT}
    )
    dispatcher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_orders',
        null=True,
        blank=True,
        limit_choices_to={'role': CustomUser.RoleChoices.DISPATCHER}
    )
    city_from = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name='orders_from',
    )
    city_to = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name='orders_to',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f"Order {self.order_id} by {self.client}"


class Vehicle(models.Model):
    license_plate = models.CharField(
        max_length=9,
        primary_key=True
    )
    transport_type = models.CharField(
        max_length=3,
    )
    max_volume = models.IntegerField()
    max_weight = models.IntegerField()
    is_available = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Vehicle'
        verbose_name_plural = 'Vehicles'

    def __str__(self):
        return f"Vehicle {self.license_plate}"


class Driver(models.Model):
    driver_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False, 
    )
    first_name = models.CharField(
        max_length=50,
    )
    last_name = models.CharField(
        max_length=50,
    )
    second_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    B = models.BooleanField()
    BE = models.BooleanField()
    C = models.BooleanField()
    C1 = models.BooleanField()
    CE = models.BooleanField()
    C1E = models.BooleanField()
    is_available = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Driver'
        verbose_name_plural = 'Drivers'

    def __str__(self):
        return f"Driver {self.first_name} {self.last_name} ({self.driver_id})"


class Shipment(models.Model):
    class StatusChoices(models.TextChoices):
        IN_PROGRESS = 'In Progress'
        DELIVERED = 'Delivered'
        DELAYED = 'Delayed'

    shipment_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='shipment',
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.CASCADE,
        related_name='shipments',
    )
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='shipments',
    )
    arrival_time = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=3)
    status = models.CharField(
        choices=StatusChoices.choices,
        default=StatusChoices.IN_PROGRESS
    )

    review_rating = models.IntegerField(
        blank=True,
        null=True,
    )
    review_text = models.TextField(
        blank=True,
        null=True,
    )
    review_created_at = models.DateTimeField(
        blank=True,
        null=True,
        auto_now=True,
    )

    class Meta:
        verbose_name = 'Shipment'
        verbose_name_plural = 'Shipments'

    def __str__(self):
        return f"Shipment {self.shipment_id} (Order {self.order.order_id})"

