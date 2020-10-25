from django.urls import path

from .views import (
    event_detail_view,
    event_list_view,
)

urlpatterns = [
    path('event/<int:event_id>/', event_detail_view),
    path('events/', event_list_view),
]
