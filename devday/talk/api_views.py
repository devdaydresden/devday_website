from rest_framework import serializers, viewsets
from rest_framework.relations import StringRelatedField
from talk.models import Talk


class SessionSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.CharField(source="slug")
    description = serializers.CharField(source="abstract")

    # TODO Jens: Replace 'event' and 'speakers' with proper nested relationships once their endpoints are done.
    event = StringRelatedField()
    published_speakers = StringRelatedField(many=True)

    class Meta:
        model = Talk
        fields = ["id", "url", "title", "description", "published_speakers", "event"]
        lookup_field = "slug"
        extra_kwargs = {
            "url": {'lookup_field': 'slug'}
        }


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Talk.objects.filter(published_speakers__isnull=False)
    serializer_class = SessionSerializer
    lookup_field = 'slug'
