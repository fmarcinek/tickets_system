from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Event, AvailableTicket
from .serializers import (
    EventSerializer,
    AvailableTicketSerializer,
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
def event_available_tickets_view(request, event_id):
    tickets = AvailableTicket.objects.filter(event=event_id)
    if not tickets.exists():
        return Response({}, status=404)
    serializer = AvailableTicketSerializer(tickets, many=True)
    return Response(serializer.data)
