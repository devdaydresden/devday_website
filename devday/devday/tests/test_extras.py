from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Model
from django.test import TestCase, override_settings
from django.utils.translation import ugettext as _

from devday.extras import ValidatedImageField

small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)


def get_in_memory_gif_file(data):
    return InMemoryUploadedFile(
        BytesIO(data),
        field_name='image',
        name='an_image.png',
        content_type='image/png',
        size=len(data),
        charset='utf-8',
    )


@override_settings(DEFAULT_FILE_STORAGE='inmemorystorage.InMemoryStorage')
class ValidatedImageFieldTest(TestCase):
    """
    Explicitly test the custom clean() call in our ImageField.  Although the
    code should be exercised during Form tests, having an explicit test here
    should make finding problems easier.
    """
    def setUp(self):
        self.gif_file = get_in_memory_gif_file(small_gif)

    def test_valid(self):
        class MockModelWithImageValid(Model):
            image = ValidatedImageField()
        instance = MockModelWithImageValid()
        instance.image.save(self.gif_file.name, self.gif_file, save=False)
        instance.full_clean()
        self.assertEquals(
            instance.image.name,
            'c7fbc3e8d889e42601d1dfa019f4678d67e2383a97a1940761d105ee.gif')

    def test_invalid(self):
        class MockModelWithImageInvalid(Model):
            image = ValidatedImageField()
        instance = MockModelWithImageInvalid()
        instance.image.save(
            'invalid_image.jpg', BytesIO(b'not an image'), save=False)
        with self.assertRaises(ValidationError):
            instance.full_clean()

    def test_custom_extensions_value(self):
        class MockModelWithImageCustomExtensions(Model):
            image = ValidatedImageField(extensions={'image/jpeg': '.jpg'})
        instance = MockModelWithImageCustomExtensions()
        instance.image.save(self.gif_file.name, self.gif_file, save=False)
        with self.assertRaisesMessage(
                ValidationError,
                _('Unsupported image file format {}').format('image/gif')):
            instance.full_clean()
