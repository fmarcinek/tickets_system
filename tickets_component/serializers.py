from rest_framework import serializers

from .models import Event, AvailableTicket


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'name', 'datetime']


class AvailableTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableTicket
        fields = ['id', 'event_id', 'type', 'amount_of_tickets', 'price']
