from django.conf.urls import url

from speaker.views import (
    CreateSpeakerView, UserSpeakerPortraitUploadView, UserSpeakerProfileView,
    UserSpeakerPortraitDeleteView, PublishedSpeakerDetailView,
    PublishedSpeakerListView)

urlpatterns = [
    url(r'speaker/register/$',
        CreateSpeakerView.as_view(), name='create_speaker'),
    url(r'speaker/profile/$',
        UserSpeakerProfileView.as_view(), name='user_speaker_profile'),
    url(r'speaker/upload_portrait/$', UserSpeakerPortraitUploadView.as_view(),
        name='upload_user_speaker_portrait'),
    url(r'speaker/delete_portrait/$', UserSpeakerPortraitDeleteView.as_view(),
        name='delete_user_speaker_portrait'),
    url(r'(?P<event>[^/]+)/speaker/(?P<slug>[^/]+)/$',
        PublishedSpeakerDetailView.as_view(),
        name='public_speaker_profile'),
    url(r'(?P<event>[^/]+)/speaker/$',
        PublishedSpeakerListView.as_view(),
        name='public_speaker_list'),
]
