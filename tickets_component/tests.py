import datetime

from rest_framework.test import APIClient
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model

from .models import (
    AvailableTicket,
    Event,
)

User = get_user_model()


class TicketsComponentTestCase(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create_user(username='abc', password='some_password')
        self.user_2 = User.objects.create_user(username='bcd', password='some_password')
        self.event_1 = Event.objects.create(name='festival', datetime=datetime.datetime.now())
        self.event_2 = Event.objects.create(name='festival 2', datetime=datetime.datetime.now())
        self.ticket_1 = AvailableTicket.objects.create(
            event=self.event_1, amount_of_tickets=3, price=5.0, type='regular'
        )
        self.ticket_2 = AvailableTicket.objects.create(
            event=self.event_2, amount_of_tickets=3, price=10.0, type='VIP'
        )
        self.ticket_3 = AvailableTicket.objects.create(
            event=self.event_2, amount_of_tickets=1, price=6.0, type='premium'
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
