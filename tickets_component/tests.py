import datetime

from rest_framework.test import APIClient
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model

from .models import (
    AvailableTicket,
    Event,
    TicketReservation,
    PurchasedTicket
)
from .tasks import remove_obsolete_reservations

User = get_user_model()


class TicketsComponentTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create_user(username='abc', password='some_password')
        self.user_2 = User.objects.create_user(username='bcd', password='some_password')
        self.event_1 = Event.objects.create(name='festival', datetime=datetime.datetime.now())
        self.event_2 = Event.objects.create(name='festival 2', datetime=datetime.datetime.now())
        self.ticket_1 = AvailableTicket.objects.create(
            event=self.event_1, amount_of_tickets=3, price=5.0, type='r'
        )
        self.ticket_2 = AvailableTicket.objects.create(
            event=self.event_2, amount_of_tickets=3, price=10.0, type='V'
        )
        self.ticket_3 = AvailableTicket.objects.create(
            event=self.event_2, amount_of_tickets=1, price=6.0, type='p'
        )

    def get_client(self):
        client = APIClient()
        client.login(username=self.user, password='some_password')
        return client

    def read_datetime_from_json(self, json):
        return datetime.datetime.strptime(json.get('datetime'), '%Y-%m-%dT%H:%M:%S.%f')

    def test_get_all_events(self):
        client = self.get_client()
        response = client.get('/api/events/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_event_detail_view(self):
        client = self.get_client()
        response = client.get('/api/event/1/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('name'), self.event_1.name)
        self.assertEqual(
            self.read_datetime_from_json(response.json()),
            self.event_1.datetime
        )

    def test_fail_no_event(self):
        client = self.get_client()
        response = client.get('/api/event/3/')
        self.assertEqual(response.status_code, 404)

    def test_get_available_tickets_for_the_event(self):
        client = self.get_client()
        response = client.get('/api/event/2/available_tickets')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual({el.get('id') for el in response.json()}, {self.ticket_2.id, self.ticket_3.id})

    def test_create_reservation(self):
        now_before_creating = datetime.datetime.now()
        initial_amount_of_available_tickets = self.ticket_1.amount_of_tickets
        amount_of_tickets_to_buy = 2

        client = self.get_client()
        response = client.post('/api/event/1/reserve_ticket', {
            'ticket': self.ticket_1.id,
            'amount_of_tickets': amount_of_tickets_to_buy
        })
        # it's important to refresh updated object!
        self.ticket_1.refresh_from_db()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(TicketReservation.objects.all()), 1)
        reservation = TicketReservation.objects.all().first()
        self.assertEqual(reservation.owner, self.user)
        self.assertEqual(reservation.ticket, self.ticket_1)
        self.assertEqual(initial_amount_of_available_tickets,
                         self.ticket_1.amount_of_tickets + amount_of_tickets_to_buy)
        self.assertGreater(reservation.expiration_datetime, now_before_creating + datetime.timedelta(minutes=15))
        self.assertLess(reservation.expiration_datetime, now_before_creating + datetime.timedelta(minutes=16))

    def test_get_user_reservations(self):
        client = self.get_client()
        r1 = TicketReservation.objects.create(owner=self.user, ticket=self.ticket_1, amount_of_tickets=1,
                                              amount_to_pay=5.0, expiration_datetime=datetime.datetime.now())
        r2 = TicketReservation.objects.create(owner=self.user, ticket=self.ticket_2, amount_of_tickets=1,
                                              amount_to_pay=10.0, expiration_datetime=datetime.datetime.now())
        r3 = TicketReservation.objects.create(owner=self.user_2, ticket=self.ticket_1, amount_of_tickets=1,
                                              amount_to_pay=5.0, expiration_datetime=datetime.datetime.now())
        response = client.get('/api/reservations/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual({el.get('id') for el in response.json()}, {r1.id, r2.id})

    def test_remove_obsolete_reservation(self):
        amount_of_tickets_to_reserve = 2
        r1 = TicketReservation.objects.create(owner=self.user, ticket=self.ticket_1,
                                              amount_of_tickets=amount_of_tickets_to_reserve,
                                              amount_to_pay=5.0, expiration_datetime=datetime.datetime.now())
        self.assertTrue(r1 in TicketReservation.objects.all())
        available_tickets_amount_before_deleting = self.ticket_1.amount_of_tickets
        remove_obsolete_reservations()
        self.assertTrue(r1 not in TicketReservation.objects.all())
        self.ticket_1.refresh_from_db()
        self.assertEqual(available_tickets_amount_before_deleting,
                         self.ticket_1.amount_of_tickets - amount_of_tickets_to_reserve)

    def test_payment_one_reservation(self):
        client = self.get_client()
        r1 = TicketReservation.objects.create(
            owner=self.user, ticket=self.ticket_1, amount_of_tickets=1, amount_to_pay=5.0,
            expiration_datetime=datetime.datetime.now() + datetime.timedelta(minutes=1)
        )
        response = client.post('/api/reservations/payment', {'reservations': [r1.id], 'currency': 'EUR', 'amount': 5.0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('message'), "Payment succeeded.")
        self.assertTrue(r1 not in TicketReservation.objects.all())
        self.assertEqual(len(PurchasedTicket.objects.all()), 1)
        purchased_ticket = PurchasedTicket.objects.all().first()
        self.assertEqual(purchased_ticket.owner, r1.owner)
        self.assertEqual(purchased_ticket.ticket, r1.ticket)
        self.assertEqual(purchased_ticket.amount_of_tickets, r1.amount_of_tickets)

    def test_payment_two_reservations(self):
        client = self.get_client()
        r1 = TicketReservation.objects.create(
            owner=self.user, ticket=self.ticket_1, amount_of_tickets=1, amount_to_pay=5.0,
            expiration_datetime=datetime.datetime.now() + datetime.timedelta(minutes=1)
        )
        r2 = TicketReservation.objects.create(
            owner=self.user, ticket=self.ticket_2, amount_of_tickets=2, amount_to_pay=20.0,
            expiration_datetime=datetime.datetime.now() + datetime.timedelta(minutes=1)
        )
        response = client.post('/api/reservations/payment',
                               {'reservations': [r1.id, r2.id], 'currency': 'EUR', 'amount': 25.0})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('message'), "Payment succeeded.")
        self.assertTrue(r1 not in TicketReservation.objects.all())
        self.assertTrue(r2 not in TicketReservation.objects.all())
        self.assertEqual(len(PurchasedTicket.objects.all()), 2)
        purchased_tickets = PurchasedTicket.objects.all()
        self.assertEqual({t.ticket.id for t in purchased_tickets}, {self.ticket_1.id, self.ticket_2.id})

    def test_fail_payment_wrong_amount_of_money(self):
        client = self.get_client()
        r1 = TicketReservation.objects.create(
            owner=self.user, ticket=self.ticket_1, amount_of_tickets=1, amount_to_pay=5.0,
            expiration_datetime=datetime.datetime.now() + datetime.timedelta(minutes=1)
        )
        response = client.post('/api/reservations/payment', {'reservations': [r1.id], 'currency': 'EUR', 'amount': 4.0})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get('message'), 'Wrong amount of money for this payment request.')

    def test_fail_payment_nonexistent_reservation(self):
        client = self.get_client()
        response = client.post('/api/reservations/payment', {'reservations': [1], 'currency': 'EUR', 'amount': 4.0})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json().get('message'), 'Reservation does not exist or expired.')

    def test_statistics_reserved_tickets_all_types(self):
        client = self.get_client()
        response = client.get('/api/statistics/reserved_tickets/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual({tuple((k, v) for k, v in r.items()) for r in response.json()}, {tuple(r) for r in [
            (('event_id', 1), ('type', 'regular'), ('quantity', 3)),
            (('event_id', 2), ('type', 'premium'), ('quantity', 1)),
            (('event_id', 2), ('type', 'VIP'), ('quantity', 3)),
        ]})

    def test_statistics_reserved_tickets_for_certain_type(self):
        client = self.get_client()
        response = client.get('/api/statistics/reserved_tickets/regular/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual({tuple((k, v) for k, v in r.items()) for r in response.json()}, {tuple(r) for r in [
            (('event_id', 1), ('type', 'regular'), ('quantity', 3)),
        ]})
