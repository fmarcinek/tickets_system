from rest_framework import serializers
import datetime

from .models import Event, AvailableTicket, TicketReservation


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'name', 'datetime']


class AvailableTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableTicket
        fields = ['id', 'event_id', 'type', 'amount_of_tickets', 'price']


class TicketReservationSerializer(serializers.ModelSerializer):
    amount_to_pay = serializers.DecimalField(max_digits=8, decimal_places=2, default=None)
    expiration_datetime = serializers.DateTimeField(default=None)
    event = serializers.SerializerMethodField(read_only=True, default=0)

    class Meta:
        model = TicketReservation
        fields = ['id', 'ticket', 'event', 'amount_of_tickets', 'amount_to_pay', 'expiration_datetime']

    def get_event(self, obj):
        return AvailableTicket.objects.get(pk=obj.ticket.id).event_id

    def validate_amount_of_tickets(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError('Not allowed amount of tickets in reservation.')
        return value

    def validate(self, data):
        t = AvailableTicket.objects.get(pk=data['ticket'].id)

        if data['amount_to_pay'] is None:
            data['amount_to_pay'] = t.price * data['amount_of_tickets']

        if data['expiration_datetime'] is None:
            data['expiration_datetime'] = datetime.datetime.now() + datetime.timedelta(minutes=15)

        if t.price * data['amount_of_tickets'] != data['amount_to_pay']:
            raise serializers.ValidationError(
                'Amount of tickets and amount to pay do not comply with the price of the ticket.'
            )
        return data
