from django.db import models
from django.utils.translation import ugettext_lazy as _

from event.models import Event
from ordered_model.models import OrderedModel

PACKAGE_NAMES = ((1, _("Platinum")), (2, _("Gold")), (3, _("Silver")))

PACKAGE_NAME_CSS_CLASS_MAP = {1: "platinum", 2: "gold", 3: "silver"}


class SponsoringPackage(models.Model):
    event = models.ForeignKey(Event, verbose_name=_("Event"), on_delete=models.CASCADE)
    package_type = models.PositiveSmallIntegerField(
        verbose_name=_("Package"), choices=PACKAGE_NAMES
    )
    pricing = models.CharField(verbose_name=_("Price"), max_length=10)

    class Meta:
        verbose_name = _("Sponsoring Package")
        verbose_name_plural = _("Sponsoring Packages")
        unique_together = (("event", "package_type"),)
        ordering = ("-event", "-package_type")

    @property
    def css_class(self):
        return PACKAGE_NAME_CSS_CLASS_MAP[self.package_type]

    def get_type_label(self):
        return dict(PACKAGE_NAMES)[self.package_type]


class SponsoringPackageItem(OrderedModel):
    package = models.ForeignKey(
        SponsoringPackage, verbose_name=_("Package"), on_delete=models.CASCADE
    )
    name = models.CharField(verbose_name=_("Name"), max_length=128)
    description = models.TextField(verbose_name=_("Description"), blank=True)
    is_header = models.BooleanField(verbose_name=_("Header"), default=False)

    order_with_respect_to = "package__package_type"

    class Meta(OrderedModel.Meta):
        verbose_name = _("Sponsoring Package Item")
        verbose_name_plural = _("Sponsoring Package Items")
