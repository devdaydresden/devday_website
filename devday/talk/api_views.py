from rest_framework import serializers, viewsets
from rest_framework.relations import StringRelatedField

from speaker.models import Speaker
from talk.models import Talk


class NestedSpeakersSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source="thumbnail")

    class Meta:
        model = Speaker
        fields = ["url", "name", "image"]
        lookup_field = "slug"
        extra_kwargs = {
            "url": {'lookup_field': 'slug'}
        }

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # TODO Jens: This probably can be solved more elegantly with a mixin.
        if not representation["image"]:
            representation["image"] = ""

        return representation


class SessionSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.CharField(source="slug")
    description = serializers.CharField(source="abstract")

    # TODO Jens: Replace 'event' and 'speakers' with proper nested relationships once their endpoints are done.
    event = StringRelatedField()
    speakers = NestedSpeakersSerializer(source="published_speakers", many=True, read_only=True)

    class Meta:
        model = Talk
        fields = ["id", "url", "title", "description", "speakers", "event"]
        lookup_field = "slug"
        extra_kwargs = {
            "url": {'lookup_field': 'slug'}
        }


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Talk.objects.filter(published_speakers__isnull=False)
    serializer_class = SessionSerializer
    lookup_field = 'slug'
