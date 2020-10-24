from .models import TicketReservation, AvailableTicket
from django.db.models import F

import datetime


def remove_obsolete_reservations():
    now = datetime.datetime.now()
    obsolete_reservations = TicketReservation.objects.filter(expiration_datetime__gt=now)
    for obs_res in obsolete_reservations:
        ticket = AvailableTicket.objects.get(pk=obs_res.ticket)
        ticket.amount_of_tickets = F('amount_of_tickets') + obs_res.amount_of_tickets
        ticket.save()

    obsolete_reservations.delete()
