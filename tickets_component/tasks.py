import datetime

from django.db.models import F

from .models import TicketReservation, AvailableTicket


def remove_obsolete_reservations():
    print(f'run task: {remove_obsolete_reservations.__name__}, datetime: {datetime.datetime.now()}')
    now = datetime.datetime.now()
    obsolete_reservations = TicketReservation.objects.filter(expiration_datetime__lt=now)
    for obs_res in obsolete_reservations:
        ticket = AvailableTicket.objects.get(pk=obs_res.ticket.id)
        print(obs_res, ticket)
        ticket.amount_of_tickets = F('amount_of_tickets') + obs_res.amount_of_tickets
        ticket.save()

    obsolete_reservations.delete()
