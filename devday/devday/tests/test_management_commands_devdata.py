import mock

from unittest import TestCase

from django.contrib.auth import get_user_model
from django.core.management import call_command


User = get_user_model()


class CommandTest(TestCase):

    @mock.patch('devday.utils.devdata.DevData', autospec=True)
    def test_devdata(self, DevDayMock):
        m = mock.Mock()
        DevDayMock.side_effect = [m]
        call_command('devdata')
        DevDayMock.assert_called_once_with(stdout=mock.ANY, style=mock.ANY)
        m.create_devdata.assert_called_once_with()
