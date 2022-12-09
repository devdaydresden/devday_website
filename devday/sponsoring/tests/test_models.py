from django.test import TestCase

from sponsoring.models import SponsoringPackage


class SponsoringPackageTest(TestCase):
    def test_css_class(self):
        package = SponsoringPackage(package_type=1)
        self.assertEqual(package.css_class, 'platinum')
        package = SponsoringPackage(package_type=2)
        self.assertEqual(package.css_class, 'gold')
        package = SponsoringPackage(package_type=3)
        self.assertEqual(package.css_class, 'silver')
