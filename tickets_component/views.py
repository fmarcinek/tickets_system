import datetime

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import F, Sum, Count

from .models import (
    Event,
    AvailableTicket,
    TicketReservation,
    TICKET_TYPES,
)
from .serializers import (
    EventSerializer,
    AvailableTicketSerializer,
    TicketReservationSerializer,
    PaymentSerializer,
    PurchasedTicketSerializer,
)
from .payments_adapter import payments as payments_adapter


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
def user_reservations_view(request):
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payment_view(request):
    payment = PaymentSerializer(data=request.data)
    if payment.is_valid(raise_exception=True):
        reservations_indicies = payment.validated_data['reservations']
        amount_to_pay = payment.validated_data['amount']
        currency = payment.validated_data['currency']

        reservations = TicketReservation.objects.filter(
            pk__in=reservations_indicies).filter(
            expiration_datetime__gte=datetime.datetime.now()
        )

        if set(reservations_indicies) != {r.id for r in reservations}:
            return Response({'message': 'Reservation does not exist or expired.'}, status=400)
        if amount_to_pay != reservations.aggregate(Sum('amount_to_pay'))['amount_to_pay__sum']:
            return Response({'message': 'Wrong amount of money for this payment request.'}, status=400)

        payment_gateway = payments_adapter.PaymentGateway()
        try:
            payment_result = payment_gateway.charge(amount_to_pay, currency)
        except (payments_adapter.CardError, payments_adapter.CurrencyError, payments_adapter.PaymentError) as ex:
            return Response({'message': ex}, status=400)
        else:
            if payment_result.amount == amount_to_pay and payment_result.currency == currency:
                reservation_dicts = TicketReservationSerializer(reservations, many=True).data
                for dct in reservation_dicts:
                    dct.update({'owner': request.user.id})
                purchased_tickets = PurchasedTicketSerializer(data=reservation_dicts, many=True)
                if purchased_tickets.is_valid(raise_exception=True):
                    purchased_tickets.save()
                    reservations.delete()
                    return Response({'message': 'Payment succeeded.'}, status=200)
    return Response({}, status=400)


@api_view(['GET'])
def reserved_tickets_statistics_view(request, type_=None):
    ticket_types_dict = dict(TICKET_TYPES)
    if type_ in ticket_types_dict.keys():
        tickets = AvailableTicket.objects.filter(type=type_)
    elif type_ in ticket_types_dict.values():
        type_ = {v: k for k, v in ticket_types_dict.items()}[type_]
        tickets = AvailableTicket.objects.filter(type=type_)
    else:
        tickets = AvailableTicket.objects.all()
    tickets_data = tickets.values('event_id', 'type').annotate(quantity=Sum('amount_of_tickets'))
    for dct in tickets_data:
        dct['type'] = ticket_types_dict[dct['type']]
    return Response(tickets_data)
