from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Event
from .serializers import (
    EventSerializer,
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
