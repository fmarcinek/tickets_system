from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Event(models.Model):
    name = models.CharField(max_length=50)
    datetime = models.DateTimeField()


class AvailableTicket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    amount_of_tickets = models.IntegerField()
    type = models.CharField(choices=[('r', 'regular'), ('p', 'premium'), ('V', 'VIP')], max_length=1)
    price = models.DecimalField(max_digits=6, decimal_places=2)


class TicketReservation(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    ticket = models.ForeignKey(AvailableTicket, on_delete=models.CASCADE)
    amount_of_tickets = models.IntegerField()
    amount_to_pay = models.DecimalField(max_digits=8, decimal_places=2)
    expiration_datetime = models.DateTimeField()


class PurchasedTicket(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    ticket = models.ForeignKey(AvailableTicket, on_delete=models.CASCADE)
    amount_of_tickets = models.IntegerField()
