from django.urls import path
from .views import SoftwareListCreateView, SoftwareRetrieveUpdateDestroyView

urlpatterns = [
    path('software', SoftwareListCreateView.as_view(), name='software-list-create'),
    path('software/<int:pk>', SoftwareRetrieveUpdateDestroyView.as_view(), name='software-detail'),
]