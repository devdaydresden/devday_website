from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from devday.utils.devdata import DevData


User = get_user_model()


class CommandTest(TestCase):

    def test_useremails(self):
        '''
        Create user_count users and test that useremails returns that many
        entries, plus two newlines.
        '''
        user_count = 20

        count_before = User.objects.count()
        dd = DevData()
        dd.create_attendees(user_count)

        self.assertEquals(User.objects.count()-count_before, user_count,
                          'created usercount test users')

        user = User.objects.all().first()
        user.contact_permission_date = None
        user.save()

        out = StringIO()
        args = []
        opts = {'stdout': out}
        call_command('useremails', *args, **opts)
        entries = len(out.getvalue().strip().split('\n'))
        self.assertEquals(entries, user_count-1,
                          'all users except one have given permission')
