from functools import partial

from django.urls import path

from .views import (
    event_detail_view,
    event_list_view,
    user_reservations_view,
    event_available_tickets_view,
    reserve_ticket_view,
    payment_view,
    tickets_statistics_view,
)
from .models import PurchasedTicket, AvailableTicket

urlpatterns = [
    path('event/<int:event_id>/', event_detail_view),
    path('events/', event_list_view),
    path('event/<int:event_id>/available_tickets', event_available_tickets_view),
    path('event/<int:event_id>/reserve_ticket', reserve_ticket_view),
    path('reservations/', user_reservations_view),
    path('reservations/payment', payment_view),
    path('statistics/reserved_tickets/', partial(tickets_statistics_view, cls=AvailableTicket)),
    path('statistics/reserved_tickets/<str:type_>/', partial(tickets_statistics_view, cls=AvailableTicket)),
    path('statistics/purchased_tickets/', partial(tickets_statistics_view, cls=PurchasedTicket)),
    path('statistics/purchased_tickets/<str:type_>/', partial(tickets_statistics_view, cls=PurchasedTicket)),
]

