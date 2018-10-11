from django.conf.urls import url

from speaker.views import (
    CreateSpeakerView, UserSpeakerPortraitUploadView, UserSpeakerProfileView)

urlpatterns = [
    url(r'speaker/register/$',
        CreateSpeakerView.as_view(), name='create_speaker'),
    url(r'speaker/profile/$',
        UserSpeakerProfileView.as_view(), name='user_speaker_profile'),
    url(r'speaker/upload_portrait/$',
        UserSpeakerPortraitUploadView.as_view(),
        name='upload_user_speaker_portrait')
]
