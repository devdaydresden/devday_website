from rest_framework import serializers, viewsets

from speaker.models import Speaker


class SpeakerSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.CharField(source="slug")
    image = serializers.ImageField(source="public_image", use_url=True, allow_null=False, allow_empty_file=False)

    class Meta:
        model = Speaker
        fields = ["id", "url", "name", "short_biography", "position", "image"]
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


class SpeakerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Speaker.objects.all()
    serializer_class = SpeakerSerializer
    lookup_field = "slug"
