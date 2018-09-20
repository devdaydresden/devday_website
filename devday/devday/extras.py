import hashlib
import magic

from django.db.models import ImageField
from django.conf import settings
from django.core.exceptions import ValidationError


class ValidatedImageField(ImageField):
    """
    Extends Djangos ImageField by validating the uploaded file, setting the
    filename based on a hash of the file, and setting the extension based on
    the image type.
    """

    extensions = {
        'image/gif': '.gif',
        'image/jpeg': '.jpg',
        'image/png': '.png',
    }

    def __init__(self, *args, **kwargs):
        super(ValidatedImageField, self).__init__(*args, **kwargs)
        if 'extensions' in kwargs:
            self.extensions = kwargs.get('extensions')

    def clean(self, *args, **kwargs):
        data = super(ValidatedImageField, self).clean(*args, **kwargs)
        m = magic.from_buffer(args[0]._file.read(1024), mime=True)
        if m in self.extensions:
            ext = self.extensions[m]
        else:
            raise ValidationError('Unsupported image file format {}'
                                  .format(m))
        h = hashlib.sha224()
        h.update(data._file.read())
        data.name = u'{}{}'.format(h.hexdigest(), ext)
        return data


def show_toolbar_callback(request):
    """
    Custom callback to always show the debug toolbar when the DEBUG setting
    is True. See https://django-debug-toolbar.readthedocs.io/en/1.0/configuration.html#debug-toolbar-config
    """
    return settings.DEBUG
