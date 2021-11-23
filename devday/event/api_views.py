from rest_framework import serializers, viewsets

from event.models import Event


class EventSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="slug")
    full_day_event = serializers.BooleanField(source='full_day')

    class Meta:
        model = Event
        fields = ["id", "url", "location", "title", "description", "full_day_event", "start_time", "end_time"]
        lookup_field = "slug"
        extra_kwargs = {
            "url": {'lookup_field': 'slug'}
        }


class EventDetailViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.filter(published=True)
    serializer_class = EventSerializer
    lookup_field = 'slug'
