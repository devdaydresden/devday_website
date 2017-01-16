from django.views.generic import TemplateView


class ImprintView(TemplateView):
    template_name = "imprint.html"


def exception_test_view(request):
    raise Exception("Synthetic server error")
