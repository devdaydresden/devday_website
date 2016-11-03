from django.views.generic import TemplateView


class ImprintView(TemplateView):
    template_name = "imprint.html"