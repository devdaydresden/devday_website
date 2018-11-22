from mock import Mock, patch
from bs4 import BeautifulSoup

from django.core import mail
from django.test import TestCase

from devday.utils.html_mail import create_html_mail


class CreateHtmlMailTests(TestCase):

    def find_attachment_by_content_id(self, msg, name):
        for a in msg.attachments:
            for (k, v) in a._headers:
                if k == 'Content-ID' and v == name:
                    return a
        return None

    @patch('devday.utils.html_mail.urlopen')
    def test_create_html_email(self, mock_urlopen):
        html = '''<html><body>
<p>First paragraph</p>
<p><img src='http://localhost/firstimage.jpg'></p>
<p>Third paragraph</p>
<p><img src='http://localhost/secondimage.jpg'></p>
<p>Final paragraph</p>
</body></html>
'''
        mini_jpeg = (
            b'\xff\xd8\xff\xdb\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02'
            b'\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04\x04\x04\x08\x06\x06\x05'
            b'\x06\t\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e'
            b'\x0b\t\t\r\x11\r\x0e\x0f\x10\x10\x11\x10\n\x0c\x12\x13'
            b'\x12\x10\x13\x0f\x10\x10\x10\xff\xc9\x00\x0b\x08\x00\x01\x00\x01'
            b'\x01\x01\x11\x00\xff\xcc\x00\x06\x00\x10\x10\x05\xff\xda\x00\x08'
            b'\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9')
        mock_httpresponse = Mock()
        mock_httpresponse.getheader = Mock()
        mock_httpresponse.read = Mock()
        mock_httpresponse.getheader.side_effect = ['image/jpeg', 'image/jpeg']
        mock_httpresponse.read.side_effect = [mini_jpeg, mini_jpeg]
        mock_urlopen.return_value.__enter__.return_value = mock_httpresponse
        msg = create_html_mail('A test mail', html)
        msg.recipientlist = ('foo@example.com',)
        msg.send()
        self.assertEquals(len(mail.outbox), 1, 'should have one message')
        msg = mail.outbox[0]
        self.assertEquals(msg.alternatives[0][1], 'text/html')
        self.assertEquals(len(msg.attachments), 2, 'has two attachments')
        soup = BeautifulSoup(msg.alternatives[0][0], 'lxml')
        for img in soup.findAll('img'):
            cid = img['src'].split(':')[1]
            att = self.find_attachment_by_content_id(msg, cid)
            self.assertIsNotNone(att, 'image tag has a matching attachment')
