import django_filters as df
from .models import Event, EarlyPass

class EventFilter(df.FilterSet):
    q = df.CharFilter(method="search", label="Search")
    class Meta:
        model = Event
        fields = ["category","date"]
    def search(self, qs, name, value):
        return qs.filter(title__icontains=value) if value else qs

class PassFilter(df.FilterSet):
    class Meta:
        model = EarlyPass
        fields = ["status","event"]
