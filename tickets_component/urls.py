from django.urls import path

from .views import (
    event_detail_view,
    event_list_view,
    user_reservations_view,
    event_available_tickets_view,
    reserve_ticket_view,
    payment_view,
    reserved_tickets_statistics_view,
)

urlpatterns = [
    path('event/<int:event_id>/', event_detail_view),
    path('events/', event_list_view),
    path('event/<int:event_id>/available_tickets', event_available_tickets_view),
    path('event/<int:event_id>/reserve_ticket', reserve_ticket_view),
    path('reservations/', user_reservations_view),
    path('reservations/payment', payment_view),
    path('statistics/reserved_tickets/', reserved_tickets_statistics_view),
    path('statistics/reserved_tickets/<str:type_>/', reserved_tickets_statistics_view),
]
