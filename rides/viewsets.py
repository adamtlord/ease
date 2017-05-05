from rest_framework import viewsets
from rides.models import Ride, Destination
from rides.serializers import RideSerializer, DestinationSerializer


class RideViewSet(viewsets.ModelViewSet):
    queryset = Ride.objects.all()
    serializer_class = RideSerializer


class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
