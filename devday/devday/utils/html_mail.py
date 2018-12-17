"""Create a HTML email message from HTML

In addition to creating a text-only version and using multipart/alternative,
find img tags and convert the URL src to an embedded base64 representation of
the image.
"""

from email.mime.image import MIMEImage
from urllib.request import urlopen

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.translation import ugettext_lazy as _
from html2text import HTML2Text


class DevDayEmailMessage(EmailMultiAlternatives):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.recipientlist = []

    def recipients(self):
        return self.recipientlist

    def attach_html(self, html):
        soup = BeautifulSoup(html, 'lxml')
        i = 0
        for tag in soup.findAll('img'):
            url = tag['src']
            with urlopen(url) as response:
                subtype = response.getheader('Content-type').split('/')[1]
                img = MIMEImage(response.read(), subtype)
                img.add_header('Content-ID', f'image-{i}')
                self.attach(img)
                tag['src'] = f'cid:image-{i}'
                i += 1
        self.attach_alternative(str(soup), 'text/html')


def create_html_mail(subject, html):
    conv = HTML2Text()
    conv.ignore_images = True
    conv.inline_links = False
    conv.use_automatic_links = True
    message = conv.handle(html)
    msg = DevDayEmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_EMAIL_SENDER,
        to=(_('Dev Day Attendees {}').format('<undisclosed-recipients:;>'),
            ),
    )
    msg.extra_headers['From'] = _(
        'Dev Day <{}>').format(settings.DEFAULT_FROM_EMAIL)
    msg.attach_html(html)
    return msg
