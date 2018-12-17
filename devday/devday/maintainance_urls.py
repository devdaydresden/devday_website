# -*- coding: utf-8 -*-
from django.conf.urls import url

from devday.views import StaticPlaceholderView

urlpatterns = [
    url(r'$', StaticPlaceholderView.as_view(),
        name='edit_static_placeholders'),
]
