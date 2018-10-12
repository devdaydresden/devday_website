from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.test import TestCase

from devday.extras import ValidatedImageField

small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)


class ValidatedImageFieldTest(TestCase):
    '''
    Explicitly test the custom clean() call in our ImageField.  Although the
    code should be exercised during Form tests, having an explicit test here
    should make finding problems easier.
    '''

    @staticmethod
    def get_uploaded_file(data):
        return InMemoryUploadedFile(
            BytesIO(data),
            field_name='image',
            name='an_image.png',
            content_type='image/png',
            size=len(data),
            charset='utf-8',
        )

    def test_valid(self):
        name = ValidatedImageField.name_image_by_contents(
            self.get_uploaded_file(small_gif))
        self.assertEquals(
            name,
            'c7fbc3e8d889e42601d1dfa019f4678d67e2383a97a1940761d105ee.gif')

    def test_invalid(self):
        with self.assertRaises(ValidationError):
            n = ValidatedImageField.name_image_by_contents(
                self.get_uploaded_file(b'not an image'))
            print('#### {} ####'.format(n))
