from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import F

from .models import Event, AvailableTicket, TicketReservation
from .serializers import (
    EventSerializer,
    AvailableTicketSerializer,
    TicketReservationSerializer,
)


@api_view(['GET'])
def event_detail_view(request, event_id):
    ev = Event.objects.filter(id=event_id)
    if not ev.exists():
        return Response({}, status=404)
    obj = ev.first()
    serializer = EventSerializer(obj)
    return Response(serializer.data)


@api_view(['GET'])
def event_list_view(request):
    events = Event.objects.all()
    serializer = EventSerializer(events, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ticket_reservations_view(request):
    trs = TicketReservation.objects.filter(owner=request.user)
    if not trs.exists():
        return Response({}, status=404)
    serializer = TicketReservationSerializer(trs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def event_available_tickets_view(request, event_id):
    tickets = AvailableTicket.objects.filter(event=event_id)
    if not tickets.exists():
        return Response({}, status=404)
    serializer = AvailableTicketSerializer(tickets, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reserve_ticket_view(request, event_id):
    reservation = TicketReservationSerializer(data=request.data)
    if reservation.is_valid(raise_exception=True):
        t = AvailableTicket.objects.get(pk=reservation.validated_data['ticket'].id)
        if t.amount_of_tickets >= reservation.validated_data['amount_of_tickets']:
            t.amount_of_tickets = F('amount_of_tickets') - reservation.validated_data['amount_of_tickets']
            t.save()
            reservation.save(owner=request.user)
            return Response(reservation.data, status=201)
        else:
            return Response({'message': "Insufficient number of tickets available."}, status=400)
    return Response({}, status=400)
