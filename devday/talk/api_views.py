from rest_framework import serializers, viewsets
from rest_framework.relations import StringRelatedField
from talk.models import Talk


class SessionSerializer(serializers.ModelSerializer):
    event = StringRelatedField()
    published_speaker = StringRelatedField()

    class Meta:
        model = Talk
        fields = ["url", "title", "abstract", "published_speakers", "event"]


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Talk.objects.filter(published_speakers__isnull=False)
    serializer_class = SessionSerializer
