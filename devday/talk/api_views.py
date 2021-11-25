from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.relations import StringRelatedField
from rest_framework.response import Response

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

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        ret["actions"] = {
            "favourite": ret["url"] + "favourite",
            "unfavourite": ret["url"] + "unfavourite"
        }

        return ret


class SessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Talk.objects.filter(published_speakers__isnull=False)
    serializer_class = SessionSerializer
    lookup_field = 'slug'

    @action(detail=True, methods=['post'])
    def favourite(self, request, slug):
        session = self.get_object()
        user = request.user
        user.favourite_talks.add(session)
        user.save()

        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def unfavourite(self, request, slug):
        session = self.get_object()
        user = request.user
        user.favourite_talks.remove(session)
        user.save()

        return Response()
