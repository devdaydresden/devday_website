from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, TemplateView, RedirectView

from event.models import Event
from sponsoring.forms import SponsoringContactForm
from sponsoring.models import SponsoringPackage


class SponsoringView(FormView):
    template_name = 'sponsoring/sponsoring.html'
    form_class = SponsoringContactForm
    success_url = reverse_lazy('sponsoring_thanks')
    email_subject_template = 'sponsoring/sponsoring_request_mail_subject.txt'
    email_body_template = 'sponsoring/sponsoring_request_mail_body.txt'
    event = None

    def dispatch(self, request, *args, **kwargs):
        self.event = get_object_or_404(Event, slug=self.kwargs['event'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.send_email(form)
        return super().form_valid(form)

    def get_form_kwargs(self):
        initial = super().get_form_kwargs()
        initial['event'] = self.event
        return initial

    def get_email_context(self, form):
        return {
            'event': self.event,
            'organization': form.cleaned_data['organization'],
            'contact_email': form.cleaned_data['email'],
            'body_text': form.cleaned_data['body'],
            'site': Site.objects.get_current(self.request),
            'request': self.request,
        }

    def send_email(self, form):
        context = self.get_email_context(form)
        email = EmailMessage(
            subject=render_to_string(
                self.email_subject_template, context, self.request),
            body=render_to_string(
                self.email_body_template, context, self.request),
            from_email=settings.DEFAULT_EMAIL_SENDER,
            to=settings.SPONSORING_RECIPIENTS,
            reply_to=[context['contact_email']],
            headers={'From': settings.SPONSORING_FROM_EMAIL},
        )
        email.send(fail_silently=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        packages = []
        for package in SponsoringPackage.objects.filter(event=self.event):
            packages.append({
                'name': package.get_package_type_display(),
                'css_class': package.css_class,
                'pricing': package.pricing,
                'package_items': []
            })
            for item in package.sponsoringpackageitem_set.all():
                if item.is_header:
                    packages[-1]['package_items'].append({
                        'name': item.name,
                        'description': item.description,
                        'package_items': [],
                    })
                else:
                    packages[-1]['package_items'][-1]['package_items'].append({
                        'name': item.name,
                        'description': item.description,
                    })
        context['packages'] = packages
        return context


class SponsoringThanksView(TemplateView):
    template_name = 'sponsoring/sponsoring_thanks.html'


class RedirectToCurrentEventView(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        return reverse(
            'sponsoring_view',
            kwargs={'event': Event.objects.current_event().slug})
